#!/bin/bash
# Script to configure the system to use external LLM by default

# Set environment variables to enable external LLM
export MARKER_LLM_PROVIDER=openai
export OPENAI_BASE_URL=http://asus-tus:1234/v1
export OPENAI_MODEL=gemini-2.5-flash
export OPENAI_API_KEY=lm-studio

echo "External LLM configuration set:"
echo "MARKER_LLM_PROVIDER=$MARKER_LLM_PROVIDER"
echo "OPENAI_BASE_URL=$OPENAI_BASE_URL"
echo "OPENAI_MODEL=$OPENAI_MODEL"
echo "OPENAI_API_KEY=**********"  # Mask the API key

echo ""
echo "The system will now use the external LLM when processing PDFs."
echo "Make sure your LLM service (e.g., LM Studio) is running at the specified endpoint."