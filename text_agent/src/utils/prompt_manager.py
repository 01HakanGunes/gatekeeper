import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.prompts.base import BasePromptTemplate


class PromptManager:
    def __init__(self, prompts_dir: Optional[str] = None):
        if prompts_dir is None:
            # Get the prompts directory relative to the project root
            current_dir = Path(__file__).parent.parent.parent  # Go up to text_agent/
            self.prompts_dir = current_dir / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        self._templates: Dict[str, Dict[str, BasePromptTemplate]] = {}
        self._data: Dict[str, Any] = {}
        self._field_data: Dict[str, Any] = {}
        self._load_prompts()
        self._load_field_data()

    def _load_prompts(self):
        """Load all prompt templates from YAML/JSON files"""
        templates_file = self.prompts_dir / "templates.yaml"

        if templates_file.exists():
            with open(templates_file, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f)

            for category, prompts in self._data.items():
                self._templates[category] = {}
                for prompt_name, config in prompts.items():
                    # Skip non-template entries (like decision_messages, available_decisions, etc.)
                    if not isinstance(config, dict) or "template" not in config:
                        continue

                    template_str = config["template"]
                    input_vars = config["input_variables"]
                    prompt_type = config.get("type", "string")

                    if prompt_type == "chat":
                        # For chat templates, treat as user message
                        template = ChatPromptTemplate.from_messages(
                            [("user", template_str)]
                        )
                    else:
                        # Use from_template which automatically infers input_variables
                        template = PromptTemplate.from_template(template_str)

                    self._templates[category][prompt_name] = template

    def _load_field_data(self):
        """Load field descriptions and related data"""
        field_file = self.prompts_dir / "field_descriptions.yaml"

        if field_file.exists():
            with open(field_file, "r", encoding="utf-8") as f:
                self._field_data = yaml.safe_load(f)

    def get_prompt(self, category: str, name: str) -> Optional[BasePromptTemplate]:
        """Get a prompt template by category and name"""
        return self._templates.get(category, {}).get(name)

    def format_prompt(self, category: str, name: str, **kwargs) -> str:
        """Get formatted prompt string"""
        template = self.get_prompt(category, name)
        if template is None:
            raise ValueError(f"Prompt not found: {category}/{name}")

        # Handle both PromptTemplate and ChatPromptTemplate
        if hasattr(template, "format_prompt"):
            prompt_value = template.format_prompt(**kwargs)
            return prompt_value.to_string()
        else:
            return template.format(**kwargs)

    def invoke_prompt(self, category: str, name: str, **kwargs):
        """Get prompt value that can be passed to LLM"""
        template = self.get_prompt(category, name)
        if template is None:
            raise ValueError(f"Prompt not found: {category}/{name}")

        return template.invoke(kwargs)

    def get_data(self, category: str, key: Optional[str] = None) -> Any:
        """Get static data from templates (non-template entries)"""
        if key is None:
            return self._data.get(category, {})
        return self._data.get(category, {}).get(key, {})

    def get_field_data(self, key: Optional[str] = None) -> Any:
        """Get field-related data"""
        if key is None:
            return self._field_data
        return self._field_data.get(key, {})

    def get_field_description(self, field: str) -> str:
        """Get description for a specific field"""
        field_descriptions = self.get_field_data("visitor_profile_fields")
        return field_descriptions.get(field, "")

    def get_field_question(self, field: str, **kwargs) -> str:
        """Get question for a specific field"""
        field_questions = self.get_field_data("field_questions")
        question = field_questions.get(field, "")
        if kwargs:
            return question.format(**kwargs)
        return question

    def get_extraction_prefixes(self, field: str) -> list:
        """Get list of prefixes to remove from extraction results"""
        prefixes = self.get_field_data("extraction_prefixes")
        formatted_prefixes = []
        for prefix in prefixes:
            formatted_prefix = prefix.format(
                field=field, field_capitalized=field.capitalize()
            )
            formatted_prefixes.append(formatted_prefix)
        return formatted_prefixes


# Global instance
prompt_manager = PromptManager()
