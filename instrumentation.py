"""
Arize AX instrumentation setup.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from arize.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

root_dir = Path(__file__).parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

_instrumented = False
_tracer_provider = None

def setup_instrumentation():
    global _instrumented, _tracer_provider
    
    if _instrumented:
        return _tracer_provider
    
    arize_space_id = os.getenv("ARIZE_SPACE_ID")
    arize_api_key = os.getenv("ARIZE_API_KEY")
    
    if not arize_space_id or not arize_api_key:
        print("Warning: ARIZE_SPACE_ID and ARIZE_API_KEY not set. Skipping Arize AI instrumentation.")
        _instrumented = True
        return None
    
    _tracer_provider = register(space_id=arize_space_id, api_key=arize_api_key, project_name="chat2purchase")
    
    OpenAIInstrumentor().instrument()
    
    _instrumented = True
    print("Arize AI instrumentation initialized!")
    return _tracer_provider


def get_tracer(name: str = "chat2purchase"):
    if _tracer_provider is None:
        setup_instrumentation()
    
    if _tracer_provider is None:
        return None
    
    return _tracer_provider.get_tracer(name)


if __name__ == "__main__":
    setup_instrumentation()
