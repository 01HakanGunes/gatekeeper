
- Manage Prompts in a different controlled place. Add fallbacks or prompt switches to the nodes
- program stucks for some reason maybe add limits

- summarizer test

- (Model abstractions: init_chat_model() for easy model switching

Prompt utilities: ChatPromptTemplate, MessagesPlaceholder

Runnable components: Use model.bind_tools(tools) for tool-calling)?

- Change summarize with shorten where we only keep the last x messages always

- initial usecase notify according to final decision

- i need to switch the some llm outputs to the json format (that are not ai_message to the human).