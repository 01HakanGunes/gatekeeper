# Security Gate System - To-Do List

### **Implement Structured JSON Output for LLM Responses**
- Convert LLM outputs that are not AI messages to humans into structured JSON format
- Focus on field extraction in `check_visitor_profile_node` and decision making in `make_decision`
- Use JSON schemas to enforce consistent output formats

### **Add Message History Management Options**
- Implement a "shorten" strategy alongside the existing "summarize" function in `src/nodes/input_nodes.py`
- Add command-line argument `--history-mode` with options: `summarize` or `shorten`
- The shorten mode should keep only the last N messages (configurable via `config/settings.py`)

### **Optimize Contact Person Validation Logic**
- Remove redundant LLM call in `validate_contact_person` node
- The node should only validate the already-extracted contact_person against the CONTACTS list
- Streamline the flow: extract → validate against list → proceed

### **Create Unified Field Extraction Tool**
- Implement a single LLM call that extracts all visitor profile fields as a structured JSON object
- Replace the current field-by-field extraction loop in `check_visitor_profile_node`
- Create a dedicated tool function that returns: `{"name": "...", "purpose": "...", "threat_level": "...", "affiliation": "..."}`

### **Complete Email Notification Implementation**
- The `send_email` tool is currently a mock implementation
- Integrate with a real email service (gmail direct main sending)
- Add email template management through the PromptManager

### **Refine Node Organization and Categories**
- Review and improve the current node categorization (`input_nodes`, `processing_nodes`, `decision_nodes`)
- Consider splitting complex nodes into smaller, single-responsibility nodes
- Evaluate if some functionality should be tools rather than nodes

### **Implement Comprehensive Logging System**
- Replace all `print()` statements with proper logging using Python's `logging` module
- Add configurable log levels (DEBUG, INFO, WARNING, ERROR) 
- Create separate loggers for different components (input, processing, decision, email)
- Add log rotation and file output options for production use
- This will improve debugging capabilities and provide better monitoring

### **Implement Multi-Language Support**
- Add internationalization (i18n) support for the security gate system
- Create language packs for common languages (English, Spanish, French, etc.)
- Allow language selection through command-line argument or configuration
- Translate all user-facing messages, prompts, and questions
- Use the PromptManager to handle language-specific templates and responses

### **Add Camera Verification Logic**
- Implement computer vision capabilities to verify visitor claims through camera feed analysis
- Create a new node `verify_visual_claims` that processes camera frames to validate visitor statements
- Use image recognition models to detect:
  - Delivery packages for delivery personnel
  - Professional attire for business visitors
  - Identification badges or uniforms
  - Suspicious items or behaviors
- Integrate with existing visitor profile to cross-reference visual evidence with stated purpose
- Add confidence scoring for visual verification results
- Create fallback mechanisms when camera feed is unavailable or unclear
- Store verification results in the state for decision-making process