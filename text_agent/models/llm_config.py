import os
from langchain_ollama import ChatOllama
from src.tools.communication import tools
from config.settings import (
    DEFAULT_MODEL_FAST,
    DEFAULT_MODEL_SMART,
    DEFAULT_MODEL_VISION,
    TEMPERATURE_MAIN,
    TEMPERATURE_VALIDATION,
    TEMPERATURE_SESSION,
    TEMPERATURE_SUMMARY,
    TEMPERATURE_DECISION,
)

# Get Ollama host from environment variable (set by docker-compose)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.0.86:11434")


# Initialize all LLMs with containerized Ollama host
llm_summary = ChatOllama(
    model=DEFAULT_MODEL_FAST, temperature=TEMPERATURE_SUMMARY, base_url=OLLAMA_HOST
)
llm_email = ChatOllama(
    model=DEFAULT_MODEL_SMART, temperature=TEMPERATURE_DECISION, base_url=OLLAMA_HOST
).bind_tools(tools)

# JSON-enabled LLMs for structured output
llm_profiler_json = ChatOllama(
    model=DEFAULT_MODEL_SMART,
    temperature=TEMPERATURE_MAIN,
    format="json",
    base_url=OLLAMA_HOST,
)
llm_validation_json = ChatOllama(
    model=DEFAULT_MODEL_FAST,
    temperature=TEMPERATURE_VALIDATION,
    format="json",
    base_url=OLLAMA_HOST,
)
llm_session_json = ChatOllama(
    model=DEFAULT_MODEL_SMART,
    temperature=TEMPERATURE_SESSION,
    format="json",
    base_url=OLLAMA_HOST,
)
llm_decision_json = ChatOllama(
    model=DEFAULT_MODEL_SMART,
    temperature=TEMPERATURE_DECISION,
    format="json",
    base_url=OLLAMA_HOST,
)

# Vision-enabled LLM initialization
llm_vision_json = ChatOllama(
    model=DEFAULT_MODEL_VISION,
    temperature=TEMPERATURE_MAIN,
    format="json",
    base_url=OLLAMA_HOST,
)
