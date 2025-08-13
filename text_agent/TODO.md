# Text Agent - To-Do List (Do not delete completed tasks)

## Bugs/Fixes

- My .env data is not passed.
- Put a cooldown to send messages from clint(a cap maybe)

## Features

- Find a dummy way to enable face recognition. (face recognition tool used / note this when the employee name entered to the chat)
- Cam id based authorization. Create auth table (json). Deterministic (no llm process) json load with permissions.
- Name based auth.
- If cargo arrived, check if a cargo is expected (logged), in a file if not reject (send notification)

## Testing

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

# Docs

- List the features

## Completed

- Added support for employee data
