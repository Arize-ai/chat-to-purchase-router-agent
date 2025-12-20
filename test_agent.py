"""
Simple test script to test the Autogen agent.
Run this from the root directory: python test_agent.py
"""
import sys
from pathlib import Path

# Add root directory to path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Import instrumentation first
import instrumentation
instrumentation.setup_instrumentation()

# Import agent and dependencies
from backend.agent.router import assistant_agent, user_proxy

# Test the agent
user_proxy.initiate_chat(
    recipient=assistant_agent,
    message="Hello! Can you help me find running shoes?",
    max_turns=20,
)

