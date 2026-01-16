#!/usr/bin/env python3
"""
Database Utility Script

This script provides functionality to add and manage multiple databases
for the AI Agent application.
"""

import os
import sys
import argparse
from urllib.parse import urlparse

# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.utils.multi_database_manager import multi_db_manager, reload_database_config
from config.settings import ADDITIONAL_DATABASES


def validate_database_url(url):
    """
    Validate that a database URL is properly formatted.
    """
    try:
        result = urlparse(url)
        # For SQLite URLs, the scheme is 'sqlite' and path follows, not netloc
        if result.scheme == 'sqlite':
            return True
        # For other databases, check if scheme and netloc are present
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def add_database_interactive():
    """
    Interactive mode to add a new database.
    """
    print("=== Add New Database ===")

    name = input("Enter a name for the database: ").strip()
    if not name:
        print("Database name cannot be empty.")
        return False

    if not multi_db_manager._is_valid_database_name(name):
        print(f"Invalid database name: {name}. Only alphanumeric characters, underscores, and hyphens are allowed.")
        return False

    url = input("Enter the database URL: ").strip()
    if not url:
        print("Database URL cannot be empty.")
        return False

    if not validate_database_url(url):
        print(f"Invalid database URL: {url}")
        return False

    success = multi_db_manager.add_database(name, url)
    if success:
        print(f"Successfully added database: {name}")
        # Update environment variables to persist the change
        os.environ[f"DB_{name.upper()}_URL"] = url
        ADDITIONAL_DATABASES[name] = url
        # Reload the database configuration to ensure it's available
        reload_database_config()
    else:
        print(f"Failed to add database: {name}")

    return success


def add_database_command_line(name, url):
    """
    Add a database from command line arguments.
    """
    if not name:
        print("Database name cannot be empty.")
        return False

    if not multi_db_manager._is_valid_database_name(name):
        print(f"Invalid database name: {name}. Only alphanumeric characters, underscores, and hyphens are allowed.")
        return False

    if not url:
        print("Database URL cannot be empty.")
        return False

    if not validate_database_url(url):
        print(f"Invalid database URL: {url}")
        return False

    success = multi_db_manager.add_database(name, url)
    if success:
        print(f"Successfully added database: {name}")
        # Update environment variables to persist the change
        os.environ[f"DB_{name.upper()}_URL"] = url
        ADDITIONAL_DATABASES[name] = url
        # Reload the database configuration to ensure it's available
        reload_database_config()
    else:
        print(f"Failed to add database: {name}")

    return success


def list_databases():
    """
    List all configured databases.
    """
    databases = multi_db_manager.list_databases()
    if databases:
        print("Configured databases:")
        for db_name in databases:
            print(f"  - {db_name}")
    else:
        print("No databases configured.")


def test_connection(name):
    """
    Test the connection to a specific database.
    """
    if name not in multi_db_manager.list_databases():
        print(f"Database '{name}' not found.")
        return False
    
    success = multi_db_manager.test_connection(name)
    if success:
        print(f"Connection to '{name}' successful.")
    else:
        print(f"Connection to '{name}' failed.")
    
    return success


def remove_database(name):
    """
    Remove a database from the manager.
    """
    if name not in multi_db_manager.list_databases():
        print(f"Database '{name}' not found.")
        return False

    success = multi_db_manager.remove_database(name)
    if success:
        print(f"Successfully removed database: {name}")
        # Remove from environment variables
        db_url_key = f"DB_{name.upper()}_URL"
        if db_url_key in os.environ:
            del os.environ[db_url_key]
        if name in ADDITIONAL_DATABASES:
            del ADDITIONAL_DATABASES[name]
        # Reload the database configuration to ensure changes are applied
        reload_database_config()
    else:
        print(f"Failed to remove database: {name}")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Utility for managing multiple databases in the AI Agent application."
    )
    parser.add_argument(
        '--add', 
        nargs=2, 
        metavar=('NAME', 'URL'), 
        help='Add a new database with the given name and URL'
    )
    parser.add_argument(
        '--list', 
        action='store_true', 
        help='List all configured databases'
    )
    parser.add_argument(
        '--test', 
        type=str, 
        metavar='NAME', 
        help='Test connection to the specified database'
    )
    parser.add_argument(
        '--remove', 
        type=str, 
        metavar='NAME', 
        help='Remove the specified database'
    )
    parser.add_argument(
        '--interactive', 
        '-i', 
        action='store_true', 
        help='Run in interactive mode to add a new database'
    )

    args = parser.parse_args()

    # Show initial list of databases
    print("Current databases:")
    list_databases()
    print()

    if args.interactive:
        add_database_interactive()
    elif args.add:
        name, url = args.add
        add_database_command_line(name, url)
    elif args.list:
        list_databases()
    elif args.test:
        test_connection(args.test)
    elif args.remove:
        remove_database(args.remove)
    else:
        # If no arguments provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()