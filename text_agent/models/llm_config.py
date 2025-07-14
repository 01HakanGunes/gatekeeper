from langchain_ollama import ChatOllama
from src.tools.communication import tools
from config.settings import (
    DEFAULT_MODEL_MAIN,
    DEFAULT_MODEL_DECISION,
    TEMPERATURE_MAIN,
    TEMPERATURE_VALIDATION,
    TEMPERATURE_SESSION,
    TEMPERATURE_SUMMARY,
    TEMPERATURE_DECISION,
)


# Initialize all LLMs
llm_main = ChatOllama(
    model=DEFAULT_MODEL_MAIN, temperature=TEMPERATURE_MAIN
)  # Main LLM for core operations
llm_validation = ChatOllama(
    model=DEFAULT_MODEL_MAIN, temperature=TEMPERATURE_VALIDATION
)
llm_session = ChatOllama(model=DEFAULT_MODEL_MAIN, temperature=TEMPERATURE_SESSION)
llm_summary = ChatOllama(model=DEFAULT_MODEL_MAIN, temperature=TEMPERATURE_SUMMARY)
llm_decision = ChatOllama(
    model=DEFAULT_MODEL_DECISION, temperature=TEMPERATURE_DECISION
)
llm_email = ChatOllama(
    model=DEFAULT_MODEL_DECISION, temperature=TEMPERATURE_DECISION
).bind_tools(tools)
