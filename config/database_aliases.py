"""
Module for managing database aliases and mapping them to real database names.
This allows the application to use aliases internally while ensuring that LLMs receive the real database names.
"""

import os
from typing import Dict, Optional
from config.settings import ADDITIONAL_DATABASES


class DatabaseAliasMapper:
    """
    Class to manage mapping between database aliases and real database names.

    The mapper allows the application to use convenient aliases internally while ensuring
    that when database names are passed to LLMs, they receive the real database names
    from the configuration.
    """

    def __init__(self):
        # Initialize the alias to real name mapping from environment variables
        self.alias_to_real_name: Dict[str, str] = {}
        self.real_name_to_alias: Dict[str, str] = {}

        # Populate mappings from environment variables
        self._load_mappings_from_env()

        # Populate mappings from additional databases configuration
        self._load_mappings_from_additional_databases()
    
    def _load_mappings_from_env(self):
        """
        Load database alias to real name mappings from environment variables.

        Environment variables should follow the format:
        - DB_ALIAS_{ALIAS_NAME}_REAL_NAME={real_database_name}
        - Example: DB_ALIAS_SALES_REAL_NAME=production_sales_db
        """
        for key, value in os.environ.items():
            if key.startswith("DB_ALIAS_") and key.endswith("_REAL_NAME"):
                # Extract the alias name from the environment variable name
                # Format: DB_ALIAS_{ALIAS_NAME}_REAL_NAME
                # Remove "DB_ALIAS_" prefix and "_REAL_NAME" suffix
                alias_part = key[len("DB_ALIAS_"):-len("_REAL_NAME")]  # This is safer than hardcoding indices
                alias_name = alias_part.lower()

                real_name = value

                if alias_name and real_name:
                    self.alias_to_real_name[alias_name] = real_name
                    self.real_name_to_alias[real_name] = alias_name

    def _load_mappings_from_additional_databases(self):
        """
        Load database alias to real name mappings from additional databases configuration.

        This method extracts the real database name from the database URL for each additional database.
        The alias is the key in ADDITIONAL_DATABASES, and the real name is extracted from the URL.
        """
        for alias, db_url in ADDITIONAL_DATABASES.items():
            # Extract the real database name from the URL
            # Format: protocol://username:password@hostname:port/real_db_name
            try:
                # Split the URL by '/' and get the last part which should be the database name
                real_db_name = db_url.split('/')[-1]

                # Remove any query parameters or fragments if present
                real_db_name = real_db_name.split('?')[0].split('#')[0]

                if alias and real_db_name:
                    self.alias_to_real_name[alias] = real_db_name
                    self.real_name_to_alias[real_db_name] = alias
            except Exception as e:
                # If parsing fails, skip this database
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not parse database URL for alias '{alias}': {e}")
    
    def add_mapping(self, alias: str, real_name: str):
        """
        Add a new alias to real name mapping.
        
        Args:
            alias: The alias name used internally by the application
            real_name: The real database name from the configuration
        """
        self.alias_to_real_name[alias.lower()] = real_name
        self.real_name_to_alias[real_name] = alias.lower()
    
    def get_real_name(self, alias: str) -> Optional[str]:
        """
        Get the real database name for a given alias.
        
        Args:
            alias: The alias name
            
        Returns:
            The real database name, or None if no mapping exists
        """
        return self.alias_to_real_name.get(alias.lower())
    
    def get_alias(self, real_name: str) -> Optional[str]:
        """
        Get the alias for a given real database name.
        
        Args:
            real_name: The real database name
            
        Returns:
            The alias name, or None if no mapping exists
        """
        return self.real_name_to_alias.get(real_name)
    
    def has_mapping(self, alias: str) -> bool:
        """
        Check if an alias has a corresponding real name mapping.
        
        Args:
            alias: The alias name
            
        Returns:
            True if a mapping exists, False otherwise
        """
        return alias.lower() in self.alias_to_real_name
    
    def get_all_aliases(self) -> list:
        """
        Get all registered aliases.
        
        Returns:
            List of all aliases
        """
        return list(self.alias_to_real_name.keys())
    
    def get_all_real_names(self) -> list:
        """
        Get all registered real database names.
        
        Returns:
            List of all real database names
        """
        return list(self.real_name_to_alias.keys())


# Global instance of the DatabaseAliasMapper
db_alias_mapper = DatabaseAliasMapper()


def get_db_alias_mapper() -> DatabaseAliasMapper:
    """
    Get the global instance of the DatabaseAliasMapper.
    
    Returns:
        DatabaseAliasMapper instance
    """
    return db_alias_mapper