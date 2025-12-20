"""
Arize AI instrumentation setup.
"""
import os
from dotenv import load_dotenv
from arize.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.instrumentation.autogen import AutogenInstrumentor

load_dotenv()
_instrumented = False

def setup_instrumentation():
    global _instrumented
    
    if _instrumented:
        return
    
    arize_space_id = os.getenv("ARIZE_SPACE_ID")
    arize_api_key = os.getenv("ARIZE_API_KEY")
    
    if not arize_space_id or not arize_api_key:
        raise ValueError(
            "ARIZE_SPACE_ID and ARIZE_API_KEY must be set in environment variables"
        )
    
    register(
        space_id=arize_space_id,
        api_key=arize_api_key,
        project_name="chat2purchase",
    )
    
    OpenAIInstrumentor().instrument()
    AutogenInstrumentor().instrument()
    
    _instrumented = True
    print("Arize AI instrumentation initialized!")


if __name__ == "__main__":
    setup_instrumentation()
