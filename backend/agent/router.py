"""
Agent router for handling chat requests using OpenAI Agents API.
"""
import sys
from pathlib import Path

# Add project root to path so imports work when run directly
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import os
import argparse
from typing import Tuple
from dotenv import load_dotenv
from openai import OpenAI
from backend.agent.db_queries import search_products_nl

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# Define tool schema for search_products_nl
SEARCH_PRODUCTS_TOOL = {
    "type": "function",
    "name": "search_products_nl",
    "description": (
        "Search for products using natural language query. "
        "Use when customers ask about products by name, price, rating, "
        "category, or combinations. Examples: 'running shoes under $100', "
        "'highly rated casual shoes', 'Nike products', 'cheapest running shoes'. "
        "Returns a list of products with id, name, description, price, rating, category, and image_path."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Natural language product search query "
                    "(e.g., 'running shoes under $100', 'highly rated casual shoes')"
                )
            }
        },
        "required": ["query"]
    }
}


def chat_with_agent(user_message: str, session_id: str, previous_response_id: str = None) -> Tuple[str, str]:
    """
    Chat with OpenAI Agents API.
    
    Args:
        user_message: The user's message
        session_id: Session/conversation ID (for tracking, not used in API)
        previous_response_id: ID of previous response for conversation continuity
        
    Returns:
        Tuple of (agent_reply_text, response_id) - response_id should be stored for next call
    """
    # Build the request parameters
    params = {
        "model": "gpt-4o",
        "input": user_message,
        "tools": [SEARCH_PRODUCTS_TOOL],
    }
    
    # Add previous_response_id if provided (for conversation continuity)
    if previous_response_id:
        params["previous_response_id"] = previous_response_id
    
    # For the first message, prepend system prompt to input
    # (OpenAI Agents API may not support separate system_instruction parameter)
    if not previous_response_id:
        params["input"] = f"{SYSTEM_PROMPT}\n\nUser: {user_message}"
    
    # Create the response using OpenAI Agents API
    response = client.responses.create(**params)
    
    # Return both the output text and the response ID for next call
    return response.output_text, response.id


if __name__ == "__main__":
    import instrumentation
    instrumentation.setup_instrumentation()
    
    parser = argparse.ArgumentParser(description="Run the shopping assistant agent")
    parser.add_argument("message", type=str, help="Message to send to the agent")
    args = parser.parse_args()
    
    # Generate a session ID for this conversation
    import uuid
    session_id = str(uuid.uuid4())
    
    reply, response_id = chat_with_agent(
        user_message=args.message,
        session_id=session_id
    )
    
    print(f"Agent reply: {reply}")
    print(f"Response ID: {response_id} (use this as previous_response_id for next message)")
