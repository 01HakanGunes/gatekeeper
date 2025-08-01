# Text Agent - To-Do List

- Add drawing the mermaid diagram again.

- I need to clean the state value when the final decision happens.

- Make each threat detection log file unique to each session. Somehow for multiple sessions, the same threat detection process should be used. When user disables their own threat detection, their session should stop logging. When there are 0 sessions, the threat detection process should be stopped.

- If the state is not initialized, and a face is detected, initialize the state with the face (send greeting and ask something).

- Make creating init state more automated

- Remove the 2 seperate schemas and use a single json schema for threat detection and vision schema

- After threat level high, directly jump to decision as call security and reset graph.

- Remove the thinking extraction and directly use from langchain

- Same session as long as the detected face is same.
