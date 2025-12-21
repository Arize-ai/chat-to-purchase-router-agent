"""
Agent router for handling chat requests.
"""
import sys
from pathlib import Path

# Add project root to path so imports work when run directly
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import os
import argparse
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, register_function
import openai
import autogen
from backend.agent.db_queries import search_products_nl

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

llm_config = {
    "model": "gpt-5",  
    "api_key": os.getenv("OPENAI_API_KEY"),
}

SYSTEM_PROMPT = """You are a shopping assistant for an online shoe store.

Use the tool search_products_nl() when customers ask about:
- Product names, brands, or specific shoes
- Price (e.g., "shoes under $100", "cheap shoes")
- Rating (e.g., "highly rated", "best rated", "4+ stars")
- Category (e.g., "running shoes", "casual", "athletic")
- Any combination of the above (e.g., "cheapest running shoes", "highly rated Nike products")

The database contains products with: id, name, description, price, rating (0-5), category, and image_path.
IMPORTANT: When customers ask about products, you MUST use the search_products_nl() tool. Do NOT ask follow-up questions - use the tool immediately.

CRITICAL: After receiving product results from the tool:
1. Parse the product list from the tool response
2. Select the top 4-7 products (prioritize by rating, then price if needed)
3. Present them in a neat, numbered list format showing: product name, price, rating, and a brief description
4. After showing the list, ALWAYS ask: "Which items would you like to add to your cart? Please let me know the product numbers or names."

Example format:
"Here are some great options I found:

1. [Product Name] - $[price] ⭐ [rating]/5
   [Brief description]

2. [Product Name] - $[price] ⭐ [rating]/5
   [Brief description]

[... continue for 4-7 products ...]

Which items would you like to add to your cart? Please let me know the product numbers or names."

Be friendly, concise, and helpful."""

def create_agent_pair(message: str = None, max_turns: int = 20):
    """
    Create a pair of assistant and user proxy agents.
    If a message is provided, automatically initiates the chat.
    

    """
    assistant_agent = AssistantAgent(
        name="shopping_assistant",
        llm_config=llm_config,
        system_message=SYSTEM_PROMPT,
        max_consecutive_auto_reply=3,
        function_map={
            "search_products_nl": search_products_nl
        }
    )
    
    user_proxy = UserProxyAgent(
        name="user",
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=10,
    )
    
    register_function(
        search_products_nl,
        caller=assistant_agent,
        executor=user_proxy,
        description="Search for products using natural language query. Use when customers ask about products by name, price, rating, category, or combinations. Examples: 'running shoes under $100', 'highly rated casual shoes', 'Nike products', 'cheapest running shoes'. Returns a list of products with id, name, description, price, rating, category, and image_path."
    )
    
    if message:
        user_proxy.initiate_chat(
            recipient=assistant_agent,
            message=message,
            max_turns=max_turns,
        )
    
    return assistant_agent, user_proxy

assistant_agent, user_proxy = create_agent_pair()


if __name__ == "__main__":
    import instrumentation
    instrumentation.setup_instrumentation()
    
    parser = argparse.ArgumentParser(description="Run the shopping assistant agent")
    parser.add_argument("message", type=str, help="Message to send to the agent")
    args = parser.parse_args()
    
    create_agent_pair(message=args.message)
