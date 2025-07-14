# JSON Schema Implementation Summary

## Changes Made

### 1. Created `config/prompts/schemas.json`
- **Purpose**: Centralized JSON schema definitions for LLM structured outputs
- **Content**: Four main schemas used throughout the application:
  - `decision_schema`: For security decision making with confidence and reasoning
  - `session_schema`: For session detection (new vs continuing visitor)
  - `extraction_schema`: Template for field extraction with confidence scores
  - `contact_validation_schema`: For validating contact persons against known list

### 2. Enhanced `PromptManager` (`src/utils/prompt_manager.py`)
- **Added**: `_load_schemas()` method to load JSON schemas from file
- **Added**: `get_schema(schema_name)` method to retrieve specific schemas
- **Updated**: Constructor to initialize schemas during startup
- **Import**: Added `json` import for schema loading

### 3. Updated Node Files

#### `src/nodes/decision_nodes.py`
- **Replaced**: Hardcoded `decision_schema` dictionary
- **With**: `prompt_manager.get_schema("decision_schema")`
- **Benefits**: Schema definition now externalized and maintainable

#### `src/nodes/input_nodes.py`
- **Replaced**: Hardcoded `session_schema` dictionary
- **With**: `prompt_manager.get_schema("session_schema")`
- **Benefits**: Consistent session detection structure

#### `src/nodes/processing_nodes.py`
- **Replaced**: Hardcoded `validation_schema` dictionary in `validate_contact_person()`
- **With**: `prompt_manager.get_schema("contact_validation_schema")`
- **Updated**: Extraction schema to reference base template from schemas file
- **Benefits**: Consistent validation and extraction patterns

## Architectural Benefits

### 1. **Maintainability**
- ✅ Single source of truth for all JSON schemas
- ✅ Easy to update schema definitions without code changes
- ✅ Version control friendly schema management

### 2. **Consistency**
- ✅ All nodes use the same schema structure
- ✅ Consistent field names and validation rules
- ✅ Uniform confidence scoring across components

### 3. **Extensibility**
- ✅ Easy to add new schemas for future features
- ✅ Schema reuse across different nodes possible
- ✅ Support for schema versioning if needed

### 4. **Developer Experience**
- ✅ Clear separation between code logic and data structure
- ✅ IDE support for JSON schema editing
- ✅ Better debugging with externalized schema definitions

## Usage Example

```python
# Before (hardcoded):
decision_schema = {
    "decision": "string (one of: allow_request, call_security, deny_request)",
    "confidence": "number between 0 and 1",
    # ... more fields
}

# After (externalized):
decision_schema = prompt_manager.get_schema("decision_schema")
```

## File Structure
```
config/prompts/
├── schemas.json          # ← NEW: JSON schema definitions
├── templates.yaml        # ← Existing: Prompt templates
└── field_descriptions.yaml # ← Existing: Field descriptions
```

This implementation follows the established pattern in your project of using the `config/prompts` directory for configuration data, while properly separating JSON schema definitions from YAML-based prompt templates.
