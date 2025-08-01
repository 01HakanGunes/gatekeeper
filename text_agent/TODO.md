# Text Agent - To-Do List

- Is the sent image in base64 format?

- Add the threat detection as an api endpoint and connect with dashboard

- If the state is not initialized, and a face is detected, initialize the state with the face (send greeting and ask something).

- Update graph with clearer node structure

- Make creating init state more automated

- Remove the 2 seperate schemas and use a single json schema for threat detection and vision schema

- Update the prompts for better results(change model settings etc)

- After threat level high, directly jump to decision as call security and reset graph.

- Remove the thinking extraction and directly use from langchain

- Fix the echo problem where not the all feedback appended to the message state.

- I need to clean the state value when the final decision happens.

- Same session as long as the detected face is same.

- New deploy
