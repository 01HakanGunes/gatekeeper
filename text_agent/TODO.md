# Text Agent - To-Do List (Do not delete completed tasks)

## Bugs/Fixes

- Put a cooldown to send messages from clint(a cap maybe)

## Features

- Cam id based authorization.

- If cargo arrived, check if a cargo is expected (logged), in a file if not reject (send notification)

## Testing

- Try on mobile device with chromium browser

## Refactoring

- Deprecated function inside sockets.py
- docker compose file position change
- Import statements are all around the code.
- not shutting down gracefully.
- Analyze threat level node is depreacted delete it.
- Make agent response a seperate field in the state

# Docs

- List the features

## Completed

- Added support for employee data
- Env variable passed to the container from github secrets in the build process.
