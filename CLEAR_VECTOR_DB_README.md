# Clear Vector Database

The `clear_vector_db.sh` script removes all documents from the vector database. This is useful when you want to reset the database or remove all indexed content.

## Usage

```bash
./clear_vector_db.sh
```

## What it does

1. Activates the virtual environment if present
2. Runs the underlying Python script (`clear_vector_db.py`) that handles the actual deletion
3. For ChromaDB, deletes the entire persistent directory to ensure all data is removed from disk
4. Reinitializes a fresh vector store
5. Provides feedback on the operation status

## Notes

- The script will exit with code 0 on success, non-zero on failure
- For ChromaDB, this completely removes all stored embeddings from both memory and disk
- Make sure your vector database service is running before executing this script