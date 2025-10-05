import re
import logging
from typing import List, Optional

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Configure logging for transparency
logging.basicConfig(
    filename='agent_actions.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AgentGuardrail:
    def __init__(self):
        # Define forbidden words for content filtering (example)
        self.forbidden_words = ['harm', 'violence', 'illegal', 'dangerous']
        # Define allowed actions (predefined action space)
        self.allowed_actions = ['send_message', 'fetch_data', 'schedule_event']
        # Initialize logger
        self.logger = logging.getLogger(__name__)

    def validate_input(self, user_input: str) -> bool:
        """
        Validate user input by checking for forbidden words.
        Returns True if input is safe, False otherwise.
        """
        input_lower = user_input.lower()
        for word in self.forbidden_words:
            if re.search(r'\b' + word + r'\b', input_lower):
                self.logger.warning(f"Input rejected: contains forbidden word '{word}'")
                return False
        self.logger.info("Input validated successfully")
        return True

    def restrict_action(self, action: str) -> bool:
        """
        Check if the requested action is within the allowed action space.
        Returns True if action is allowed, False otherwise.
        """
        if action in self.allowed_actions:
            self.logger.info(f"Action '{action}' is allowed")
            return True
        self.logger.warning(f"Action '{action}' is not in allowed action space")
        return False

    def execute_safe_action(self, user_input: str, action: str) -> str:
        """
        Process user input and execute action if it passes guardrails.
        Returns a response message.
        """
        # Step 1: Validate input
        if not self.validate_input(user_input):
            return "Error: Input contains inappropriate content."

        # Step 2: Restrict action
        if not self.restrict_action(action):
            return f"Error: Action '{action}' is not permitted."

        # Step 3: Simulate executing the action
        self.logger.info(f"Executing action '{action}' for input: {user_input}")
        return f"Success: Action '{action}' executed."

def main():
    # Initialize the guardrail system
    guardrail = AgentGuardrail()

    # Example test cases
    test_cases = [
        {"input": "Please send a message to the team", "action": "send_message"},
        {"input": "Schedule a meeting for tomorrow", "action": "schedule_event"},
        {"input": "Perform an illegal action", "action": "hack_system"},
        {"input": "Fetch some data", "action": "fetch_data"},
        {"input": "Cause harm to the system", "action": "send_message"},
    ]

    # Process each test case
    for case in test_cases:
        print(f"\nProcessing input: {case['input']}")
        print(f"Requested action: {case['action']}")
        result = guardrail.execute_safe_action(case['input'], case['action'])
        print(f"Result: {result}")
        
    user_input = input("\nEnter your request (or press Enter to exit): ")
    while user_input != "":
        result = guardrail.execute_safe_action(user_input, "send_message")
        print(f"Result: {result}")
        user_input = input("Enter your request (or press Enter to exit): ")

if __name__ == "__main__":
    main()