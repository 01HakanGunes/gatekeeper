# Security Gate System - To-Do List

- Deploy the project as docker container to the server
- 2 containers, containarized ollama and the main Agentic System
- openai whisper

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