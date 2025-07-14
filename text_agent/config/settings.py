# Configuration settings for the security gate system

# Maximum number of human messages allowed before summarization
MAX_HUMAN_MESSAGES = 10

# Model configurations
DEFAULT_MODEL_MAIN = "gemma3n:e2b"
DEFAULT_MODEL_DECISION = "qwen3:4b"

# Temperature settings
TEMPERATURE_MAIN = 0
TEMPERATURE_VALIDATION = 0.1
TEMPERATURE_SESSION = 0.1
TEMPERATURE_SUMMARY = 0.1
TEMPERATURE_DECISION = 0

# Recursion limit for graph execution
DEFAULT_RECURSION_LIMIT = 100
