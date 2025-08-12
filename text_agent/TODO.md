# Text Agent - To-Do List

## Bugs/Fixes

- When the final decision happens i need to reset the state but the last message from state is used as the user feedback. Fix that
  (use a seperate field)

- Add the decisions as seperate tools.

- Too slow

- My .env data is not passed.

- Put a cooldown to send messages from cleint

## Features

- Find a dummy way to enable face recognition.

- Cam id based authorization. Create auth table (json). Deterministic (no llm process) json load with permissions.

- Name based auth.

- If cargo arrived, check if a cargo is expected (logged), in a file if not reject (send notification)

## Testing

- Send multiple messages

- !Test the whole tree and complete the process.

- Test with multiple sessions.

- Try on mobile device with chromium browser

## Refactoring

- Deprecated function inside sockets.py

- !Change the threatLog naming with visionLog everywhere

- docker compose file position change

- Import statements are all around the code.

- not shutting down gracefully.

- Analyze threat level node is depreacted delete it.

- Make agent response a seperate field in the state
