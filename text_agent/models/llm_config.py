from langchain_ollama import ChatOllama
from src.tools.communication import tools
from config.settings import (
    DEFAULT_MODEL_MAIN,
    DEFAULT_MODEL_THINKING,
    TEMPERATURE_MAIN,
    TEMPERATURE_VALIDATION,
    TEMPERATURE_SESSION,
    TEMPERATURE_SUMMARY,
    TEMPERATURE_DECISION,
)


# Initialize all LLMs
llm_summary = ChatOllama(model=DEFAULT_MODEL_MAIN, temperature=TEMPERATURE_SUMMARY)
llm_email = ChatOllama(
    model=DEFAULT_MODEL_THINKING, temperature=TEMPERATURE_DECISION
).bind_tools(tools)

# JSON-enabled LLMs for structured output
llm_profiler_json = ChatOllama(
    model=DEFAULT_MODEL_THINKING, temperature=TEMPERATURE_MAIN, format="json"
)
llm_validation_json = ChatOllama(
    model=DEFAULT_MODEL_MAIN, temperature=TEMPERATURE_VALIDATION, format="json"
)
llm_session_json = ChatOllama(
    model=DEFAULT_MODEL_THINKING, temperature=TEMPERATURE_SESSION, format="json"
)
llm_decision_json = ChatOllama(
    model=DEFAULT_MODEL_THINKING, temperature=TEMPERATURE_DECISION, format="json"
)
