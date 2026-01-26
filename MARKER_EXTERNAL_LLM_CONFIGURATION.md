# Configuring Marker to Use External LLMs (LM Studio and Others)

## Overview
The marker library can be configured to use external Large Language Models (LLMs) to enhance PDF processing. This is particularly useful for complex documents where LLMs can help with table merging, content understanding, and layout analysis.

## Configuration Options

### Environment Variables
To enable external LLM usage with marker, set the following environment variables:

#### For LM Studio (OpenAI Compatible)
```bash
export MARKER_LLM_PROVIDER=openai
export OPENAI_BASE_URL=http://asus-tus:1234/v1  # Default LM Studio endpoint
export OPENAI_MODEL=gemini-2.5-flash  # Model name as configured in LM Studio
export OPENAI_API_KEY=lm-studio  # Default API key for LM Studio
```

#### For Ollama
```bash
export MARKER_LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434  # Default Ollama endpoint
export OLLAMA_MODEL=llama3.2-vision  # Model name as configured in Ollama
```

#### For OpenAI
```bash
export MARKER_LLM_PROVIDER=openai
export OPENAI_BASE_URL=https://api.openai.com/v1  # OpenAI API endpoint
export OPENAI_MODEL=gpt-4o  # Model name
export OPENAI_API_KEY=your_openai_api_key_here
```

#### For Google Gemini
```bash
export MARKER_LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_gemini_api_key_here
```

#### For Anthropic Claude
```bash
export MARKER_LLM_PROVIDER=claude
export CLAUDE_API_KEY=your_claude_api_key_here
```

#### For Azure OpenAI
```bash
export MARKER_LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
export AZURE_OPENAI_DEPLOYMENT=your-deployment-name
export AZURE_OPENAI_API_KEY=your_azure_openai_api_key
```

## Integration with the RAG System

### Docker/Container Environments
When running in containers, ensure the environment variables are properly set in your container configuration:

```yaml
# docker-compose.yml example
services:
  rag-service:
    environment:
      - MARKER_LLM_PROVIDER=openai
      - OPENAI_BASE_URL=http://host.docker.internal:1234/v1  # For accessing host services from container
      - OPENAI_MODEL=lm-studio
      - OPENAI_API_KEY=lm-studio
```

### Configuration in Application
The changes to `pdf_converter.py` automatically detect these environment variables and configure the marker library accordingly.

## Benefits of Using External LLMs

1. **Enhanced Accuracy**: LLMs can better understand complex layouts and merge tables across pages
2. **Improved Table Processing**: Better handling of multi-page tables and complex structures
3. **Better Content Understanding**: More accurate classification of document elements
4. **Advanced Post-Processing**: LLMs can clean up and refine the extracted content

## Performance Considerations

1. **Processing Time**: Using external LLMs will significantly increase processing time
2. **Cost**: Using commercial LLMs (OpenAI, Claude, etc.) will incur costs
3. **Network Dependency**: Processing depends on network connectivity to the LLM service
4. **Privacy**: Document content will be sent to the external LLM service

## Troubleshooting

### Common Issues

1. **Connection Errors**: Ensure the LLM service is running and accessible at the configured endpoint
2. **Authentication Errors**: Verify API keys are correct and have sufficient permissions
3. **Model Not Found**: Check that the model name matches what's available in your LLM service
4. **Timeout Errors**: Increase timeout values if processing large documents

### Debugging Tips

1. Check that environment variables are properly set
2. Verify the LLM service is accessible with a simple test request
3. Monitor logs for specific error messages
4. Start with simple documents to verify configuration

## Security Considerations

1. **API Key Security**: Store API keys securely and avoid hardcoding them
2. **Network Security**: Use HTTPS connections when possible
3. **Data Privacy**: Be aware of data privacy implications when sending documents to external services
4. **Access Control**: Restrict access to the configuration endpoints

## Example Usage

After setting the environment variables, the system will automatically use the configured external LLM when processing PDFs. The conversion process remains the same from the user perspective, but the underlying processing will leverage the external LLM for enhanced accuracy.