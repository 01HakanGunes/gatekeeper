# Security Gate System - To-Do List

- dashboard/logging

- face-recognition

- After threat level high, directly jump to decision as call security and reset graph.

- Remove the thinking extraction and directly use from langchain

- Mobile app to use as camera / maybe normal camera setup for faster testing

### **Implement Logging System**
- Replace all `print()` statements with proper logging using Python's `logging` module
- Add configurable log levels (DEBUG, INFO, WARNING, ERROR) 
- Create separate loggers for different components (input, processing, decision, email)
- Add log rotation and file output options for production use
- This will improve debugging capabilities and provide better monitoring


- Note (Image Tagging
Issue: If you push images to Docker Hub with the same tag (e.g., latest), docker compose might not pull the updated image because Docker could assume the local image is current. This could result in your server running an outdated version.
Recommendation: Use unique tags for each build, such as the Git commit hash (e.g., myimage:abc123) or a build number. Then, ensure docker compose uses the new tag. You could:)

- Create example voice files to test the whisper.
- Create a node responsible for whisper connnection and text input flow.
- Async, sessions?