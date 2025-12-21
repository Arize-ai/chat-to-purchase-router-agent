"""
FastAPI server for the shopping assistant agent.
"""
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from typing import Optional, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import instrumentation
import uuid

# Setup instrumentation
instrumentation.setup_instrumentation()

from backend.agent.router import chat_with_agent

app = FastAPI()

# Store previous response IDs per session for conversation continuity
# Key: session_id, Value: previous_response_id
session_response_ids: Dict[str, str] = {}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response


class ChatRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    sessionId: str
    cartActions: Optional[list] = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests from the frontend.
    
    Simply takes the human message and passes it to chat_with_agent from router.py.
    """
    try:
        # Generate or use provided session ID
        session_id = request.sessionId or str(uuid.uuid4())
        
        print(f"Received message: '{request.message}' for session: {session_id}")
        
        # Get previous response ID for this session (if exists)
        previous_response_id = session_response_ids.get(session_id)
        
        # Call the agent with the user message
        reply, response_id = chat_with_agent(
            user_message=request.message,
            session_id=session_id,
            previous_response_id=previous_response_id
        )
        
        # Store the response ID for next call in this session
        session_response_ids[session_id] = response_id
        
        print(f"Agent reply: '{reply[:100]}...'")
        
        response = ChatResponse(
            message=reply,
            sessionId=session_id,
            cartActions=[]
        )
        return response
    except Exception as e:
        import traceback
        error_msg = f"Error in chat endpoint: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return ChatResponse(
            message=f"Server error: {str(e)}",
            sessionId=request.sessionId or "error",
            cartActions=[]
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
