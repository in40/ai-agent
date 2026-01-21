# Enhanced Security Features

## Overview

This document describes the enhanced security mechanisms in the AI agent, focusing on SQL validation, security analysis, and protection against harmful queries.

## Key Security Features

### 1. Basic SQL Validation
- Blocks harmful SQL commands (DROP, DELETE, INSERT, UPDATE, etc.)
- Ensures queries start with SELECT or WITH
- Detects potential SQL injection patterns
- Limits to single statements
- Filters out SQL comments that could be used maliciously

### 2. Advanced Security LLM Analysis
- Uses an LLM to detect potentially harmful SQL queries while reducing false positives
- Distinguishes between legitimate column/table names and actual malicious commands
- Provides contextual analysis based on the database schema
- Offers confidence levels for security assessments
- Supports multiple LLM providers for security analysis (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)

This addresses issues where legitimate column names like `created_at` were incorrectly flagged as harmful due to containing substrings like "create".

### 3. Security Check After Refinement
- Validates refined SQL queries for security issues
- Ensures that refined queries are also safe before execution
- Prevents bypass of security checks through query refinement

### 4. Configurable Security Policies
- `USE_SECURITY_LLM`: Whether to use the advanced security LLM analysis (default: true)
- `TERMINATE_ON_POTENTIALLY_HARMFUL_SQL`: Whether to block potentially harmful SQL (default: true)
- Option to disable SQL blocking for trusted environments

### 5. Disabling SQL Blocking
To disable the SQL blocking feature, you can:

1. Pass `disable_sql_blocking=True` when calling `run_enhanced_agent()`:
   ```python
   result = run_enhanced_agent("Your request", disable_sql_blocking=True)
   ```

2. Set the environment variable `USE_SECURITY_LLM=false`:
   ```bash
   export USE_SECURITY_LLM=false
   ```

**Warning:** Disabling SQL blocking can pose security risks and should only be done in trusted environments.

## Security Configuration

The security features can be configured via environment variables in the `.env` file:

- `SECURITY_LLM_MODEL`: Model to use for security analysis (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `SECURITY_LLM_PROVIDER`: Provider for security analysis (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)
- `SECURITY_LLM_HOSTNAME`: Hostname for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_PORT`: Port for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_API_PATH`: API path for security LLM service (for non-OpenAI providers)
- `USE_SECURITY_LLM`: Whether to use the advanced security LLM analysis (default: true)
- `TERMINATE_ON_POTENTIALLY_HARMFUL_SQL`: Whether to block potentially harmful SQL (default: true)

## Security Validation Process

1. **Initial Validation**: Basic keyword matching for harmful SQL commands
2. **Advanced Analysis**: LLM-based security analysis to reduce false positives
3. **Contextual Analysis**: Considers database schema context for more accurate assessments
4. **Confidence Assessment**: Provides confidence levels for security decisions
5. **Final Decision**: Blocks or allows the query based on security analysis

## Security Best Practices

1. Keep the security LLM enabled in production environments
2. Regularly review and update security policies
3. Monitor security logs for potential threats
4. Use appropriate LLM models for security analysis
5. Ensure database connections are properly secured
6. Regularly update dependencies to address security vulnerabilities