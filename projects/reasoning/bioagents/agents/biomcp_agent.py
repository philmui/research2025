"""
Biomedical MCP Agent

A high-level interface for interacting with biomedical research tools via the MCP protocol.
Provides a simple async chat interface while handling all the complexity of server management,
connection handling, and resource cleanup.

Features:
- Simple async chat interface via achat() method
- Automatic server lifecycle management with lazy initialization
- Per-operation connections for proper async resource management
- Robust error handling and diagnostics
- Environment-based configuration
- Context manager support for proper cleanup
- Auto-start capability for interactive environments

Example:
    # Simple usage (auto-starts server on first call)
    agent = BioMCPAgent()
    result = await agent.achat("Find articles about Alzheimer's disease")
    print(result)

    # Explicit lifecycle management (recommended for production)
    async with BioMCPAgent() as agent:
        result = await agent.achat("Get details for variant rs113488022")
        print(result)
"""

import asyncio
import os
import shutil
import subprocess
import requests
import atexit
import weakref
from typing import Any, Optional
from contextlib import asynccontextmanager

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStreamableHttp
from agents.model_settings import ModelSettings
from loguru import logger

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

from bioagents.agents.common import AgentResponse
from bioagents.agents.base_agent import ReasoningAgent
from bioagents.models.llms import LLM

class BioMCPAgentError(Exception):
    """Base exception for BioMCPAgent errors."""
    pass


class BioMCPServerError(BioMCPAgentError):
    """Raised when the MCP server fails to start or respond."""
    pass


class BioMCPConnectionError(BioMCPAgentError):
    """Raised when connection to the MCP server fails."""
    pass

BIOMCP_PORT = int(os.environ.get("BIOMCP_PORT", 8131))

class BioMCPAgent(ReasoningAgent):
    """
    High-level interface for biomedical MCP interactions.
    
    This class encapsulates all the complexity of managing a biomedical MCP server,
    providing a simple async chat interface for biomedical research queries.
    
    The agent handles:
    - Server lifecycle management (start/stop)
    - Connection establishment and monitoring
    - Agent configuration and setup
    - Resource cleanup and error recovery
    
    Usage as context manager (recommended):
        async with BioMCPAgent() as agent:
            result = await agent.achat("Find articles about cancer research")
            
    Manual usage:
        agent = BioMCPAgent()
        await agent.start()
        try:
            result = await agent.achat("Get variant details for rs123456")
        finally:
            await agent.stop()
    """
    
    def __init__(
        self,
        name: str = "Biomedical MCP Agent",
        model_name: str=LLM.GPT_4_1_MINI,
        instructions: str="You are a biomedical research assistant.",
        port: Optional[int] = BIOMCP_PORT,
        timeout: int = 60,  # Increased default timeout for biomedical queries
        server_startup_timeout: int = 60,
        debug: bool = False,
    ):
        """
        Initialize the BioMCPAgent.
        
        Args:
            port: Port for the MCP server (defaults to BIOMCP_PORT env var or 8131)
            timeout: Timeout for individual requests in seconds (increased for biomedical queries)
            server_startup_timeout: Timeout for server startup in seconds  
            debug: Enable debug logging
            
        Raises:
            BioMCPAgentError: If required dependencies are missing
        """
        super().__init__(name, model_name, instructions)
        
        self.port = port or BIOMCP_PORT
        self.timeout = timeout
        self.server_startup_timeout = server_startup_timeout
        self.debug = debug
        
        # Validate environment
        self._validate_environment()
        
        # Internal state - simplified for per-operation connections
        self._server_process: Optional[subprocess.Popen[Any]] = None
        self._server_url = f"http://localhost:{self.port}"
        self._mcp_endpoint = f"{self._server_url}/mcp/"
        self._server_started = False  # Track server process only
        self._start_lock = asyncio.Lock()  # Prevent race conditions during auto-start
        self._auto_started = False  # Track if we auto-started (for cleanup)
        
        # Agent instance for reuse across operations
        self._agent: Optional[Agent] = None
        
        # Configure logging
        if debug:
            logger.enable("biomcp_agent")
        else:
            logger.disable("biomcp_agent")
    
    def _validate_environment(self) -> None:
        """Validate required dependencies and environment variables."""
        # Check uv
        if not shutil.which("uv"):
            raise BioMCPAgentError(
                "uv package manager is required. Install from: "
                "https://docs.astral.sh/uv/getting-started/installation/"
            )
        
        # Check OpenAI API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise BioMCPAgentError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass openai_api_key parameter."
            )
    
    def _check_port_available(self) -> bool:
        """Check if the configured port is available."""
        import socket
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.port))
            return result != 0
    
    def _test_http_endpoint(self, url: str, timeout: int = 5) -> tuple[bool, str]:
        """Test if an HTTP endpoint is responding."""
        try:
            response = requests.get(url, timeout=timeout)
            return True, f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except Exception as e:
            return False, f"Error: {e}"
    
    async def _start_server(self) -> subprocess.Popen[Any]:
        """Start the biomedical MCP server process."""
        if not self._check_port_available():
            raise BioMCPServerError(
                f"Port {self.port} is already in use. Please stop other servers or use a different port."
            )
        
        # Locate server file - try multiple possible locations
        this_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try different possible locations for the server file
        possible_locations = [
            # First try the same directory (for backward compatibility)
            os.path.join(this_dir, "biomcp_server.py"),
            # Then try the mcp directory (correct location)
            os.path.join(os.path.dirname(this_dir), "mcp", "biomcp_server.py"),
            # Also try relative to the bioagents directory
            os.path.join(os.path.dirname(this_dir), "biomcp_server.py"),
        ]
        
        server_file = None
        for location in possible_locations:
            if os.path.exists(location):
                server_file = location
                logger.debug(f"Found server file at: {server_file}")
                break
        
        if not server_file:
            locations_tried = '\n  '.join(possible_locations)
            raise BioMCPServerError(
                f"Server file not found in any of the expected locations:\n  {locations_tried}\n"
                f"Please ensure biomcp_server.py is available in one of these paths."
            )
        
        logger.info(f"Starting biomedical MCP server on {self._server_url}")
        
        # Set environment variables for server
        env = os.environ.copy()
        env["BIOMCP_PORT"] = str(self.port)
        
        # Start server process
        try:
            process = subprocess.Popen(
                ["uv", "run", server_file],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
        except Exception as e:
            raise BioMCPServerError(f"Failed to start server process: {e}")
        
        # Monitor startup
        logger.info("Waiting for server to start...")
        for i in range(self.server_startup_timeout):
            await asyncio.sleep(1)
            
            # Check if process crashed
            if process.poll() is not None:
                stdout, _ = process.communicate()
                raise BioMCPServerError(
                    f"Server process terminated unexpectedly after {i+1} seconds.\n"
                    f"Output:\n{stdout}"
                )
            
            # Test HTTP connectivity after initial startup time
            if i >= 3:
                success, message = self._test_http_endpoint(self._server_url)
                logger.debug(f"Connection test {i-2}: {message}")
                
                if success:
                    # Test MCP endpoint specifically  
                    mcp_success, mcp_message = self._test_http_endpoint(self._mcp_endpoint)
                    logger.debug(f"MCP endpoint test: {mcp_message}")
                    
                    if mcp_success or "404" in mcp_message:
                        logger.info("Server is responding to HTTP requests!")
                        return process
        
        # Timeout reached
        process.terminate()
        stdout, _ = process.communicate()
        raise BioMCPServerError(
            f"Server failed to respond after {self.server_startup_timeout} seconds.\n"
            f"Server output:\n{stdout}"
        )
    
    async def _create_connection(self) -> MCPServerStreamableHttp:
        """Establish connection to the MCP server."""
        try:
            from datetime import timedelta
            
            server = MCPServerStreamableHttp(
                name="Biomedical MCP Server",
                params={
                    "url": self._mcp_endpoint,
                    "timeout": timedelta(seconds=self.timeout),  # HTTP request timeout
                    "sse_read_timeout": timedelta(seconds=self.timeout),  # SSE read timeout
                },
                client_session_timeout_seconds=self.timeout,  # MCP session timeout
            )
            await server.__aenter__()
            return server
        except Exception as e:
            raise BioMCPConnectionError(f"Failed to connect to MCP server: {e}")
    
    def _create_agent(self, mcp_server: MCPServer) -> Agent:
        """Create and configure the biomedical agent."""
        return Agent(
            name="BiomedicalAssistant",
            instructions=(
                "You are a biomedical research assistant. Use the available biomedical tools "
                "to answer questions about genetic variants, research articles, and biomedical data. "
                "Be helpful, accurate, and informative in your responses. When using tools, "
                "provide clear explanations of the results and their significance. "
                "If a biomedical query takes time, be patient as external databases may be slow."
            ),
            mcp_servers=[mcp_server],
            model_settings=ModelSettings(tool_choice="auto"),
        )
    
    async def start(self) -> None:
        """
        Start the biomedical MCP server process only.
        
        This method only starts the server process. Connections are created
        per-operation to ensure proper async resource management.
        
        Raises:
            BioMCPServerError: If server startup fails
        """
        if self._server_started:
            logger.warning("Server is already started")
            return
        
        try:
            # Start server process only
            self._server_process = await self._start_server()
            self._server_started = True
            logger.info("BioMCP server started successfully")
            
        except Exception as e:
            # Clean up on failure
            await self._cleanup()
            raise
    
    async def stop(self) -> None:
        """
        Stop the server process and clean up resources.
        
        This method only handles server process cleanup since connections
        are managed per-operation.
        """
        await self._cleanup()
        logger.info("BioMCP server stopped")
    
    async def _cleanup(self) -> None:
        """Internal cleanup method - only handles server process."""
        # Terminate server process
        if self._server_process:
            try:
                self._server_process.terminate()
                try:
                    self._server_process.wait(timeout=5)
                    logger.debug("Server stopped gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("Force-stopping server...")
                    self._server_process.kill()
                    self._server_process.wait()
                    logger.debug("Server force-stopped")
            except Exception as e:
                logger.warning(f"Error stopping server: {e}")
            self._server_process = None
        
        # Reset state
        self._server_started = False
        self._agent = None  # Reset agent to force recreation with new server
    
    async def _ensure_server_started(self) -> None:
        """
        Ensure the server is started, auto-starting if necessary.
        
        This method handles lazy server initialization with proper concurrency control.
        """
        if self._server_started:
            return
            
        async with self._start_lock:
            # Double-check after acquiring lock
            if self._server_started:
                return
                
            try:
                logger.info("Auto-starting BioMCP server for first use...")
                await self.start()
                self._auto_started = True
                
                # Register cleanup for auto-started server
                self._register_cleanup()
                    
                logger.info("BioMCP server auto-started successfully")
                
            except Exception as e:
                logger.error(f"Failed to auto-start BioMCP server: {e}")
                raise BioMCPAgentError(
                    f"Failed to auto-start server: {e}. "
                    f"Try manually starting with 'async with BioMCPAgent()' or 'await agent.start()'"
                ) from e

    def _register_cleanup(self) -> None:
        """Register cleanup for auto-started server - simplified for server-only cleanup."""
        # Use weakref to avoid circular references
        weak_self = weakref.ref(self)
        
        def cleanup_server():
            agent = weak_self()
            if agent and agent._auto_started:
                try:
                    agent._synchronous_cleanup()
                except Exception as e:
                    # Suppress all cleanup errors - they're non-critical
                    logger.debug(f"Auto-cleanup completed: {e}")
        
        atexit.register(cleanup_server)

    def _synchronous_cleanup(self) -> None:
        """Synchronous cleanup for server process only."""
        try:
            # Terminate server process synchronously
            if self._server_process:
                try:
                    self._server_process.terminate()
                    try:
                        self._server_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self._server_process.kill()
                        self._server_process.wait()
                    logger.debug("Server process terminated synchronously")
                except Exception as e:
                    logger.debug(f"Server termination completed: {e}")
                self._server_process = None
            
            # Reset state
            self._server_started = False
            self._agent = None  # Reset agent to force recreation with new server
            
        except Exception as e:
            logger.debug(f"Synchronous cleanup completed: {e}")

    async def achat(self, query_str: str) -> AgentResponse:
        """
        Process a biomedical research query and return the response.
        
        This is the main interface method for interacting with biomedical tools.
        Uses per-operation connections for proper async resource management.
        
        **Auto-Start Behavior**: If the server is not started, it will automatically
        start the server process on the first call to achat(). Connections are created
        and destroyed within each operation for async safety.
        
        Args:
            query_str: Natural language query about biomedical research, variants, or articles
            
        Returns:
            An AgentResponse object containing the response from the biomedical agent with tool results and analysis
            
        Raises:
            BioMCPAgentError: If server startup fails or query processing fails
            
        Examples:
            # Simple usage (auto-starts server on first call)
            agent = BioMCPAgent()
            result = await agent.achat("Find recent articles about CRISPR gene editing")
            
            # Explicit lifecycle management (recommended for production)
            async with BioMCPAgent() as agent:
                result = await agent.achat("Get details for genetic variant rs113488022")
        """
        if not query_str.strip():
            raise BioMCPAgentError("Query string cannot be empty")
        
        # Ensure server is started (auto-start if needed)
        await self._ensure_server_started()
        
        # Execute the query with per-operation connection
        logger.info(f"Processing query: {query_str}")
        
        try:
            # Generate trace ID for tracking
            trace_id = gen_trace_id()
            
            with trace(workflow_name="Biomedical Query", trace_id=trace_id):
                async with await self._create_connection() as mcp_server:
                    if self._agent is None:
                        self._agent = self._create_agent(mcp_server)
                    else:
                        self._agent.mcp_servers = [mcp_server]
                    
                    result = await asyncio.wait_for(
                        Runner.run(
                            starting_agent=self._agent,
                            input=query_str,
                            max_turns=3,
                        ),
                        timeout=self.timeout
                    )
                    
                logger.info(f"Query completed successfully. Trace ID: {trace_id}")
                return self._construct_response(result, "", "biomcp")
                
        except asyncio.TimeoutError as e:
            error_msg = f"Query timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise BioMCPAgentError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Query failed: {str(e)}"
            logger.error(error_msg)
            raise BioMCPAgentError(error_msg) from e
    
    async def __aenter__(self) -> "BioMCPAgent":
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.stop()
    
    @property
    def is_started(self) -> bool:
        """Check if the server is started and ready."""
        return self._server_started
    
    @property
    def server_url(self) -> str:
        """Get the server URL."""
        return self._server_url
    
    def __repr__(self) -> str:
        status = "started" if self._server_started else "stopped"
        return f"BioMCPAgent(port={self.port}, server_status={status})"


#----------------------------------------------
# Example usage and testing functions
#----------------------------------------------

# Example usage and testing functions
async def example_usage():
    """Example demonstrating how to use BioMCPAgent with comprehensive biomedical examples."""
    print("🧬 BioMCPAgent - Comprehensive Biomedical Research Examples")
    print("=" * 80)
    
    try:
        # Demonstrate both usage patterns
        print("🧪 Testing explicit lifecycle management...")
        async with BioMCPAgent(
            debug=True, 
            timeout=90,  # 90 seconds for complex biomedical queries
        ) as agent:
            print(f"✅ Explicitly started {agent}")
            print(f"🔗 Server URL: {agent.server_url}")
            print(f"⚙️  Configured with {agent.timeout}s timeout")
            
            # Test one query with explicit management
            result = await agent.achat("What tools are available in the biomedical server?")
            print(f"✅ Explicit management response received")
        
        print("\n🚀 Testing auto-start capability...")
        # Test auto-start capability (new feature)
        auto_agent = BioMCPAgent(debug=True, timeout=90)
        print(f"📦 Created agent (not started yet): {auto_agent}")
        
        # This will auto-start the agent
        result = await auto_agent.achat("Get details for the genetic variant rs113488022.")
        print(f"✅ Auto-start response received!")
        print(f"🔄 Agent is now started: {auto_agent.is_started}")
        
        # Continue with remaining examples using the auto-started agent
        remaining_examples = [
            "Find recent research articles about Alzheimer's disease.",
            "Search for articles about CRISPR gene editing and cancer treatment.",
            "Get detailed information about PubMed article 37351900.",
        ]
        
        for i, query in enumerate(remaining_examples, 1):
            print(f"\n{'='*80}")
            print(f"🧪 Auto-agent example {i}/{len(remaining_examples)}: {query}")
            print(f"{'='*80}")
            
            try:
                result = await auto_agent.achat(query)
                print(f"✅ Response:\n{result}")
            except Exception as e:
                print(f"❌ Error in example {i}: {e}")
            
            # Add delay between examples
            if i < len(remaining_examples):
                print("\n⏳ Waiting before next example...")
                await asyncio.sleep(2)
        
        # Note: auto-started agent will be cleaned up automatically on exit
        
        print(f"\n🎉 All biomedical examples completed!")
                    
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        return False
    
    return True


if __name__ == "__main__":
    """Run comprehensive biomedical examples when script is executed directly."""
    print("🚀 Starting BioMCPAgent comprehensive testing...")
    print("📋 This will demonstrate all biomedical research capabilities")
    print("⏱️  Biomedical queries can take 30-90 seconds due to external database calls\n")
    
    try:
        success = asyncio.run(example_usage())
        
        if success:
            print("\n" + "=" * 80)
            print("🎉 BioMCPAgent comprehensive testing completed successfully!")
            print("✅ All biomedical research examples demonstrated the following capabilities:")
            print("   • Tool discovery and listing")
            print("   • Genetic variant analysis")
            print("   • Biomedical literature search")
            print("   • Article retrieval and analysis")
            print("   • Structured biomedical data processing")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("❌ BioMCPAgent testing failed")
            print("🔧 Please check the error messages above and ensure:")
            print("   • OpenAI API key is properly configured")
            print("   • biomcp-python dependencies are available")
            print("   • Network connectivity for PubMed access")
            print("   • Port availability (default: 8131)")
            print("=" * 80)
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        print("🛑 BioMCPAgent testing stopped")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        print("🔧 Please check your environment configuration")
        exit(1) 