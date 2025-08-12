# Text Agent - To-Do List

## Bugs/Fixes

- Stop development debug then merge into main with frontend

- Each time threat level high extracted, another invoke to the graph in parallel happens. Instead of this only fetch from the state, when thet high threat detected somehow stop the processing of following high threat frames until the state is cleared and session initialized again from scratch.

- Analyze threat level node is depreacted delete it.

- After threat level high, directly jump to decision as call security and reset graph.
  Make the image processor trigger the graph when the threat level field is high (find a way to jump to the decision part/ is it really necessary)

- Add the decisions as seperate tools.

- Too slow

- My .env data is not passed.

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

- Deprecated function inside sockets.py

- !Change the threatLog naming with visionLog everywhere

- docker compose file position change

- Import statements are all around the code.

- not shutting down gracefully.
