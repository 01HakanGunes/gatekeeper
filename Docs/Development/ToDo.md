
- i need to switch the some llm outputs to the json format (that are not ai_message to the human).

- Manage Prompts in a different controlled place. Add fallbacks or prompt switches to the nodes

- Change summarize with shorten where we only keep the last x messages always


- there is an extra layer in the "validate_contact_person" node that calls an llm again but is not connected correctly. We already have the contact_person name extracted.

- I can extract all the fields in "1" llm prompt turn as json.