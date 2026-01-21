# SQL Validation and Security Analysis

## Overview

This document describes the comprehensive SQL validation and security analysis mechanisms in the AI agent, designed to prevent harmful SQL queries while maintaining functionality for legitimate database operations.

## Components

### 1. Basic SQL Validation

The basic SQL validation performs initial checks on generated SQL queries to prevent harmful operations:

#### Validation Checks
- **Command Blocking**: Blocks harmful SQL commands (DROP, DELETE, INSERT, UPDATE, etc.)
- **SELECT-Only Policy**: Ensures queries start with SELECT or WITH
- **Pattern Detection**: Identifies potential SQL injection patterns
- **Statement Limiting**: Restricts to single statements
- **Comment Filtering**: Blocks SQL comments that could be used maliciously

#### Implementation
The basic validation is implemented in the `validate_sql` node of the LangGraph workflow and in the `SQLValidator` class in `models/sql_validator.py`.

### 2. Advanced Security LLM Analysis

The advanced security analysis uses an LLM to detect potentially harmful SQL queries while reducing false positives:

#### Key Features
- **Context-Aware Analysis**: Considers database schema context to better distinguish between legitimate column names and harmful commands
- **Reduced False Positives**: Addresses issues where legitimate column names like `created_at` were incorrectly flagged as harmful due to containing substrings like "create"
- **Confidence Levels**: Provides confidence levels for security assessments
- **Multiple Provider Support**: Supports multiple LLM providers for security analysis (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)

#### Implementation
The advanced security analysis is implemented in the `validate_sql` node and the `SecurityLLMAnalyzer` class in `models/security_analyzer.py`.

### 3. Security Check After Refinement

Additional security validation is performed on refined SQL queries:

#### Purpose
- Ensures that refined queries are also safe before execution
- Prevents bypass of security checks through query refinement
- Validates that the refinement process didn't introduce security vulnerabilities

#### Implementation
This check is implemented in the `security_check_after_refinement` node in the LangGraph workflow.

## Configuration

### Environment Variables

The security validation can be configured via environment variables in the `.env` file:

- `SECURITY_LLM_MODEL`: Model to use for security analysis (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `SECURITY_LLM_PROVIDER`: Provider for security analysis (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)
- `SECURITY_LLM_HOSTNAME`: Hostname for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_PORT`: Port for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_API_PATH`: API path for security LLM service (for non-OpenAI providers)
- `USE_SECURITY_LLM`: Whether to use the advanced security LLM analysis (default: true)
- `TERMINATE_ON_POTENTIALLY_HARMFUL_SQL`: Whether to block potentially harmful SQL (default: true)

### Disabling SQL Blocking

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

## Validation Process

The SQL validation process follows this sequence:

1. **Initial Validation**: Basic keyword matching for harmful SQL commands
2. **Advanced Analysis**: LLM-based security analysis to reduce false positives (if enabled)
3. **Contextual Analysis**: Considers database schema context for more accurate assessments
4. **Confidence Assessment**: Provides confidence levels for security decisions
5. **Final Decision**: Blocks or allows the query based on security analysis

## Security Best Practices

1. **Keep Security LLM Enabled**: Maintain the advanced security analysis in production environments
2. **Regular Policy Reviews**: Periodically review and update security policies
3. **Monitor Security Logs**: Regularly check security logs for potential threats
4. **Appropriate Model Selection**: Use appropriate LLM models for security analysis
5. **Secure Connections**: Ensure database connections are properly secured
6. **Dependency Updates**: Regularly update dependencies to address security vulnerabilities
7. **Environment Isolation**: Use separate environments for development and production with appropriate security settings

## Troubleshooting

### Common Issues

1. **False Positives**: Legitimate queries being flagged as harmful
   - Solution: Ensure advanced security LLM analysis is enabled to reduce false positives

2. **Performance Impact**: Security analysis slowing down query processing
   - Solution: Optimize security LLM configuration or consider caching for repeated queries

3. **Configuration Errors**: Incorrect security settings
   - Solution: Verify all security-related environment variables are correctly set

4. **Model Unavailability**: Security LLM not responding
   - Solution: Check model configuration and connectivity, have fallback mechanisms in place

## Integration Points

The SQL validation and security analysis integrates with multiple components:

- **LangGraph Workflow**: Through `validate_sql` and `security_check_after_refinement` nodes
- **SQL Generator**: Receives validation feedback for query refinement
- **SQL Executor**: Only executes queries that pass validation
- **Database Manager**: Provides schema context for contextual analysis
- **Error Handler**: Processes validation errors appropriately