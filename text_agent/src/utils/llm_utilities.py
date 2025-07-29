import json
import re
from typing import Optional

from src.utils import prompt_manager
from src.utils.camera import image_file_to_base64
from models.llm_config import llm_vision_json


def analyze_image_with_prompt(
    image_path: str, prompt_key: str, schema_key: str
) -> Optional[dict]:
    """
    Analyzes an image using a specified prompt and schema, and returns the LLM's response as a JSON object.

    Args:
        image_path (str): Path to the image file.
        prompt_key (str): Key for the prompt to use (e.g., "analyze_image_threat_json").
        schema_key (str): Key for the schema to use (e.g., "vision_schema").

    Returns:
        Optional[dict]: The parsed JSON response from the LLM, or None if there was an error.
    """
    # Convert image to base64
    try:
        image_b64 = image_file_to_base64(image_path)
    except Exception as e:
        print(f"⚠️ Could not convert image to base64: {e}")
        return None

    if not image_b64:
        print("⚠️ Skipping vision analysis due to missing image base64.")
        return None

    # Get the schema and generate the prompt
    schema = prompt_manager.get_schema(schema_key)
    try:
        prompt = prompt_manager.invoke_prompt(
            "vision", prompt_key, json_schema=json.dumps(schema, indent=2)
        )
    except Exception as e:
        print(f"⚠️ Error generating prompt: {e}")
        return None

    # Create the message for the LLM
    image_part = {
        "type": "image_url",
        "image_url": f"data:image/jpeg;base64,{image_b64}",
    }
    text_part = {"type": "text", "text": prompt}
    message = {
        "role": "user",
        "content": [image_part, text_part],
    }

    # Invoke the LLM
    try:
        response = llm_vision_json.invoke([message])
        print("success vision data received from llm model.")
    except Exception as e:
        print(f"⚠️ Vision LLM response error: {e}")
        return None

    # Extract and normalize the content
    content = response.content if hasattr(response, "content") else str(response)
    if isinstance(content, list):
        content = "\n".join(str(x) for x in content)

    # Parse the content to JSON
    try:
        vision_data = json.loads(content)
        print("success vision data received from llm model and converted to json.")
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                vision_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                print("⚠️ No valid JSON found in LLM response")
                return None
        else:
            print("⚠️ No JSON object found in LLM response")
            return None
    except Exception as e:
        print(f"⚠️ Error parsing LLM response: {e}")
        return None

    return vision_data
