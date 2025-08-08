# Text Agent - To-Do List

- 1 sid that is created by socketio enough?

- i need sids' saved of each session so backend can send them message whenever they need.

- vision_log file should include session id field for each session, Each send image should be sent with session id and image processor should save the results to appropriate one.

- With socketio setup, most of the time i get echo response, because i removed the seperate face detection feedback.
  When session deactivated, return "show your face", and when a new session starts return "Hello sir whatup, what do you want sir?"
  Send the messages from the face detection process by using socketio events.

- multiple langgraph instances needed or not needed for multi-session setup i want?

- Image processor should activate, reset session with interprocess flag value assignment.

- If the state is not initialized, and a face is detected, initialize the state with the face (send greeting and ask something).
  After no face detected for 10 frames, clear the state. Set the state flag to inactive. When the flag is inactive and there is a face detected, initialize the state with the face (send greeting and ask something).

- Make each threat detection log file unique to each session. Somehow for multiple sessions, the same threat detection process should be used. When user disables their own threat detection, their session should stop logging. When there are 0 sessions, the threat detection process should be stopped.

- After threat level high, directly jump to decision as call security and reset graph.

- Try on mobile device with chromium browser

## Refactoring

- vision_data_log.json -> vision_log.json

- Change the threatLog naming with visionLog everywhere

- docker compose file position change

- Do i really need this custom lifespan for fastapi: "async def lifespan(app: FastAPI):"

- Import statements are all around the code.
