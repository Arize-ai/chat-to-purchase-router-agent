"""
Agent router for handling chat requests.
"""
import asyncio
import os
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

After getting results from the tool, describe the products to the customer. When they want to add items to their cart, identify the specific product and prepare to add it.

Be friendly, concise, and helpful."""

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
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
)

register_function(
    search_products_nl,
    caller=assistant_agent,
    executor=user_proxy,
    description="Search for products using natural language query. Use when customers ask about products by name, price, rating, category, or combinations. Examples: 'running shoes under $100', 'highly rated casual shoes', 'Nike products', 'cheapest running shoes'. Returns a list of products with id, name, description, price, rating, category, and image_path."
)
