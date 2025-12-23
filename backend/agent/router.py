"""
Agent router for handling chat requests using OpenAI Agents API.
"""
import sys
from pathlib import Path

# Add project root to path so imports work when run directly
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import os
import json
import re
import uuid
import argparse
from typing import Tuple, Optional, Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI
from backend.agent.db_queries import search_products_nl

# Load .env file from project root
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a shopping assistant for an online shoe store.

CRITICAL RULE: You MUST ALWAYS use the search_products_nl() tool when customers:
- Ask about products (e.g., "show me running shoes", "I want black sneakers")
- Request specific products (e.g., "I'd like to get the black canvas skate sneakers", "I want Nike shoes")
- Ask about product names, brands, or specific shoes
- Ask about price (e.g., "shoes under $100", "cheap shoes")
- Ask about rating (e.g., "highly rated", "best rated", "4+ stars")
- Ask about category (e.g., "running shoes", "casual", "athletic")
- Ask about any combination of the above

The database contains products with: id, name, description, price, rating (0-5), category, and image_path.

IMPORTANT: When customers mention ANY product, you MUST use the search_products_nl() tool FIRST. Do NOT respond without searching. Do NOT ask follow-up questions - use the tool immediately.

CRITICAL: After receiving product results from the tool:
1. Parse the product list from the tool response
2. If the customer asked for a specific product, show that product (or the closest match)
3. If the customer is browsing, select the top 4-5 products (prioritize by rating, then price if needed)
4. Present them in a neat, numbered list format showing: product name, price, rating, and a brief description
5. After showing the list, ALWAYS ask: "Which items would you like to add to your cart? Please let me know the product numbers or names."

IMPORTANT: When a customer explicitly says they want to ADD a product to cart (e.g., "I want to add X", "I'll take X", "add X to cart", "I'd like to get X"), you should:
1. Search for that specific product using the tool
2. Confirm which product you found
3. Use language like "I'll add [Product Name] to your cart" or "Adding [Product Name] to your cart"

Example format for browsing:
"Here are some great options I found:

1. [Product Name] - $[price] ⭐ [rating]/5
   [Brief description]

2. [Product Name] - $[price] ⭐ [rating]/5
   [Brief description]

[... continue for 4-5 products ...]

Which items would you like to add to your cart? Please let me know the product numbers or names."

Example format when customer wants to add to cart:
"Great choice! I'll add the **[Product Name]** to your cart. [Brief confirmation message]"

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


def _extract_products_from_result(result: str) -> List[Dict[str, Any]]:
    """Extract products list from search result string."""
    products = []
    if isinstance(result, str) and "Found" in result and "product(s):" in result:
        try:
            list_match = re.search(r'product\(s\):\s*(\[.*\])', result, re.DOTALL)
            if list_match:
                products_str = list_match.group(1)
                products = json.loads(products_str)
                if not isinstance(products, list):
                    products = []
        except (json.JSONDecodeError, AttributeError):
            pass
    return products


def run_tool(tool_name: str, arguments: dict) -> Tuple[str, List[Dict[str, Any]]]:
    """Execute a tool call and return the result string and products list."""
    if tool_name == "search_products_nl":
        query = arguments.get("query", "")
        result = search_products_nl(query)
        products = _extract_products_from_result(result)
        return result if isinstance(result, str) else str(result), products
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def _extract_output_text(response: Any) -> Optional[str]:
    """Extract text output from OpenAI response object."""
    if hasattr(response, 'output_text') and response.output_text:
        return response.output_text
    
    if hasattr(response, 'output') and response.output:
        for item in response.output:
            if isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    return item["text"]
            elif hasattr(item, 'type') and item.type == "text":
                if hasattr(item, 'text'):
                    return item.text
                elif hasattr(item, 'content'):
                    return item.content
    return None


def _extract_tool_calls(response: Any) -> List[Dict[str, Any]]:
    """Extract tool calls from OpenAI response object."""
    tool_calls = []
    if hasattr(response, 'output') and response.output:
        for item in response.output:
            if isinstance(item, dict):
                if item.get("type") in ["tool_call", "function_call"]:
                    tool_calls.append(item)
            elif hasattr(item, 'type') and item.type in ["tool_call", "function_call"]:
                tool_calls.append({
                    "call_id": getattr(item, 'call_id', None) or getattr(item, 'id', None),
                    "name": getattr(item, 'name', None),
                    "arguments": getattr(item, 'arguments', None)
                })
    return tool_calls


def _parse_tool_arguments(args: Any) -> Dict[str, Any]:
    """Parse tool call arguments (may be JSON string, dict, or None)."""
    if args is None:
        return {}
    elif isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return {}
    else:
        return args or {}


def _extract_tool_call_info(call: Any) -> Optional[Tuple[str, str, Dict[str, Any]]]:
    """Extract tool name, call_id, and arguments from a tool call object."""
    if isinstance(call, dict):
        tool_name = call.get("name")
        call_id = call.get("call_id") or call.get("id")
        args = call.get("arguments", {})
    else:
        tool_name = getattr(call, 'name', None)
        call_id = getattr(call, 'call_id', None) or getattr(call, 'id', None)
        args = getattr(call, 'arguments', None)
    
    if not tool_name or not call_id:
        return None
    
    tool_arguments = _parse_tool_arguments(args)
    return tool_name, call_id, tool_arguments


def chat_with_agent(user_message: str, session_id: str, previous_response_id: str = None) -> Tuple[str, str, list]:
    """
    Chat with OpenAI Agents API with tool execution loop.
    
    Args:
        user_message: The user's message
        session_id: Session/conversation ID (for tracking, not used in API)
        previous_response_id: ID of previous response for conversation continuity
        
    Returns:
        Tuple of (agent_reply_text, response_id, products) - products is a list of product dicts from tool calls
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
    if not previous_response_id:
        params["input"] = f"{SYSTEM_PROMPT}\n\nUser: {user_message}"
    
    # Create the initial response using OpenAI Agents API
    response = client.responses.create(**params)
    
    # Tool call execution loop
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    found_products = []  # Track products found during tool execution
    
    ERROR_MESSAGE = "I'm sorry, I encountered an issue processing your request."
    
    while iteration < max_iterations:
        iteration += 1
        
        output_text = _extract_output_text(response)
        if output_text:
            return output_text, response.id, found_products
        
        tool_calls = _extract_tool_calls(response)
        if not tool_calls:
            output_text = _extract_output_text(response)
            return output_text or ERROR_MESSAGE, response.id, found_products
        
        # Execute each tool call
        tool_outputs = []
        for call in tool_calls:
            call_info = _extract_tool_call_info(call)
            if not call_info:
                continue
            
            tool_name, call_id, tool_arguments = call_info
            
            try:
                result, products = run_tool(tool_name, tool_arguments)
                if products and isinstance(products, list):
                    found_products.extend(products)
                
                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": result,
                })
            except Exception as e:
                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": f"Error: {str(e)}",
                })
        
        # Send tool results back to the model
        try:
            response = client.responses.create(
                model="gpt-4o",
                previous_response_id=response.id,
                input=tool_outputs,
            )
        except Exception as e:
            if "No tool output found" in str(e) or "invalid_request_error" in str(e):
                return (
                    "I apologize, but I encountered an issue while processing your request. "
                    "Please try rephrasing your question or ask me again.",
                    response.id,
                    found_products
                )
            return ERROR_MESSAGE, response.id, found_products
    
    # Exhausted iterations or no valid response
    if iteration >= max_iterations:
        return f"{ERROR_MESSAGE} Please try again.", response.id, found_products
    
    output_text = _extract_output_text(response)
    return output_text or ERROR_MESSAGE, response.id, found_products


if __name__ == "__main__":
    import instrumentation
    instrumentation.setup_instrumentation()
    
    parser = argparse.ArgumentParser(description="Run the shopping assistant agent")
    parser.add_argument("message", type=str, help="Message to send to the agent")
    args = parser.parse_args()
    
    session_id = str(uuid.uuid4())
    
    reply, response_id, products = chat_with_agent(
        user_message=args.message,
        session_id=session_id
    )
    
