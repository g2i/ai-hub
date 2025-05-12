# CLAUDE.md

This file provides instructions to Claude when working with the notebooks in this directory.

## Model Instructions

When working with any code in the notebooks:

1. **ALWAYS use `gpt-4.1-nano` as the model**: When you see any model initialization or setup, always use "gpt-4.1-nano" as the model. This is the default model for this project.

2. **Function calling for structured output**: When using structured output with OpenAI models, always specify `method="function_calling"` to avoid warnings.

Example:
```python
# Correct initialization
model = ChatOpenAI(model="gpt-4.1-nano")

# Correct structured output
structured_llm = model.with_structured_output(SomeSchema, method="function_calling")
```

3. **Default model initialization**: When initializing models, use this helper function:
```python
def init_chat_model(model_name="gpt-4.1-nano", model_provider="openai"):
    if model_provider == "openai":
        return ChatOpenAI(model=model_name)
    # Add other providers as needed
    return None
```

## Standard Settings

- Always set `LANGCHAIN_DISABLE_GRAPH_VIZ = "true"` in the environment variables
- When invoking LangGraph, ensure proper error handling for model responses