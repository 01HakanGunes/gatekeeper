# Text Agent - To-Do List

- Socketio integration

- CORS for socketio

- multiple langgraph instances needed or not needed for multi-session setup i want?

- Dont send an image with chat message.

- Image processor should activate, reset session with interprocess flag value assignment.

- If the state is not initialized, and a face is detected, initialize the state with the face (send greeting and ask something).
  After no face detected for 10 frames, clear the state. Set the state flag to inactive. When the flag is inactive and there is a face detected, initialize the state with the face (send greeting and ask something).

- Make each threat detection log file unique to each session. Somehow for multiple sessions, the same threat detection process should be used. When user disables their own threat detection, their session should stop logging. When there are 0 sessions, the threat detection process should be stopped.

- After threat level high, directly jump to decision as call security and reset graph.

- Try on mobile device with chromium browser

## Refactoring

- docker compose file position change

- Remove the thinking extraction and directly use from langchain

- Do i really need this custom lifespan for fastapi: "async def lifespan(app: FastAPI):"

- Import statements are all around the code.
