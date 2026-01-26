# Marker Library LLM Configuration Guide

## Issue Description

Users observed the message "Loading models (this may take several minutes on first use)..." and assumed that local models were being used instead of external LLMs. However, this message refers to the base models (layout detection, OCR, etc.) that marker needs to load regardless of whether LLM enhancement is enabled.

## Clarification

The marker library operates in two phases:
1. **Base Model Loading**: Loads essential models for layout detection, OCR, table recognition, etc. This is necessary for all conversions and causes the "Loading models..." message.
2. **LLM Enhancement**: Optionally enhances the conversion with an external LLM for better accuracy and understanding of complex layouts.

## Solution Implemented

1. **Environment Variable Propagation**: Modified the `_perform_conversion` method in `pdf_converter.py` to explicitly set environment variables that the marker library might expect directly for LLM enhancement.

2. **Cleanup Mechanism**: Added a `finally` block to clean up the environment variables after the conversion is complete to avoid affecting other parts of the application.

3. **Proper Exception Handling**: Ensured that environment variables are cleaned up even if an exception occurs during the conversion process.

4. **Enhanced Logging**: Added logging to clarify when base models are loaded versus when LLM enhancement is configured.

## Files Modified

- `/root/qwen_test/ai_agent/rag_component/pdf_converter.py`

## Configuration Requirements

To use external LLMs with the marker library for enhancement, the following environment variables must be set:

### For OpenAI-compatible APIs:
```bash
export MARKER_LLM_PROVIDER=openai
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Or your custom endpoint
export OPENAI_MODEL="gpt-4"  # Or your preferred model
export OPENAI_API_KEY="your-api-key"
```

### For Ollama:
```bash
export MARKER_LLM_PROVIDER=ollama
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2-vision"  # Or your preferred model
```

### For Google Gemini:
```bash
export MARKER_LLM_PROVIDER=gemini
export GEMINI_API_KEY="your-api-key"
```

### For Anthropic Claude:
```bash
export MARKER_LLM_PROVIDER=claude
export CLAUDE_API_KEY="your-api-key"
```

### For Azure OpenAI:
```bash
export MARKER_LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT="https://your-resource.azure.openai.com"
export AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
export AZURE_OPENAI_API_KEY="your-api-key"
```

## Verification

Run the following command to verify the configuration:
```bash
cd /root/qwen_test/ai_agent/rag_component && python check_marker_config.py
```

## Important Notes

- The "Loading models (this may take several minutes on first use)..." message refers to the base models and is normal behavior regardless of LLM configuration.
- The external LLM is used for enhancement during the conversion process, improving accuracy for complex documents.
- The environment variables are temporarily set during the conversion process and cleaned up afterward to avoid conflicts with other parts of the application.
- Default values are provided for common configurations to ensure the system works even if some environment variables are not explicitly set.
- The marker library will now properly use the configured external LLM service for enhanced PDF conversion when `MARKER_LLM_PROVIDER` is set.