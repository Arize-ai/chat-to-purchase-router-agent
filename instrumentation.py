"""
Arize AI instrumentation setup.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from arize.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

# Load .env file from project root
root_dir = Path(__file__).parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)
_instrumented = False

def setup_instrumentation():
    global _instrumented
    
    if _instrumented:
        return
    
    arize_space_id = os.getenv("ARIZE_SPACE_ID")
    arize_api_key = os.getenv("ARIZE_API_KEY")
    
    if not arize_space_id or not arize_api_key:
        print("Warning: ARIZE_SPACE_ID and ARIZE_API_KEY not set. Skipping Arize AI instrumentation.")
        _instrumented = True
        return
    
    register(
        space_id=arize_space_id,
        api_key=arize_api_key,
        project_name="chat2purchase",
    )
    
    OpenAIInstrumentor().instrument()
    
    _instrumented = True
    print("Arize AI instrumentation initialized!")


if __name__ == "__main__":
    setup_instrumentation()
