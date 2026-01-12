# Database Alias to Real Name Mapping System

## Overview
This system enables the AI agent application to use convenient aliases internally while ensuring that LLMs receive the real database names from the configuration. This addresses the requirement that "when database name passed to llm models we need to use real database names from config file instead of alias used in app."

## Components

### 1. DatabaseAliasMapper (`config/database_aliases.py`)
- Manages mappings between database aliases and real database names
- Automatically loads mappings from additional databases defined in `config/settings.py`
- Supports manual mappings via environment variables
- Provides methods to get real names from aliases and vice versa

#### Automatic Loading from Additional Databases
The system automatically extracts real database names from the database URLs defined in `ADDITIONAL_DATABASES`. For example:
- If `ADDITIONAL_DATABASES` contains `{"analytics": "postgresql://user:pass@host:5432/analytics_prod_db"}`,
  the system automatically creates a mapping from alias "analytics" to real name "analytics_prod_db".

#### Manual Environment Variable Format
```
DB_ALIAS_{ALIAS_NAME}_REAL_NAME={real_database_name}
```

#### Example
```
DB_ALIAS_SALES_REAL_NAME=production_sales_db
DB_ALIAS_INVENTORY_REAL_NAME=production_inventory_db
```

### 2. Updated MultiDatabaseManager (`utils/multi_database_manager.py`)
- Modified `get_schema_dump` method to accept a `use_real_name` parameter
- Maps table names to both database aliases and real database names
- Updated `reload_database_config()` function to refresh alias mappings when database configurations change

### 3. Updated LangGraph Agent (`langgraph_agent.py`)
- Extended `AgentState` to include `table_to_real_db_mapping`
- Updated `get_schema_node` to populate both alias and real name mappings
- Modified SQL generation calls to pass both mappings to the SQL generator

### 4. Updated SQL Generator (`models/sql_generator.py`)
- Modified `generate_sql` method to accept `table_to_real_db_mapping`
- Updated `format_database_mapping` to use real names when available
- Ensures LLMs receive real database names instead of aliases

## Usage

### Setting Up Mappings
Mappings can be set up in two ways:

1. **Automatic from Additional Databases** (recommended for most cases):
   Define additional databases in environment variables as you normally would:
   ```bash
   export DB_ANALYTICS_TYPE=postgresql
   export DB_ANALYTICS_USERNAME=user
   export DB_ANALYTICS_PASSWORD=pass
   export DB_ANALYTICS_HOSTNAME=host
   export DB_ANALYTICS_PORT=5432
   export DB_ANALYTICS_NAME=analytics_prod_db

   # OR
   export DB_REPORTING_URL=postgresql://user:pass@host:5432/reporting_prod_db
   ```
   The system will automatically create mappings from "analytics" → "analytics_prod_db" and "reporting" → "reporting_prod_db".

2. **Manual Environment Variables** (for overriding automatic mappings):
   ```bash
   export DB_ALIAS_SALES_REAL_NAME=production_sales_db
   export DB_ALIAS_INVENTORY_REAL_NAME=production_inventory_db
   ```

3. **Programmatically**:
   ```python
   from config.database_aliases import get_db_alias_mapper

   mapper = get_db_alias_mapper()
   mapper.add_mapping("sales", "production_sales_db")
   mapper.add_mapping("inventory", "production_inventory_db")
   ```

### How It Works
1. During application startup, the system reads additional database configurations from environment variables
2. It automatically creates mappings between database aliases and real database names
3. During schema retrieval, both table-to-alias and table-to-real-name mappings are created
4. When generating SQL, the system passes both mappings to the LLM
5. The LLM receives real database names in its context, ensuring accurate SQL generation
6. The application continues to use aliases internally for convenience

## Benefits
- Maintains internal consistency with convenient aliases
- Ensures LLMs have access to accurate real database names
- Automatically handles additional databases defined in configuration
- Supports manual overrides for special cases
- Supports complex multi-database environments
- Provides flexibility in configuration
- Maintains backward compatibility

## Example Flow
1. Application defines additional database "analytics" pointing to "analytics_prod_db"
2. System automatically creates mapping: "analytics" → "analytics_prod_db"
3. Schema retrieval creates mappings for tables in "analytics" database
4. Both alias and real name mappings are passed to LLM
5. LLM generates SQL using real database name "analytics_prod_db"
6. Application executes query using internal alias "analytics" but connects to real database