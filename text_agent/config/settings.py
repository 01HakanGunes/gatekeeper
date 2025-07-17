# Configuration settings for the security gate system

# Maximum number of human messages allowed before summarization
MAX_HUMAN_MESSAGES = 20

# Message history management settings
DEFAULT_HISTORY_MODE = "summarize"  # Options: "summarize" or "shorten"
SHORTEN_KEEP_MESSAGES = 5  # Number of recent messages to keep in shorten mode
CURRENT_HISTORY_MODE = (
    DEFAULT_HISTORY_MODE  # Will be set by main.py based on command-line args
)

# Model configurations
DEFAULT_MODEL_MAIN = "qwen3:0.6b"
DEFAULT_MODEL_THINKING = "qwen3:0.6b"

# Temperature settings
TEMPERATURE_MAIN = 0
TEMPERATURE_VALIDATION = 0.1
TEMPERATURE_SESSION = 0.1
TEMPERATURE_SUMMARY = 0.1
TEMPERATURE_DECISION = 0

# Recursion limit for graph execution
DEFAULT_RECURSION_LIMIT = 100
