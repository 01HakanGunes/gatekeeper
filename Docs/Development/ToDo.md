# Security Gate System - To-Do List

### CI/CD Part
- set github actions,
- github actions, github self-hosted runner
- Github actions to build the image for each git push remote
- docker hub/ GitHub Container Registry (GHCR) push image, github runner should execute the "docker compose" from the ssh server so it pulls the new image.

- Note (Image Tagging
Issue: If you push images to Docker Hub with the same tag (e.g., latest), docker compose might not pull the updated image because Docker could assume the local image is current. This could result in your server running an outdated version.
Recommendation: Use unique tags for each build, such as the Git commit hash (e.g., myimage:abc123) or a build number. Then, ensure docker compose uses the new tag. You could:)

- Build the image on the ssh server?


- Create example voice files to test the whisper.
- Create a node responsible for whisper connnection and text input flow.

- python import module issues when containerized

- Make the agent nonstop work, when someones intreaction ends, it should return back

### **Implement Comprehensive Logging System**
- Replace all `print()` statements with proper logging using Python's `logging` module
- Add configurable log levels (DEBUG, INFO, WARNING, ERROR) 
- Create separate loggers for different components (input, processing, decision, email)
- Add log rotation and file output options for production use
- This will improve debugging capabilities and provide better monitoring

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