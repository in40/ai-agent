import re
from utils.multi_database_manager import multi_db_manager
from config.settings import TERMINATE_ON_POTENTIALLY_HARMFUL_SQL, ENABLE_SCREEN_LOGGING, DISABLE_DATABASES
import logging

logger = logging.getLogger(__name__)

class SQLExecutor:
    def __init__(self, database_manager=None):
        # Use the global multi-database manager if none provided
        self.db_manager = database_manager or multi_db_manager
        # Store the disable databases setting
        self.disable_databases = DISABLE_DATABASES

    def execute_sql_and_get_results(self, sql_query, db_name=None, table_to_db_mapping=None):
        """
        Execute the SQL query and return the results
        If db_name is "all_databases" or None, execute on all databases and aggregate results
        """
        # If databases are disabled, return empty results
        if self.disable_databases:
            logger.info("Databases are disabled, returning empty results for SQL execution")
            return []

        # If db_name is None, use the primary database name from the database manager
        if db_name is None:
            # Get the first available database as the primary database
            all_databases = self.db_manager.list_databases()
            if all_databases:
                db_name = all_databases[0]  # Use the first database as default
            else:
                raise ValueError("No databases available for execution")

        # First, try to extract just the SQL query from the response if it contains extra text
        # This handles cases where the LLM response includes more than just the SQL query
        import re
        import json

        # Look for JSON objects that might contain sql_query
        json_pattern = r'"sql_query"\s*:\s*"((?:[^"\\]|\\.)*")'
        json_match = re.search(json_pattern, str(sql_query))
        if json_match:
            # Extract the SQL query from the JSON
            try:
                # Find the full JSON object containing the sql_query
                full_json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\"sql_query\"[^{}]*\})', str(sql_query), re.DOTALL)
                if full_json_match:
                    json_str = full_json_match.group(1)
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        sql_query = parsed_json['sql_query']
            except (json.JSONDecodeError, KeyError):
                # If JSON parsing fails, continue with the original approach
                pass

        # Also try to extract SQL between ```sql and ``` markers
        markdown_match = re.search(r'```(?:sql)?\n(.*?)\n```', str(sql_query), re.DOTALL)
        if markdown_match:
            sql_query = markdown_match.group(1).strip()

        # Remove any content between ###ponder### tags and ###/ponder### tags
        sql_query = re.sub(r'###ponder###.*?###/ponder###', '', str(sql_query), flags=re.DOTALL)

        # Also remove any content between <thinking> tags and </thinking> tags
        sql_query = re.sub(r'<thinking>.*?</thinking>', '', sql_query, flags=re.DOTALL)

        # Strip any leading/trailing whitespace
        sql_query = sql_query.strip()

        try:
            # Check for potentially harmful commands
            is_safe, issues = self.check_for_harmful_commands(sql_query)

            if not is_safe:
                warning_msg = f"Potential security issue detected in SQL query: {', '.join(issues)}"
                if ENABLE_SCREEN_LOGGING:
                    logger.warning(warning_msg)
                print(f"WARNING: {warning_msg}")

                # Only terminate if the configuration parameter is enabled
                if TERMINATE_ON_POTENTIALLY_HARMFUL_SQL:
                    raise ValueError(f"SQL query blocked due to security concerns: {', '.join(issues)}")

            # Sanitize the SQL query to remove database prefixes that cause cross-database reference errors
            sanitized_query = self._sanitize_sql_query(sql_query)

            # If db_name is "all_databases", execute on all databases and aggregate results
            if db_name == "all_databases":
                return self._execute_on_appropriate_databases(sanitized_query, table_to_db_mapping)

            # Validate table existence before execution (only for single database queries)
            if db_name != "all_databases":
                if not self._validate_table_existence(sanitized_query, db_name, table_to_db_mapping):
                    raise ValueError(f"One or more tables in the query do not exist in the database '{db_name}'")

            # Execute the sanitized query on the specified database
            results = self.db_manager.execute_query(db_name, sanitized_query)

            return results

        except Exception as e:
            # Check if this is a cross-database query error
            error_str = str(e).lower()
            if "relation" in error_str and "does not exist" in error_str:
                # This might be a cross-database query issue
                # Check if the query involves multiple databases
                table_names = self._extract_table_names(sql_query)
                all_databases = self.db_manager.list_databases()

                # Check if tables are from different databases
                tables_by_db = {}
                for table_name in table_names:
                    clean_table_name = table_name.strip('"\'')

                    # Check which database contains this table
                    for db_name_check in all_databases:
                        try:
                            schema = self.db_manager.get_schema_dump(db_name_check)
                            if any(clean_table_name.lower() == schema_table_name.lower() for schema_table_name in schema.keys()):
                                if db_name_check not in tables_by_db:
                                    tables_by_db[db_name_check] = []
                                tables_by_db[db_name_check].append(clean_table_name)
                                break
                        except Exception:
                            continue  # Skip if we can't get schema for this database

                # If tables are from multiple databases, this confirms it's a cross-database issue
                if len(tables_by_db) > 1:
                    logger.info(f"Detected cross-database query issue. Attempting to execute on all databases.")
                    # Try executing on all databases instead
                    return self._execute_on_appropriate_databases(sanitized_query, table_to_db_mapping)

            if ENABLE_SCREEN_LOGGING:
                logger.error(f"Error executing SQL query: {str(e)}")

            # Re-raise the exception to be caught by the calling function
            raise

    def _validate_table_existence(self, sql_query, db_name, table_to_db_mapping=None):
        """
        Validate that all tables referenced in the SQL query exist in the specified database
        and that all columns referenced in the query exist in the corresponding tables
        """
        # If databases are disabled, skip validation and return True
        if self.disable_databases:
            logger.info("Databases are disabled, skipping table existence validation")
            return True

        import re
        import json

        # First, try to extract just the SQL query from the response if it contains extra text
        # This handles cases where the LLM response includes more than just the SQL query
        # Look for JSON objects that might contain sql_query
        json_pattern = r'"sql_query"\s*:\s*"((?:[^"\\]|\\.)*")'
        json_match = re.search(json_pattern, str(sql_query))
        if json_match:
            # Extract the SQL query from the JSON
            try:
                # Find the full JSON object containing the sql_query
                full_json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\"sql_query\"[^{}]*\})', str(sql_query), re.DOTALL)
                if full_json_match:
                    json_str = full_json_match.group(1)
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        sql_query = parsed_json['sql_query']
            except (json.JSONDecodeError, KeyError):
                # If JSON parsing fails, continue with the original approach
                pass

        # Also try to extract SQL between ```sql and ``` markers
        markdown_match = re.search(r'```(?:sql)?\n(.*?)\n```', str(sql_query), re.DOTALL)
        if markdown_match:
            sql_query = markdown_match.group(1).strip()

        # Remove any content between ###ponder### tags and ###/ponder### tags
        sql_query = re.sub(r'###ponder###.*?###/ponder###', '', str(sql_query), flags=re.DOTALL)

        # Also remove any content between <thinking> tags and </thinking> tags
        sql_query = re.sub(r'<thinking>.*?</thinking>', '', sql_query, flags=re.DOTALL)

        # Strip any leading/trailing whitespace
        sql_query = sql_query.strip()

        try:
            # Extract table names from the SQL query
            table_names = self._extract_table_names(sql_query)

            # If we have a table-to-database mapping, only validate tables that should be in this database
            if table_to_db_mapping:
                # Filter table names to only those that should exist in the current database
                tables_for_this_db = []
                for table_name in table_names:
                    # Remove quotes if present
                    clean_table_name = table_name.strip('"\'')

                    # Check if this table is mapped to the current database
                    if (clean_table_name in table_to_db_mapping and
                        table_to_db_mapping[clean_table_name].lower() == db_name.lower()):
                        tables_for_this_db.append(table_name)
            else:
                # If no mapping provided, validate all tables in this database
                tables_for_this_db = table_names

            # Get the schema for this database to check if the tables exist
            schema = self.db_manager.get_schema_dump(db_name)

            # Check if all relevant table names exist in the schema (case-insensitive comparison)
            for table_name in tables_for_this_db:
                # Remove any schema or database prefixes from the table name
                # e.g., "default"."contacts" -> "contacts", or public.contacts -> contacts
                clean_table_name = table_name
                if '.' in clean_table_name:
                    # Take only the last part (the actual table name)
                    clean_table_name = clean_table_name.split('.')[-1]

                # Remove quotes if present
                clean_table_name = clean_table_name.strip('"\'')

                # Check if the table exists in the schema (case-insensitive)
                table_exists = False
                table_schema = None
                actual_table_name = None  # Store the actual table name from the schema
                for schema_table_name in schema.keys():
                    if schema_table_name.lower() == clean_table_name.lower():
                        table_exists = True
                        table_schema = schema[schema_table_name]
                        actual_table_name = schema_table_name  # Store the actual table name
                        break

                if not table_exists:
                    logger.warning(f"Table '{clean_table_name}' does not exist in database '{db_name}' (original reference: '{table_name}')")
                    return False

                # Now validate that columns referenced for this table actually exist
                if table_schema:
                    # Extract column references for this table from the SQL query
                    # Look for patterns like "table_alias.column_name" or "table_name.column_name"
                    import re
                    # Find all column references for this table or its aliases
                    # This regex looks for the table name followed by a dot and a column name
                    # It handles both quoted and unquoted identifiers
                    table_aliases = self._extract_table_aliases(sql_query)

                    # Debug logging
                    logger.debug(f"Table aliases for '{clean_table_name}': {table_aliases.get(clean_table_name, [])}")

                    # Check for column references using the table name directly
                    # Case-insensitive matching for the table name
                    column_pattern = rf'{re.escape(clean_table_name)}\.([a-zA-Z_][a-zA-Z0-9_]*)'
                    direct_column_matches = re.findall(column_pattern, sql_query, re.IGNORECASE)

                    # Also check for quoted table names
                    quoted_column_pattern = rf'["\']?{re.escape(clean_table_name)}["\']?\.(["\']?[a-zA-Z_][a-zA-Z0-9_]*["\']?)'
                    quoted_direct_matches = re.findall(quoted_column_pattern, sql_query, re.IGNORECASE)
                    # Remove quotes from matched column names
                    quoted_direct_matches = [col.strip('"\'') for col in quoted_direct_matches]

                    # Combine direct matches
                    direct_column_matches.extend(quoted_direct_matches)

                    # Debug logging
                    logger.debug(f"Direct column matches for '{clean_table_name}': {direct_column_matches}")

                    # Check for column references using table aliases
                    alias_columns = []
                    for alias in table_aliases.get(actual_table_name.lower(), []):
                        # Unquoted alias
                        alias_pattern = rf'{alias}\.([a-zA-Z_][a-zA-Z0-9_]*)'
                        alias_matches = re.findall(alias_pattern, sql_query, re.IGNORECASE)

                        # Quoted alias
                        quoted_alias_pattern = rf'["\']?{alias}["\']?\.(["\']?[a-zA-Z_][a-zA-Z0-9_]*["\']?)'
                        quoted_alias_matches = re.findall(quoted_alias_pattern, sql_query, re.IGNORECASE)
                        # Remove quotes from matched column names
                        quoted_alias_matches = [col.strip('"\'') for col in quoted_alias_matches]

                        alias_columns.extend(alias_matches)
                        alias_columns.extend(quoted_alias_matches)

                        # Debug logging
                        logger.debug(f"Alias '{alias}' column matches: {alias_matches + quoted_alias_matches}")

                    # For columns in the SELECT clause that might refer to this table,
                    # we need to check if they exist in this table (but this is tricky without knowing aliases)
                    # For now, we'll focus on qualified column names (table.column or alias.column)

                    # Combine all column references
                    all_columns = direct_column_matches + alias_columns

                    # Debug logging
                    logger.debug(f"All columns to check for '{clean_table_name}': {all_columns}")

                    # Get actual column names from the schema
                    if isinstance(table_schema, list):
                        # Old format - backward compatibility
                        actual_columns = [col['name'] if isinstance(col, dict) else col['name'] for col in table_schema]
                    else:
                        # New format with comments
                        actual_columns = [col['name'] for col in table_schema.get('columns', [])]

                    # Debug logging
                    logger.debug(f"Actual columns in '{clean_table_name}': {[col for col in actual_columns]}")

                    # Check if all referenced columns exist in the table
                    for col_name in all_columns:
                        if col_name and col_name.lower() not in [ac.lower() for ac in actual_columns]:
                            logger.warning(f"Column '{col_name}' does not exist in table '{clean_table_name}' in database '{db_name}'")
                            return False

            return True
        except Exception as e:
            logger.error(f"Error validating table and column existence: {str(e)}")
            # If we can't validate, we'll let the query proceed and let the database handle the error
            return True

    def _extract_table_aliases(self, sql_query):
        """
        Extract table aliases from the SQL query
        Returns a dictionary mapping original table names to their aliases
        """
        import re

        # Dictionary to store table name to aliases mapping
        table_aliases = {}

        # Pattern to match table names and their aliases in FROM and JOIN clauses
        # Handles both quoted and unquoted identifiers
        # FROM table_name [AS] alias
        from_alias_pattern = r'FROM\s+(?:["\']?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)["\']?\.["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?|["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?)\s+(?:AS\s+)?(["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?)(?=\s|WHERE|GROUP|ORDER|HAVING|LIMIT|ON|USING|\(|\)|,)'

        # JOIN table_name [AS] alias
        join_alias_pattern = r'JOIN\s+(?:["\']?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)["\']?\.["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?|["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?)\s+(?:AS\s+)?(["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?)(?=\s|ON|WHERE|GROUP|ORDER|HAVING|LIMIT|USING|\(|\)|,)'

        # Process FROM clauses
        from_matches = re.findall(from_alias_pattern, sql_query, re.IGNORECASE)
        for match in from_matches:
            # Handle both three-part names (db.schema.table) and simple names (table)
            if match[1]:  # Three-part name: db.schema.table alias
                table_name = match[1]  # Get the actual table name
                alias = match[4] if match[4] else None
            elif match[2]:  # Simple name: table alias
                table_name = match[2]
                alias = match[4] if match[4] else None
            else:
                continue

            if alias:
                table_name_lower = table_name.lower()
                if table_name_lower not in table_aliases:
                    table_aliases[table_name_lower] = []
                if alias not in table_aliases[table_name_lower]:
                    table_aliases[table_name_lower].append(alias)

        # Process JOIN clauses
        join_matches = re.findall(join_alias_pattern, sql_query, re.IGNORECASE)
        for match in join_matches:
            # Handle both three-part names (db.schema.table) and simple names (table)
            if match[1]:  # Three-part name: db.schema.table alias
                table_name = match[1]  # Get the actual table name
                alias = match[4] if match[4] else None
            elif match[2]:  # Simple name: table alias
                table_name = match[2]
                alias = match[4] if match[4] else None
            else:
                continue

            if alias:
                table_name_lower = table_name.lower()
                if table_name_lower not in table_aliases:
                    table_aliases[table_name_lower] = []
                if alias not in table_aliases[table_name_lower]:
                    table_aliases[table_name_lower].append(alias)

        # Also look for simple table alias patterns like "table_name alias" without explicit AS
        simple_alias_pattern = r'(?:FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN)\s+(?:["\']?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)["\']?\.["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?|["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?=\s|WHERE|GROUP|ORDER|HAVING|LIMIT|ON|USING|\(|\)|,)'
        simple_matches = re.findall(simple_alias_pattern, sql_query, re.IGNORECASE)

        for match in simple_matches:
            # Handle both three-part names (db.schema.table) and simple names (table)
            if match[1]:  # Three-part name: db.schema.table alias
                table_name = match[1]  # Get the actual table name
                alias = match[3] if match[3] else None
            elif match[2]:  # Simple name: table alias
                table_name = match[2]
                alias = match[3] if match[3] else None
            else:
                continue

            if alias:
                table_name_lower = table_name.lower()
                if table_name_lower not in table_aliases:
                    table_aliases[table_name_lower] = []
                if alias not in table_aliases[table_name_lower]:
                    table_aliases[table_name_lower].append(alias)

        return table_aliases

    def _sanitize_sql_query(self, sql_query):
        """
        Sanitize the SQL query to remove database prefixes that cause cross-database reference errors
        For example: "SELECT * FROM contacts_db.public.contacts c" becomes "SELECT * FROM public.contacts c"
        Also handles quoted identifiers like "default"."public"."contacts" -> "public"."contacts"
        But preserves schema.table format and other uses of dots in the query (like column references)

        The goal is to remove the database name prefix while keeping the schema.table format intact.
        """
        import re

        # First, try to extract just the SQL query from the response if it contains extra text
        # This handles cases where the LLM response includes more than just the SQL query
        # Look for JSON objects that might contain sql_query
        json_pattern = r'"sql_query"\s*:\s*"((?:[^"\\]|\\.)*")'
        json_match = re.search(json_pattern, sql_query)
        if json_match:
            # Extract the SQL query from the JSON
            import json
            try:
                # Find the full JSON object containing the sql_query
                full_json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\"sql_query\"[^{}]*\})', sql_query, re.DOTALL)
                if full_json_match:
                    json_str = full_json_match.group(1)
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        sql_query = parsed_json['sql_query']
            except (json.JSONDecodeError, KeyError):
                # If JSON parsing fails, continue with the original approach
                pass

        # Also try to extract SQL between ```sql and ``` markers
        markdown_match = re.search(r'```(?:sql)?\n(.*?)\n```', sql_query, re.DOTALL)
        if markdown_match:
            sql_query = markdown_match.group(1).strip()

        # Remove any content between ###ponder### tags and ###/ponder### tags
        sql_query = re.sub(r'###ponder###.*?###/ponder###', '', sql_query, flags=re.DOTALL)

        # Also remove any content between <thinking> tags and </thinking> tags
        sql_query = re.sub(r'<thinking>.*?</thinking>', '', sql_query, flags=re.DOTALL)

        # First, fix escaped single quotes that are causing PostgreSQL syntax errors
        # Replace \' with ' (converting escaped quotes to proper SQL string literals)
        # This handles cases where the LLM generates backslash-escaped quotes
        sql_query = re.sub(r"\\'", "'", sql_query)

        # Also handle other common escape sequences
        sql_query = sql_query.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')

        # Remove extra backslashes that might be used for escaping
        # This handles cases where the LLM might have added extra escaping
        sql_query = re.sub('\\\\\\\\', '\\\\', sql_query)

        # Remove any potential comment indicators that could be used maliciously
        # This is a basic protection against comment-based SQL injection
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        sql_query = re.sub(r'--.*', '', sql_query)

        # Remove any potential command terminators that could allow multiple statements
        # This is important for preventing stacked query attacks
        sql_query = sql_query.strip(';')

        # Prevent certain dangerous SQL patterns
        dangerous_patterns = [
            r'\b(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE|EXEC|EXECUTE|MERGE)\b',
            r'\b(GRANT|REVOKE)\b',
            r'\b(CALL|LOAD|SOURCE)\b'
        ]

        # Check for potentially dangerous patterns but allow SELECT, WITH, etc.
        sql_upper = sql_query.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                # Only raise an error if it's not part of an allowed pattern
                # For example, we allow SELECT but not DELETE
                if not re.match(r'^\s*(SELECT|WITH|SHOW|DESCRIBE|EXPLAIN)\b', sql_upper):
                    # This is a more restrictive check - we'll log but not necessarily block
                    # as some legitimate queries might contain these keywords in strings
                    logger.warning(f"Potentially dangerous SQL pattern detected: {re.search(pattern, sql_upper).group()}")

        # Additional sanitization to remove any remaining leading/trailing whitespace
        sql_query = sql_query.strip()

        # The key insight is that we need to differentiate between:
        # 1. Three-part names: database.schema.table (remove database, keep schema.table)
        # 2. Two-part names that are actually schema.table (keep as is)
        # 3. Two-part names that are database.table (remove database, keep table)

        # Pattern to match three-part names in SQL contexts: KEYWORD database.schema.table [alias]
        # Example: FROM "mydb"."public"."users" u -> FROM "public"."users" u
        pattern_context_three_part = r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+(["\'][^"\'.]+\.[^"\'.]+["\']\.)(["\'][^"\'.]+["\']\.)(["\'][^"\'.]+["\'])(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?\b'

        def replace_context_three_part(match):
            keyword = match.group(1)
            database_part = match.group(2)  # The database part with quotes (e.g., "mydb".)
            schema_part = match.group(3)  # The schema part with quotes (e.g., "public".)
            table_name = match.group(4)  # The table name with quotes (e.g., "users")
            alias = match.group(5)  # The alias if it exists

            # Remove the database part, keep schema.table
            if alias:
                return f"{keyword} {schema_part}{table_name} {alias}"
            else:
                return f"{keyword} {schema_part}{table_name}"

        # Apply the transformation for three-part names (database.schema.table)
        sanitized_query = re.sub(pattern_context_three_part, replace_context_three_part, sql_query, flags=re.IGNORECASE)

        # Pattern to match three-part names without aliases in SQL contexts
        pattern_context_three_part_no_alias = r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+(["\'][^"\'.]+\.[^"\'.]+["\']\.)(["\'][^"\'.]+["\']\.)(["\'][^"\'.]+["\'])(?=\s|$|WHERE|GROUP|ORDER|HAVING|LIMIT|ON|USING|\(|\)|,)'

        def replace_context_three_part_no_alias(match):
            keyword = match.group(1)
            database_part = match.group(2)  # The database part with quotes
            schema_part = match.group(3)  # The schema part with quotes
            table_name = match.group(4)  # The table name with quotes

            # Remove the database part, keep schema.table
            return f"{keyword} {schema_part}{table_name}"

        # Apply the transformation for three-part names (database.schema.table) without aliases
        sanitized_query = re.sub(pattern_context_three_part_no_alias, replace_context_three_part_no_alias, sanitized_query, flags=re.IGNORECASE)

        # Pattern to match unquoted three-part names in SQL contexts: KEYWORD database.schema.table [alias]
        # Example: FROM mydb.public.users u -> FROM public.users u
        pattern_context_unquoted_three_part = r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+([a-zA-Z_][a-zA-Z0-9_]*\.)((?:[a-zA-Z_][a-zA-Z0-9_]*\.)[a-zA-Z_][a-zA-Z0-9_]*)\b(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?'

        def replace_context_unquoted_three_part(match):
            keyword = match.group(1)
            database_prefix = match.group(2)  # The database prefix (e.g., "mydb".)
            schema_and_table = match.group(3)  # The "schema.table" part
            alias = match.group(4)  # The alias if it exists

            # Remove the database prefix, keep schema.table
            if alias:
                return f"{keyword} {schema_and_table} {alias}"
            else:
                return f"{keyword} {schema_and_table}"

        # Apply the transformation for unquoted three-part names
        sanitized_query = re.sub(pattern_context_unquoted_three_part, replace_context_unquoted_three_part, sanitized_query, flags=re.IGNORECASE)

        # Pattern to match unquoted three-part names without aliases in SQL contexts
        pattern_context_unquoted_three_part_no_alias = r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+([a-zA-Z_][a-zA-Z0-9_]*\.)((?:[a-zA-Z_][a-zA-Z0-9_]*\.)[a-zA-Z_][a-zA-Z0-9_]*)\b(?=\s|$|WHERE|GROUP|ORDER|HAVING|LIMIT|ON|USING|\(|\)|,)'

        def replace_context_unquoted_three_part_no_alias(match):
            keyword = match.group(1)
            database_prefix = match.group(2)  # The database prefix
            schema_and_table = match.group(3)  # The "schema.table" part

            # Remove the database prefix, keep schema.table
            return f"{keyword} {schema_and_table}"

        # Apply the transformation for unquoted three-part names without aliases
        sanitized_query = re.sub(pattern_context_unquoted_three_part_no_alias, replace_context_unquoted_three_part_no_alias, sanitized_query, flags=re.IGNORECASE)

        # For two-part names, we need to determine if it's database.table or schema.table
        # Since we can't always know for sure, we'll use a heuristic based on common schema names
        pattern_context_two_part = r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+(["\'][^"\'.]+["\']\.)(["\'][^"\'.]+["\'])(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?\b'

        def replace_context_two_part(match):
            keyword = match.group(1)
            first_part = match.group(2)  # The first part with quotes and dot (e.g., "mydb". or "public".)
            table_name = match.group(3)  # The table name with quotes (e.g., "users")
            alias = match.group(4)  # The alias if it exists

            # Check if the first part is a known schema name
            first_part_clean = first_part.strip('."\'')

            # Common PostgreSQL schema names - if the first part matches one of these,
            # treat as schema.table and keep both parts
            known_schemas = {'public', 'analytics', 'information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1',
                            'pg_toast_temp_1', 'pg_surgery', 'timescaledb_experimental', 'timescaledb_information',
                            'timescaledb_internal', '_timescaledb_cache', '_timescaledb_catalog', '_timescaledb_config',
                            'cron', 'timescaledb_toolkit', 'dbdev', 'vault'}

            if first_part_clean.lower() in known_schemas:
                # This is likely schema.table, keep both parts
                result = f"{keyword} {first_part}{table_name}"
            else:
                # This is likely database.table, remove the database part
                result = f"{keyword} {table_name}"

            if alias:
                result += f" {alias}"

            return result

        # Apply the transformation for two-part names (database.table or schema.table)
        sanitized_query = re.sub(pattern_context_two_part, replace_context_two_part, sanitized_query, flags=re.IGNORECASE)

        # Pattern to match two-part names without aliases in SQL contexts
        pattern_context_two_part_no_alias = r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+(["\'][^"\'.]+["\']\.)(["\'][^"\'.]+["\'])(?=\s|$|WHERE|GROUP|ORDER|HAVING|LIMIT|ON|USING|\(|\)|,)'

        def replace_context_two_part_no_alias(match):
            keyword = match.group(1)
            first_part = match.group(2)  # The first part with quotes and dot
            table_name = match.group(3)  # The table name with quotes

            # Check if the first part is a known schema name
            first_part_clean = first_part.strip('."\'')
            known_schemas = {'public', 'analytics', 'information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1',
                            'pg_toast_temp_1', 'pg_surgery', 'timescaledb_experimental', 'timescaledb_information',
                            'timescaledb_internal', '_timescaledb_cache', '_timescaledb_catalog', '_timescaledb_config',
                            'cron', 'timescaledb_toolkit', 'dbdev', 'vault'}

            if first_part_clean.lower() in known_schemas:
                # This is likely schema.table, keep both parts
                return f"{keyword} {first_part}{table_name}"
            else:
                # This is likely database.table, remove the database part
                return f"{keyword} {table_name}"

        # Apply the transformation for two-part names (database.table or schema.table) without aliases
        sanitized_query = re.sub(pattern_context_two_part_no_alias, replace_context_two_part_no_alias, sanitized_query, flags=re.IGNORECASE)

        # For unquoted identifiers, we need to be careful about the order of operations
        # The issue in the test was that unquoted three-part names like mydb.public.users
        # were being processed incorrectly by the two-part patterns
        # We should process three-part names first, then two-part names

        # The three-part unquoted patterns were already handled above, so now we handle
        # the remaining two-part names appropriately

        # For unquoted two-part names, use negative lookahead to avoid known schemas
        # This will only replace patterns that don't start with known schema names
        # IMPORTANT: This should only match actual two-part names, not the first part of three-part names
        sanitized_query = re.sub(
            r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+((?!public\.|analytics\.|information_schema\.|pg_catalog\.|pg_toast\.|pg_temp_1\.|pg_toast_temp_1\.|pg_surgery\.|timescaledb_experimental\.|timescaledb_information\.|timescaledb_internal\.|_timescaledb_cache\.|_timescaledb_catalog\.|_timescaledb_config\.|cron\.|timescaledb_toolkit\.|dbdev\.|vault\.)[a-zA-Z_][a-zA-Z0-9_]*\.)([a-zA-Z_][a-zA-Z0-9_]*)\b(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?',
            lambda m: f"{m.group(1)} {m.group(3)}" + (f" {m.group(4)}" if m.group(4) else ""),
            sanitized_query,
            flags=re.IGNORECASE
        )

        # Handle unquoted two-part names without aliases
        sanitized_query = re.sub(
            r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+((?!public\.|analytics\.|information_schema\.|pg_catalog\.|pg_toast\.|pg_temp_1\.|pg_toast_temp_1\.|pg_surgery\.|timescaledb_experimental\.|timescaledb_information\.|timescaledb_internal\.|_timescaledb_cache\.|_timescaledb_catalog\.|_timescaledb_config\.|cron\.|timescaledb_toolkit\.|dbdev\.|vault\.)[a-zA-Z_][a-zA-Z0-9_]*\.)([a-zA-Z_][a-zA-Z0-9_]*)\b(?=\s|$|WHERE|GROUP|ORDER|HAVING|LIMIT|ON|USING|\(|\)|,)',
            lambda m: f"{m.group(1)} {m.group(3)}",
            sanitized_query,
            flags=re.IGNORECASE
        )

        logger.info(f"Sanitized SQL query: {sanitized_query}")

        return sanitized_query

    def _execute_on_appropriate_databases(self, sql_query, table_to_db_mapping=None):
        """
        Execute the SQL query on databases that contain the referenced tables and aggregate results.
        For queries involving tables from multiple databases, this method will attempt to execute
        the query on each database that contains at least one of the referenced tables.
        NOTE: True cross-database joins are not supported by most SQL databases, so complex queries
        involving joins across databases will likely fail at execution time. This is expected behavior.
        """
        # If databases are disabled, return empty results
        if self.disable_databases:
            logger.info("Databases are disabled, returning empty results for cross-database execution")
            return []
        import re
        import json

        # First, try to extract just the SQL query from the response if it contains extra text
        # This handles cases where the LLM response includes more than just the SQL query
        # Look for JSON objects that might contain sql_query
        json_pattern = r'"sql_query"\s*:\s*"((?:[^"\\]|\\.)*")'
        json_match = re.search(json_pattern, str(sql_query))
        if json_match:
            # Extract the SQL query from the JSON
            try:
                # Find the full JSON object containing the sql_query
                full_json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\"sql_query\"[^{}]*\})', str(sql_query), re.DOTALL)
                if full_json_match:
                    json_str = full_json_match.group(1)
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        sql_query = parsed_json['sql_query']
            except (json.JSONDecodeError, KeyError):
                # If JSON parsing fails, continue with the original approach
                pass

        # Also try to extract SQL between ```sql and ``` markers
        markdown_match = re.search(r'```(?:sql)?\n(.*?)\n```', str(sql_query), re.DOTALL)
        if markdown_match:
            sql_query = markdown_match.group(1).strip()

        # Remove any content between ###ponder### tags and ###/ponder### tags
        sql_query = re.sub(r'###ponder###.*?###/ponder###', '', str(sql_query), flags=re.DOTALL)

        # Also remove any content between <thinking> tags and </thinking> tags
        sql_query = re.sub(r'<thinking>.*?</thinking>', '', sql_query, flags=re.DOTALL)

        # Strip any leading/trailing whitespace
        sql_query = sql_query.strip()

        # Extract table names from the SQL query
        original_table_names = self._extract_table_names(sql_query)

        all_databases = self.db_manager.list_databases()
        combined_results = []

        # Check if all tables exist across all databases (for cross-database queries)
        all_tables_exist = True
        tables_found_in_databases = {}

        for table_name in original_table_names:
            # Remove quotes from table name if present
            clean_table_name = table_name.strip('"\'')

            # Check if this table exists in any database
            table_found = False
            for db_name in all_databases:
                schema = self.db_manager.get_schema_dump(db_name)

                # Check if the table exists in the schema (case-insensitive)
                if any(clean_table_name.lower() == schema_table_name.lower() for schema_table_name in schema.keys()):
                    table_found = True
                    if db_name not in tables_found_in_databases:
                        tables_found_in_databases[db_name] = []
                    tables_found_in_databases[db_name].append(clean_table_name)
                    break  # Found in one database is sufficient for this table

            if not table_found:
                logger.warning(f"Table '{clean_table_name}' does not exist in any database")
                all_tables_exist = False

        # If not all tables exist in the database ecosystem, we can't execute the query
        if not all_tables_exist:
            raise ValueError(f"One or more tables in the query do not exist in any of the configured databases: {original_table_names}")

        # Check if this is a cross-database query (tables from multiple databases)
        databases_with_tables = list(tables_found_in_databases.keys())
        is_cross_database_query = len(databases_with_tables) > 1

        if is_cross_database_query:
            logger.info(f"Detected cross-database query involving tables from databases: {databases_with_tables}. "
                       f"This may fail at execution time if the query contains actual joins across databases, "
                       f"since most SQL databases don't support joins across different database connections.")

        # Execute the query on databases that contain at least one of the tables referenced in the query
        for db_name in all_databases:
            if db_name in tables_found_in_databases and tables_found_in_databases[db_name]:
                try:
                    # Sanitize the query to remove database prefixes before execution
                    sanitized_query = self._sanitize_sql_query(sql_query)

                    # Validate table and column existence before execution
                    if not self._validate_table_existence(sanitized_query, db_name, table_to_db_mapping):
                        raise ValueError(f"One or more tables or columns in the query do not exist in the database '{db_name}'")

                    # Execute the sanitized query on this database
                    results = self.db_manager.execute_query(db_name, sanitized_query)

                    # Add database identifier to each result row to distinguish sources
                    for result in results:
                        result["_source_database"] = db_name

                    # Combine results from all databases
                    combined_results.extend(results)

                    logger.info(f"Query executed on '{db_name}' database, got {len(results)} results")
                except Exception as e:
                    error_msg = f"SQL execution error on '{db_name}' database: {str(e)}"
                    logger.error(error_msg)
                    # Continue with other databases even if one fails

                    # For cross-database queries, it's expected that the query might fail on some databases
                    # if it contains joins referencing tables not present in that specific database
                    if is_cross_database_query:
                        logger.info(f"This error is expected for cross-database queries when the query "
                                   f"references tables not present in '{db_name}' database.")
                    else:
                        # For non-cross-database queries, this is a genuine error
                        raise
            else:
                logger.info(f"Skipping '{db_name}' database - none of the tables {original_table_names} exist in this database")

        return combined_results


    def _extract_table_names(self, sql_query):
        """
        Extract table names from a SQL query
        This is a simplified implementation that handles basic SELECT statements
        Updated to handle schema prefixes and quoted identifiers
        """
        import re
        import json

        # First, try to extract just the SQL query from the response if it contains extra text
        # This handles cases where the LLM response includes more than just the SQL query
        # Look for JSON objects that might contain sql_query
        json_pattern = r'"sql_query"\s*:\s*"((?:[^"\\]|\\.)*")'
        json_match = re.search(json_pattern, str(sql_query))
        if json_match:
            # Extract the SQL query from the JSON
            try:
                # Find the full JSON object containing the sql_query
                full_json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\"sql_query\"[^{}]*\})', str(sql_query), re.DOTALL)
                if full_json_match:
                    json_str = full_json_match.group(1)
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        sql_query = parsed_json['sql_query']
            except (json.JSONDecodeError, KeyError):
                # If JSON parsing fails, continue with the original approach
                pass

        # Also try to extract SQL between ```sql and ``` markers
        markdown_match = re.search(r'```(?:sql)?\n(.*?)\n```', str(sql_query), re.DOTALL)
        if markdown_match:
            sql_query = markdown_match.group(1).strip()

        # Remove any content between ###ponder### tags and ###/ponder### tags
        sql_query = re.sub(r'###ponder###.*?###/ponder###', '', str(sql_query), flags=re.DOTALL)

        # Also remove any content between <thinking> tags and </thinking> tags
        sql_query = re.sub(r'<thinking>.*?</thinking>', '', sql_query, flags=re.DOTALL)

        # Strip any leading/trailing whitespace
        sql_query = sql_query.strip()

        # Convert to uppercase for easier parsing
        query_upper = sql_query.upper()

        # Find table names in FROM clause
        # Updated to handle schema prefixes and quoted identifiers like "default"."contacts"
        from_pattern = r'FROM\s+((?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?(?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?["\']?([A-Z_][A-Z0-9_]*)["\']?)(?:\s+|$|WHERE|GROUP|ORDER|HAVING|LIMIT|ON|USING)'
        from_matches = re.findall(from_pattern, query_upper)

        # Find table names in JOIN clauses
        join_pattern = r'(?:JOIN|INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN)\s+((?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?(?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?["\']?([A-Z_][A-Z0-9_]*)["\']?)(?:\s+|$|ON|USING)'
        join_matches = re.findall(join_pattern, query_upper)

        # Find table names in other contexts (like INSERT INTO, UPDATE, etc.)
        insert_pattern = r'INSERT\s+INTO\s+((?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?(?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?["\']?([A-Z_][A-Z0-9_]*)["\']?)(?:\s+|$|VALUES|\()'
        insert_matches = re.findall(insert_pattern, query_upper)

        update_pattern = r'UPDATE\s+((?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?(?:["\']?[A-Z_][A-Z0-9_]*["\']?\.)?["\']?([A-Z_][A-Z0-9_]*)["\']?)(?:\s+|$|SET)'
        update_matches = re.findall(update_pattern, query_upper)

        # Extract the actual table name (second group from each match tuple)
        all_matches = [match[1] for match in from_matches] + [match[1] for match in join_matches] + \
                      [match[1] for match in insert_matches] + [match[1] for match in update_matches]

        table_names = []

        for match in all_matches:
            # Remove quotes if present
            cleaned = match.strip('"\'')
            table_names.append(cleaned)

        # Remove duplicates while preserving order
        unique_table_names = []
        for name in table_names:
            if name not in unique_table_names:
                unique_table_names.append(name)

        return unique_table_names

    def check_for_harmful_commands(self, query):
        """
        Check the SQL query for potentially harmful commands
        Returns (is_safe: bool, issues: list)
        """
        import re

        # First, try to extract just the SQL query from the response if it contains extra text
        # This handles cases where the LLM response includes more than just the SQL query
        # Look for JSON objects that might contain sql_query
        json_pattern = r'"sql_query"\s*:\s*"((?:[^"\\]|\\.)*")'
        json_match = re.search(json_pattern, query)
        if json_match:
            # Extract the SQL query from the JSON
            import json
            try:
                # Find the full JSON object containing the sql_query
                full_json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\"sql_query\"[^{}]*\})', query, re.DOTALL)
                if full_json_match:
                    json_str = full_json_match.group(1)
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        query = parsed_json['sql_query']
            except (json.JSONDecodeError, KeyError):
                # If JSON parsing fails, continue with the original approach
                pass

        # Also try to extract SQL between ```sql and ``` markers
        markdown_match = re.search(r'```(?:sql)?\n(.*?)\n```', query, re.DOTALL)
        if markdown_match:
            query = markdown_match.group(1).strip()

        # Remove any content between ###ponder### tags and ###/ponder### tags
        query = re.sub(r'###ponder###.*?###/ponder###', '', query, flags=re.DOTALL)

        # Also remove any content between <thinking> tags and </thinking> tags
        query = re.sub(r'<thinking>.*?</thinking>', '', query, flags=re.DOTALL)

        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower().strip()

        issues = []

        # Check for potentially harmful commands
        harmful_commands = [
            'drop', 'delete', 'truncate', 'alter', 'create', 'insert',
            'update', 'grant', 'revoke', 'exec', 'execute', 'merge'
        ]

        # Check if the query starts with SELECT (for basic safety)
        if not query_lower.strip().startswith('select'):
            issues.append("Query does not start with SELECT")

        # Check for harmful commands anywhere in the query
        for command in harmful_commands:
            if command in query_lower:
                # Allow 'select' but not other harmful commands
                if command != 'select':
                    issues.append(f"Contains potentially harmful command: {command}")

        # Check for other potentially harmful patterns
        harmful_patterns = [
            'union select',  # Could indicate SQL injection
            'information_schema',  # Could be used to extract schema info
            'pg_',  # PostgreSQL system tables/functions
            'sqlite_',  # SQLite system tables/functions
            'xp_',  # SQL Server extended procedures
            'sp_',  # SQL Server stored procedures
        ]

        for pattern in harmful_patterns:
            if pattern in query_lower:
                issues.append(f"Contains potentially harmful pattern: {pattern}")

        return len(issues) == 0, issues