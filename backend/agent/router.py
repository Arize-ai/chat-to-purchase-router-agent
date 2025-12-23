"""
Agent router for handling chat requests using OpenAI Responses API.
"""
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent

import os
import json
import re
from typing import Tuple, Optional, Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI
from opentelemetry.trace import Status, StatusCode
from openinference.instrumentation import using_session, using_prompt_template
from backend.agent.db_queries import search_products_nl
import instrumentation

env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tracer = instrumentation.get_tracer(__name__)

SYSTEM_PROMPT = """You are a shopping assistant for an online shoe store.

CRITICAL: You MUST ALWAYS use the search_products_nl() tool when customers ask about products, prices, ratings, categories, brands, or any combination. Use the tool immediately - do NOT ask follow-up questions first.

The database contains products with: id, name, description, price, rating (0-5), category, and image_path.

After receiving product results:
- If customer asked for a specific product, show that product (or closest match)
- If browsing, show top 4-5 products (prioritize by rating, then price)
- Present in a numbered list: product name, price, rating, and brief description
- Always end with: "Which items would you like to add to your cart? Please let me know the product numbers or names."

When customer wants to add a product to cart (e.g., "I want to add X", "I'll take X", "add X to cart"):
1. Search for that product using the tool
2. Confirm and say: "I'll add [Product Name] to your cart"

Example browsing format:
"Here are some great options I found:

1. [Product Name] - $[price] ⭐ [rating]/5
   [Brief description]

2. [Product Name] - $[price] ⭐ [rating]/5
   [Brief description]

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
    with tracer.start_as_current_span(f"tool.{tool_name}") as span:
        span.set_attribute("openinference.span.kind", "TOOL")
        span.set_attribute("input.value", json.dumps(arguments))
        try:
            if tool_name == "search_products_nl":
                query = arguments.get("query", "")
                result = search_products_nl(query)
                products = _extract_products_from_result(result)
                output = result if isinstance(result, str) else str(result)
                span.set_attribute("output.value", output)
                span.set_status(Status(StatusCode.OK))
                return output, products
            else:
                error_msg = f"Unknown tool: {tool_name}"
                span.set_status(Status(StatusCode.ERROR, error_msg))
                raise ValueError(error_msg)
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


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
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return {}
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
    Returns:
        Tuple of (agent_reply_text, response_id, products) - products is a list of product dicts from tool calls
    """
    with using_session(session_id=session_id):
        with tracer.start_as_current_span("chat_with_agent") as span:
            span.set_attribute("openinference.span.kind", "CHAIN")
            span.set_attribute("input.value", user_message)
            try:
                input_text = f"{SYSTEM_PROMPT}\n\nUser: {user_message}" if not previous_response_id else user_message
                params = {
                    "model": "gpt-4o",
                    "input": input_text,
                    "tools": [SEARCH_PRODUCTS_TOOL],
                }
                if previous_response_id:
                    params["previous_response_id"] = previous_response_id
                
                with using_prompt_template(
                    template="{system_prompt}\n\nUser: {user_message}",
                    variables={"system_prompt": SYSTEM_PROMPT, "user_message": user_message} if not previous_response_id else {},
                    version="v1.0",
                ):
                    response = client.responses.create(**params)
        
                max_iterations = 10
                iteration = 0
                found_products = []
                ERROR_MESSAGE = "I'm sorry, I encountered an issue processing your request."
                
                while iteration < max_iterations:
                    iteration += 1
                    
                    output_text = _extract_output_text(response)
                    if output_text:
                        span.set_attribute("output.value", output_text)
                        span.set_status(Status(StatusCode.OK))
                        return output_text, response.id, found_products
                    
                    tool_calls = _extract_tool_calls(response)
                    if not tool_calls:
                        result = output_text or ERROR_MESSAGE
                        span.set_attribute("output.value", result)
                        span.set_status(Status(StatusCode.OK))
                        return result, response.id, found_products
                    
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
                    
                    try:
                        response = client.responses.create(
                            model="gpt-4o",
                            previous_response_id=response.id,
                            input=tool_outputs,
                        )
                    except Exception as e:
                        if "No tool output found" in str(e) or "invalid_request_error" in str(e):
                            error_msg = "I apologize, but I encountered an issue while processing your request. Please try rephrasing your question."
                        else:
                            error_msg = ERROR_MESSAGE
                        span.set_attribute("output.value", error_msg)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        return error_msg, response.id, found_products
                
                result = _extract_output_text(response) or f"{ERROR_MESSAGE} Please try again."
                span.set_attribute("output.value", result)
                span.set_status(Status(StatusCode.ERROR if iteration >= max_iterations else StatusCode.OK))
                return result, response.id, found_products
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise