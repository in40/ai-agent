#!/usr/bin/env python3
"""
Automated Qdrant Database Cleanup Script
Removes all ingested documents from Qdrant collections
"""

import os
import sys
import logging
import argparse
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse


def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_qdrant_client():
    """Initialize Qdrant client from environment variables or defaults"""
    host = os.getenv('QDRANT_HOST', 'localhost')
    port = int(os.getenv('QDRANT_PORT', 6333))
    api_key = os.getenv('QDRANT_API_KEY')
    https = os.getenv('QDRANT_HTTPS', '').lower() == 'true'
    prefix = os.getenv('QDRANT_PREFIX', '')
    url = os.getenv('QDRANT_URL')  # Allow full URL specification
    verify_ssl = os.getenv('QDRANT_VERIFY_SSL', 'true').lower() == 'true'  # SSL verification setting

    kwargs = {}

    # Handle API key separately to avoid forcing HTTPS
    if api_key and url:
        # If using a full URL, we can pass the API key separately
        kwargs['api_key'] = api_key
    elif api_key and not https:
        # For HTTP with API key, some versions of the client may need special handling
        # The qdrant_client library sometimes forces HTTPS when API key is provided
        # We'll try to initialize without forcing HTTPS
        from qdrant_client import QdrantClient as QC
        # Initialize with URL that specifies HTTP explicitly
        http_url = f"http://{host}:{port}"
        client = QC(url=http_url, api_key=api_key, https=False)
        return client
    elif api_key:
        # Standard case with API key and HTTPS
        kwargs['api_key'] = api_key

    if https:
        kwargs['https'] = True
    if prefix:
        kwargs['prefix'] = prefix

    # Only add verify if https is enabled
    if https and not verify_ssl:
        kwargs['verify'] = False  # Correct parameter name for SSL verification

    try:
        # If QDRANT_URL is provided, use it instead of host/port
        if url:
            return QdrantClient(url=url, **kwargs)
        else:
            return QdrantClient(host=host, port=port, **kwargs)
    except Exception as e:
        logging.error(f"Failed to connect to Qdrant at {host}:{port} - {str(e)}")
        raise


def delete_all_collections(client):
    """Delete all collections in the Qdrant instance"""
    try:
        collections = client.get_collections()
        logging.info(f"Found {len(collections.collections)} collections to delete")
        
        deleted_count = 0
        for collection in collections.collections:
            logging.info(f"Deleting collection: {collection.name}")
            client.delete_collection(collection.name)
            logging.info(f"Successfully deleted collection: {collection.name}")
            deleted_count += 1
            
        logging.info(f"All {deleted_count} collections have been deleted successfully")
        return True
    except Exception as e:
        logging.error(f"Error deleting collections: {str(e)}")
        return False


def delete_all_points_from_collection(client, collection_name):
    """Delete all points from a specific collection using empty filter"""
    try:
        logging.info(f"Deleting all points from collection: {collection.name}")
        
        # Delete all points using an empty filter (matches all points)
        result = client.delete(
            collection_name=collection.name,
            points_selector=models.FilterSelector(
                filter=models.Filter()  # Empty filter matches all points
            )
        )
        
        logging.info(f"Successfully deleted all points from collection: {collection.name}")
        return True
    except Exception as e:
        logging.error(f"Error deleting points from collection {collection.name}: {str(e)}")
        return False


def delete_all_documents(client, method='collections'):
    """
    Main function to delete all documents using specified method
    Methods:
    - 'collections': Delete entire collections (most efficient)
    - 'points': Delete all points from each collection
    """
    if method == 'collections':
        return delete_all_collections(client)
    elif method == 'points':
        try:
            collections = client.get_collections()
            logging.info(f"Found {len(collections.collections)} collections")
            
            success_count = 0
            for collection in collections.collections:
                if delete_all_points_from_collection(client, collection.name):
                    success_count += 1
                    
            logging.info(f"Successfully cleaned {success_count}/{len(collections.collections)} collections")
            return success_count == len(collections.collections)
        except Exception as e:
            logging.error(f"Error getting collections: {str(e)}")
            return False
    else:
        logging.error(f"Unknown method: {method}. Use 'collections' or 'points'")
        return False


def main():
    parser = argparse.ArgumentParser(description='Automate Qdrant database cleanup')
    parser.add_argument(
        '--method', 
        choices=['collections', 'points'], 
        default='collections',
        help="Method to use for cleanup: 'collections' (delete entire collections) or 'points' (delete all points)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logging.info(f"Starting Qdrant cleanup with method: {args.method}")
    
    if args.dry_run:
        logging.info("DRY RUN MODE: No actual deletion will occur")
        
        # Just show what would be deleted
        try:
            client = get_qdrant_client()
            collections = client.get_collections()
            logging.info(f"Would delete {len(collections.collections)} collections:")
            for collection in collections.collections:
                logging.info(f"  - {collection.name}")
        except Exception as e:
            logging.error(f"Could not connect to Qdrant: {str(e)}")
            return 1
        
        return 0
    
    try:
        client = get_qdrant_client()
        
        # Verify connection
        collections = client.get_collections()
        logging.info(f"Connected to Qdrant successfully. Found {len(collections.collections)} collections.")
        
        success = delete_all_documents(client, method=args.method)
        
        if success:
            logging.info("Qdrant cleanup completed successfully")
            return 0
        else:
            logging.error("Qdrant cleanup failed")
            return 1
            
    except Exception as e:
        logging.error(f"Failed to connect to Qdrant or perform cleanup: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())