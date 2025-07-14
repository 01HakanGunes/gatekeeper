def extract_answer_from_thinking_model(response):
    """
    Extract the actual answer from thinking models that wrap responses in <think> tags.

    Args:
        response: The LLM response object or string

    Returns:
        str: The extracted answer content
    """
    if hasattr(response, "content"):
        content = response.content
    else:
        content = str(response)

    # Check if the response contains a thinking section
    if "<think>" in content:
        # Split by </think> and get everything after it
        parts = content.split("</think>", 1)
        if len(parts) > 1:
            return parts[1].strip()

    # Return the original content if no think tags found
    return content.strip()
