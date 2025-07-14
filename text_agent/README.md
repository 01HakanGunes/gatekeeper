# Security Gate System - Modular Architecture

This project implements a security gate system using LangChain and LangGraph with a clean, modular architecture.

## 📁 Project Structure

```
text_agent/
├── src/                      # Core source code
│   ├── core/                 # Core system components
│   │   ├── __init__.py
│   │   ├── state.py          # TypedDict definitions (VisitorProfile, State)
│   │   ├── constants.py      # System constants (CONTACTS, MAX_HUMAN_MESSAGES)
│   │   └── graph.py          # Graph builder and configuration
│   │
│   ├── nodes/                # LangGraph node implementations
│   │   ├── __init__.py
│   │   ├── input_nodes.py    # Input handling (receive_input, detect_session, etc.)
│   │   ├── processing_nodes.py # Profile processing (check_visitor_profile, etc.)
│   │   └── decision_nodes.py # Decision making (make_decision, notify_contact)
│   │
│   ├── tools/                # LangChain tools
│   │   ├── __init__.py
│   │   └── communication.py  # Email sending tool
│   │
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── extraction.py     # Text extraction utilities
│
├── models/                   # LLM configuration
│   ├── __init__.py
│   └── llm_config.py         # LLM initialization and management
│
├── config/                   # Configuration files
│   └── settings.py           # Application settings and constants
│
├── examples/                 # Usage examples
│   └── security_gate.py      # Main application example
│
├── agent.py                  # Original monolithic file (kept for reference)
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application

```bash
# Run as a Python module
python -m examples.security_gate
```

### Using the Modular Components

```python
from src.core.graph import create_security_graph, create_initial_state
from config.settings import DEFAULT_RECURSION_LIMIT

# Create the security graph
graph = create_security_graph()

# Create initial state
initial_state = create_initial_state()

# Run the security screening process
result = graph.invoke(initial_state, {"recursion_limit": DEFAULT_RECURSION_LIMIT})
```

## 🏗️ Architecture Components

### Core Components (`src/core/`)

- **`state.py`**: Defines the core data structures
  - `VisitorProfile`: Visitor information TypedDict
  - `State`: Main graph state TypedDict
  
- **`constants.py`**: System-wide constants
  - `CONTACTS`: Predefined contact list
  - `MAX_HUMAN_MESSAGES`: Conversation length limit
  
- **`graph.py`**: Graph construction and configuration
  - `create_security_graph()`: Builds the complete LangGraph workflow
  - `create_initial_state()`: Creates initial state for new sessions

### Node Implementations (`src/nodes/`)

#### Input Nodes (`input_nodes.py`)
- `receive_input()`: Handle user input with validation
- `detect_session()`: Determine if same or new visitor session
- `check_context_length()`: Monitor conversation length
- `summarize()`: Compress conversation history
- `reset_conversation()`: Clear state for new visitor

#### Processing Nodes (`processing_nodes.py`)  
- `check_visitor_profile_node()`: Extract visitor information using LLM
- `validate_contact_person()`: Match contacts against known list
- `question_visitor()`: Ask specific questions for missing information
- `check_visitor_profile_condition()`: Determine if profile is complete

#### Decision Nodes (`decision_nodes.py`)
- `make_decision()`: Security decision making based on profile
- `notify_contact()`: Send email notifications to contacts
- `check_decision_for_notification()`: Route based on decision type

### Tools (`src/tools/`)

- **`communication.py`**: Email communication tool
  - `send_email()`: LangChain tool for sending notifications

### Utilities (`src/utils/`)

- **`extraction.py`**: Text processing utilities
  - `extract_answer_from_thinking_model()`: Parse LLM responses

### Models (`models/`)

- **`llm_config.py`**: LLM initialization and management
  - Configures different LLMs for different purposes (main, decision, email, etc.)
  - Uses settings from `config/settings.py`

### Configuration (`config/`)

- **`settings.py`**: Application configuration
  - Model names and parameters
  - Temperature settings
  - System limits

## 🔄 Workflow

1. **Input Processing**: User input is received and validated
2. **Session Management**: System detects new vs continuing sessions
3. **Profile Extraction**: LLM extracts visitor information from conversation
4. **Contact Validation**: Visitor contacts are matched against known list
5. **Information Gathering**: System asks for missing required information
6. **Decision Making**: Security decision based on complete profile
7. **Notification**: Contacts are notified if access is granted

## 🛠️ Extending the System

### Adding New Node Types

1. Create new files in `src/nodes/` for your node category
2. Import and register in `src/nodes/__init__.py`
3. Add nodes to graph in `src/core/graph.py`

### Adding New Tools

1. Create tool functions in `src/tools/`
2. Export in `src/tools/__init__.py`
3. Use in relevant node implementations

### Modifying LLM Configuration

1. Update model settings in `config/settings.py`
2. Modify LLM initialization in `models/llm_config.py`
3. Use new models in node implementations

## 📝 Benefits of Modular Architecture

1. **Separation of Concerns**: Each file has a specific responsibility
2. **Reusability**: Components can be imported and used independently
3. **Testability**: Individual components can be tested in isolation
4. **Maintainability**: Changes are localized to specific modules
5. **Scalability**: New features can be added without affecting existing code
6. **Configuration Management**: Settings are centralized and easily modified

## 🔧 Dependencies

See `requirements.txt` for complete dependency list. Key dependencies:
- `langchain-ollama`: For LLM integration
- `langgraph`: For graph-based workflows
- `typing-extensions`: For enhanced type hints

## 📚 Original vs Modular

The original `agent.py` file contained all functionality in a single file (~940 lines). The modular version splits this into:
- **Core**: 4 files for fundamental components
- **Nodes**: 3 files organizing workflow steps by purpose
- **Tools**: 1 file for external integrations
- **Models**: 1 file for LLM management
- **Config**: 1 file for settings
- **Examples**: 1 file demonstrating usage

This organization makes the codebase much more maintainable and allows for easier collaboration and testing.