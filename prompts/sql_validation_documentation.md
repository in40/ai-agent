# SQL Validation and Security Checks Documentation

## Overview

The system implements a comprehensive two-tier security validation system to ensure SQL queries are safe before execution. This includes both basic keyword matching and advanced LLM-based security analysis to protect against SQL injection and other harmful commands.

## Two-Tier Validation System

The system employs a dual-layer approach to SQL validation:

### 1. Basic Keyword Matching
- Checks for potentially harmful SQL commands
- Validates against dangerous patterns that might indicate SQL injection
- Ensures queries start with SELECT or WITH for safety
- Checks for multiple statements and comment sequences

### 2. LLM-Based Security Analysis
- Uses a specialized security LLM to analyze queries for potential vulnerabilities
- Provides more nuanced analysis than basic keyword matching
- Considers context and schema information in the analysis
- Falls back to basic validation if the LLM fails

## Validation Process Flow

### Initial Validation Node
The `validate_sql_node` performs the first round of validation:

```python
def validate_sql_node(state: AgentState) -> AgentState:
    sql = state["sql_query"]
    disable_blocking = state.get("disable_sql_blocking", False)
    schema_dump = state.get("schema_dump", {})

    # If SQL blocking is disabled, skip all validations and return success
    if disable_blocking:
        return {
            **state,
            "validation_error": None
        }

    # Basic validation: Check if query is empty
    if not sql or sql.strip() == "":
        error_msg = "SQL query is empty"
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
        }

    # Use the security LLM for advanced analysis if enabled
    use_security_llm = str_to_bool(os.getenv("USE_SECURITY_LLM", "true"))
    if use_security_llm:
        try:
            security_detector = SecuritySQLDetector()
            is_safe, reason = security_detector.is_query_safe(sql, schema_dump)

            if not is_safe:
                error_msg = f"Security LLM detected potential security issue: {reason}"
                return {
                    **state,
                    "validation_error": error_msg,
                    "retry_count": state.get("retry_count", 0) + 1
                }
            else:
                # If security LLM says it's safe, skip basic validation
                return {
                    **state,
                    "validation_error": None
                }
        except Exception as e:
            logger.warning(f"Security LLM failed: {str(e)}, falling back to basic validation")
            # If security LLM fails, fall back to basic validation
            pass

    # Fallback to enhanced basic keyword matching if security LLM is disabled or failed
    # ... (detailed basic validation follows)
```

### Post-Refinement Validation
After SQL refinement, the system performs additional security checks:

```python
def security_check_after_refinement_node(state: AgentState) -> AgentState:
    sql = state["sql_query"]
    disable_blocking = state.get("disable_sql_blocking", False)
    schema_dump = state.get("schema_dump", {})

    # If SQL blocking is disabled, skip security check and return success
    if disable_blocking:
        return {
            **state,
            "validation_error": None
        }

    # Use the security LLM for advanced analysis if enabled
    use_security_llm = str_to_bool(os.getenv("USE_SECURITY_LLM", "true"))
    if use_security_llm:
        try:
            security_detector = SecuritySQLDetector()
            is_safe, reason = security_detector.is_query_safe(sql, schema_dump)

            if not is_safe:
                error_msg = f"Security LLM detected potential security issue after refinement: {reason}"
                return {
                    **state,
                    "validation_error": error_msg,
                    "retry_count": state.get("retry_count", 0) + 1
                }
            else:
                # If security LLM says it's safe, we can proceed
                return {
                    **state,
                    "validation_error": None
                }
        except Exception as e:
            logger.warning(f"Security LLM failed: {str(e)}, falling back to basic validation")
            # If security LLM fails, fall back to basic validation
            pass

    # Fallback to basic keyword matching if security LLM is disabled or failed
    # ... (detailed basic validation follows)
```

## Detailed Validation Checks

### Harmful Command Detection
The system checks for potentially harmful SQL commands:

```python
harmful_commands = ["drop", "delete", "insert", "update", "truncate", "alter", "exec", "execute", "merge", "replace"]

for command in harmful_commands:
    # Special handling for 'create' to avoid false positives with column names like 'created_at'
    if command == "create":
        import re
        if re.search(r'\bcreate\s+(table|database|index|view|procedure|function|trigger|role|user|schema)\b', sql_lower):
            error_msg = f"Potentially harmful SQL detected: {command}"
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1
            }
    elif command in sql_lower:
        error_msg = f"Potentially harmful SQL detected: {command}"
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
        }
```

### Dangerous Pattern Detection
The system identifies dangerous patterns that might indicate SQL injection:

```python
dangerous_patterns = [
    "union select",  # Could indicate SQL injection
    "information_schema",  # Could be used to extract schema info
    "pg_",  # PostgreSQL system tables/functions
    "sqlite_",  # SQLite system tables/functions
    "xp_",  # SQL Server extended procedures
    "sp_",  # SQL Server stored procedures
    "exec\\(",  # Execution functions
    "execute\\(",  # Execution functions
    "eval\\(",  # Evaluation functions
    "waitfor delay",  # Time-based attacks
    "benchmark\\(",  # Performance-based attacks
    "sleep\\(",  # Time-based attacks
    # ... many more patterns
]

for pattern in dangerous_patterns:
    import re
    if re.search(pattern, sql_lower, re.IGNORECASE):
        error_msg = f"Potentially dangerous SQL pattern detected: {pattern}"
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
        }
```

### Additional Security Checks
The system performs several additional security validations:

1. **Statement Count**: Checks for multiple statements (semicolon-separated) to prevent stacked queries
2. **Comment Detection**: Checks for comment sequences that might be used to bypass filters
3. **Hex Escape Sequences**: Ensures query doesn't contain hex escapes that might be used for injection
4. **Binary Literals**: Checks for binary literals that might be used for injection
5. **Dangerous Functions**: Identifies potentially dangerous function calls

```python
# Check for multiple statements (semicolon-separated)
if sql.count(';') > 1:
    error_msg = "Multiple SQL statements detected. Only single statements are allowed for safety."
    return {
        **state,
        "validation_error": error_msg,
        "retry_count": state.get("retry_count", 0) + 1
    }

# Check for comment sequences that might be used to bypass filters
if "/*" in sql or "--" in sql or "#" in sql:
    error_msg = "SQL comments detected. These are not allowed for safety."
    return {
        **state,
        "validation_error": error_msg,
        "retry_count": state.get("retry_count", 0) + 1
    }

# Additional check: Ensure query doesn't contain hex escapes that might be used for injection
import re
if re.search(r"'\\x[0-9a-fA-F]{2}", sql_lower) or re.search(r"'0x[0-9a-fA-F]+", sql_lower):
    error_msg = "Hexadecimal escape sequences detected. These are not allowed for safety."
    return {
        **state,
        "validation_error": error_msg,
        "retry_count": state.get("retry_count", 0) + 1
    }

# Additional check: Ensure query doesn't contain binary literals that might be used for injection
if re.search(r"b'[01]+'", sql_lower):
    error_msg = "Binary literals detected. These are not allowed for safety."
    return {
        **state,
        "validation_error": error_msg,
        "retry_count": state.get("retry_count", 0) + 1
    }
```

## Security LLM Analysis

The system uses a specialized security LLM to perform advanced analysis:

```python
def is_query_safe(self, sql_query: str, schema_context: dict) -> tuple[bool, str]:
    """
    Analyze the SQL query for security issues using the security LLM
    Returns a tuple of (is_safe, reason)
    """
    # Format the schema context for the LLM
    schema_str = json.dumps(schema_context, indent=2)
    
    # Format the prompt with the SQL query and schema context
    prompt = self.security_analysis_template.format(
        sql_query=sql_query,
        schema_context=schema_str
    )
    
    # Call the LLM to analyze the query
    response = self.llm.invoke(prompt)
    
    # Parse the response to extract the safety assessment
    try:
        # The LLM responds with a JSON object
        result = json.loads(response.content)
        
        is_safe = result.get("is_safe", False)
        security_issues = result.get("security_issues", [])
        confidence_level = result.get("confidence_level", "unknown")
        explanation = result.get("explanation", "")
        
        # If there are security issues, return the first one as the reason
        reason = security_issues[0] if security_issues else explanation
        
        return is_safe, reason
    except json.JSONDecodeError:
        # If we can't parse the response, assume the query is unsafe
        return False, "Could not parse security analysis response"
    except Exception as e:
        # If there's an error analyzing the response, assume the query is unsafe
        return False, f"Error analyzing query: {str(e)}"
```

## Configuration Options

The security validation can be configured through environment variables:

- `USE_SECURITY_LLM`: Controls whether to use the advanced LLM-based analysis (default: "true")
- `TERMINATE_ON_POTENTIALLY_HARMFUL_SQL`: Controls whether to block harmful SQL (default: True)

## Conditional Routing Based on Validation

The system uses conditional logic to route queries based on validation results:

```python
def should_validate_sql(state: AgentState) -> Literal["safe", "unsafe"]:
    if state.get("validation_error"):
        return "unsafe"
    return "safe"

def should_validate_after_security_check(state: AgentState) -> Literal["refine", "respond"]:
    has_validation_error = state.get("validation_error")

    if has_validation_error and state.get("retry_count", 0) < 10:
        return "refine"  # Go to validation after security failure
    return "respond"  # Proceed to response if security check passed
```

## Security Validation in the Workflow

The security validation is integrated at multiple points in the workflow:

1. **Initial Validation**: After SQL generation, before execution
2. **Post-Refinement Validation**: After SQL refinement, before execution
3. **Conditional Routing**: Based on validation results, the system routes to refinement or execution

## Benefits of the Security System

1. **Dual-Layer Protection**: Combines basic keyword matching with advanced LLM analysis
2. **Context-Aware**: Considers schema information in security analysis
3. **Configurable**: Can be adjusted based on security requirements
4. **Robust Fallback**: Falls back to basic validation if LLM fails
5. **Detailed Reporting**: Provides specific reasons for security issues
6. **Continuous Improvement**: Learns from previous validation results