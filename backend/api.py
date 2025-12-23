"""
FastAPI server for the shopping assistant agent.
"""
import sys
from pathlib import Path
import os
import json
from typing import Optional, Dict
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from opentelemetry.trace import Status, StatusCode
from openinference.instrumentation import using_session
import instrumentation

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.agent.router import chat_with_agent

env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

instrumentation.setup_instrumentation()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tracer = instrumentation.get_tracer(__name__)

app = FastAPI()
session_response_ids: Dict[str, str] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    sessionId: str
    cartActions: Optional[list] = None


def _call_llm(system_content: str, user_content: str, max_tokens: int = 200) -> Optional[str]:
    """Helper function to call OpenAI LLM."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def agent_references_products(agent_reply: str) -> bool:
    """
    Use LLM to determine if the agent's message references any products.
    This is used to determine what "Add to Cart" button to show the user.
    """
    prompt = f"""Analyze this agent message from a shopping conversation to determine if it references or mentions any specific products.

    Agent's message: "{agent_reply}"

    Determine if the agent is mentioning, describing, or referencing any specific products (shoes, sneakers, boots, etc.).

    Examples of YES (references products):
    - "Here are some great options: 1. Black Sneakers..."
    - "I found the Black Canvas Skate Sneakers"
    - "The Nike Running Shoes are available"
    - "I'll add the Black Leather Boots to your cart"
    - Any message that mentions specific product names
    
    Examples of NO (no product references):
    - "What are you looking for?"
    - "I can help you find products"
    - General greetings or questions

    Respond with ONLY "YES" or "NO" - nothing else."""

    with tracer.start_as_current_span("agent_references_products") as span:
        span.set_attribute("openinference.span.kind", "TOOL")
        span.set_attribute("input.value", agent_reply)
        try:
            result = _call_llm(
                system_content="You are a product reference analyzer. Respond with only YES or NO.",
                user_content=prompt,
                max_tokens=10
            )
            is_yes = result and result.upper() == "YES"
            span.set_attribute("output.value", str(is_yes))
            span.set_status(Status(StatusCode.OK))
            return is_yes
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return False


def extract_and_search_products(agent_reply: str, session_id: str, previous_response_id: Optional[str]) -> list:
    """
    Extract product names from agent message using LLM, then search for each product.
    Returns list of found product dicts (max 4).
    """
    prompt = f"""Extract product names from this agent message. Return ONLY a JSON array of product names mentioned, or an empty array if no products are mentioned.

    Agent's message: "{agent_reply}"

    Examples:
    - "Here are some options: 1. Black Sneakers - $50, 2. Red Boots - $80" -> ["Black Sneakers", "Red Boots"]
    - "I found the Black Canvas Skate Sneakers" -> ["Black Canvas Skate Sneakers"]
    - "The Nike Running Shoes are available" -> ["Nike Running Shoes"]
    - "How can I help you?" -> []

    Return ONLY a JSON array like: ["Product Name 1", "Product Name 2"] or []"""

    result = _call_llm(
        system_content="You are a product name extractor. Return only a JSON array of product names.",
        user_content=prompt,
        max_tokens=200
    )
    if not result:
        return []
    
    try:
        product_names = json.loads(result)
        if not isinstance(product_names, list):
            return []
    except json.JSONDecodeError:
        return []
    
    found_products = []
    for product_name in product_names[:4]:
        _, _, search_products = chat_with_agent(
            user_message=f"search for {product_name}",
            session_id=session_id,
            previous_response_id=previous_response_id
        )
        
        if not search_products:
            continue
        
        product_name_lower = product_name.lower()
        for product in search_products:
            if product_name_lower in product.get("name", "").lower():
                found_products.append(product)
                break
    
    return found_products


def create_cart_action(product: dict) -> dict:
    """Create a cart action dict from a product dict."""
    return {
        "type": "add",
        "product": {
            "id": product.get("id"),
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "price": float(product.get("price", 0)),
            "rating": float(product.get("rating", 0)),
            "category": product.get("category", ""),
            "image_path": product.get("image_path", "")
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok", "message": "API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests from the frontend."""
    session_id = request.sessionId or str(uuid.uuid4())
    
    with using_session(session_id=session_id):
        with tracer.start_as_current_span("chat_request") as parent_span:
            parent_span.set_attribute("openinference.span.kind", "CHAIN")
            parent_span.set_attribute("input.value", request.message)
            try:
                previous_response_id = session_response_ids.get(session_id)
                
                reply, response_id, products = chat_with_agent(
                    user_message=request.message,
                    session_id=session_id,
                    previous_response_id=previous_response_id
                )
                
                session_response_ids[session_id] = response_id
                agent_mentions_products = agent_references_products(reply)
                
                products_to_show = products
                if agent_mentions_products and not products:
                    products_to_show = extract_and_search_products(reply, session_id, previous_response_id)
                
                cart_actions = []
                if agent_mentions_products and products_to_show:
                    for product in products_to_show[:4]: 
                        if isinstance(product, dict) and 'id' in product:
                            cart_actions.append(create_cart_action(product))
                
                parent_span.set_attribute("output.value", reply)
                parent_span.set_status(Status(StatusCode.OK))
                return ChatResponse(
                    message=reply,
                    sessionId=session_id,
                    cartActions=cart_actions
                )
            except Exception as e:
                parent_span.set_status(Status(StatusCode.ERROR, str(e)))
                return ChatResponse(
                    message="I'm sorry, I encountered an error. Please try again.",
                    sessionId=session_id
                )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)