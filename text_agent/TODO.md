# Text Agent - To-Do List

## Bugs/Fixes

- !Threat level is not set correctly.

- !Security question? Agent still asks and works badly. Deprecated.

- My .env data is not passed.

- After threat level high, directly jump to decision as call security and reset graph.

- Add the decisions as seperate tools.

- Too slow

## Features

- Find a dummy way to enable face recognition.

- Cam id based authorization. Create auth table (json). Deterministic (no llm process) json load with permissions.

- Name based auth.

- If cargo arrived, check if a cargo is expected (logged), in a file if not reject (send notification)

## Testing

- !Test the whole tree and complete the process.

- Test with multiple sessions.

- Try on mobile device with chromium browser

## Refactoring

- !Change the threatLog naming with visionLog everywhere

- docker compose file position change

- Import statements are all around the code.

- not shutting down gracefully.
