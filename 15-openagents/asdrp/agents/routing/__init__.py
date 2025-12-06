"""
Routing Agents Package

Contains orchestration agents that route queries to specialized agents.

Key exports:
- SmartRouter: Main router class
- create_smart_router: Factory function for easy router creation
"""

from .smart_router import SmartRouter, create_smart_router

__all__ = [
    "SmartRouter",
    "create_smart_router",
]
