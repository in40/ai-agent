# Qdrant Database Cleanup Utility

This utility provides automated cleanup for Qdrant vector databases by removing all ingested documents.

## Files Included

- `qdrant_cleanup.py` - Main Python script for cleaning up Qdrant collections
- `qdrant_cleanup.sh` - Shell script wrapper for easier execution
- `qdrant_cleanup_cron.sh` - Optional script for cron job execution

## Prerequisites

- Python 3.7+
- Qdrant client library: `pip install qdrant-client`

## Installation

1. Install the required Python package:
   ```bash
   pip install qdrant-client
   ```

## Configuration

The script can be configured using environment variables:

- `QDRANT_HOST` - Qdrant host (default: localhost)
- `QDRANT_PORT` - Qdrant port (default: 6333)
- `QDRANT_API_KEY` - Qdrant API key (required if authentication is enabled)
- `QDRANT_HTTPS` - Use HTTPS (default: false)
- `QDRANT_PREFIX` - URL prefix if Qdrant is behind a proxy (optional)
- `QDRANT_URL` - Full Qdrant URL (alternative to host/port combination)
- `QDRANT_VERIFY_SSL` - Verify SSL certificates (default: true, set to false to disable verification)

## Usage

### Using the Shell Script (Recommended)

```bash
# Clean up by deleting entire collections (most efficient)
./qdrant_cleanup.sh

# Clean up by deleting all points within collections (preserves collection structure)
./qdrant_cleanup.sh --method points

# Dry run - show what would be deleted without actually deleting
./qdrant_cleanup.sh --dry-run

# Verbose output
./qdrant_cleanup.sh --verbose

# With custom Qdrant settings
QDRANT_HOST=my-qdrant-host QDRANT_PORT=6334 ./qdrant_cleanup.sh
```

### Using the Python Script Directly

```bash
# Clean up by deleting entire collections
python3 qdrant_cleanup.py

# Clean up by deleting all points within collections
python3 qdrant_cleanup.py --method points

# Dry run
python3 qdrant_cleanup.py --dry-run

# Verbose output
python3 qdrant_cleanup.py --verbose
```

## Scheduling Automatic Cleanup

### Using Cron

To schedule automatic cleanup using cron, add an entry to your crontab:

```bash
# Edit crontab
crontab -e

# Add a line to run cleanup daily at 2 AM
0 2 * * * cd /path/to/script && QDRANT_HOST=localhost QDRANT_PORT=6333 /usr/bin/python3 qdrant_cleanup.py --method collections >> /var/log/qdrant-cleanup.log 2>&1
```

### Using Systemd Timer (Linux)

1. Create a service file `/etc/systemd/system/qdrant-cleanup.service`:
   ```ini
   [Unit]
   Description=Qdrant Database Cleanup
   After=network.target

   [Service]
   Type=oneshot
   ExecStart=/usr/bin/python3 /path/to/qdrant_cleanup.py --method collections
   Environment=QDRANT_HOST=localhost
   Environment=QDRANT_PORT=6333
   ```

2. Create a timer file `/etc/systemd/system/qdrant-cleanup.timer`:
   ```ini
   [Unit]
   Description=Run Qdrant Cleanup Daily
   Requires=qdrant-cleanup.service

   [Timer]
   OnCalendar=daily
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. Enable and start the timer:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable qdrant-cleanup.timer
   sudo systemctl start qdrant-cleanup.timer
   ```

## Methods

The script supports two cleanup methods:

1. **Collections (default)**: Deletes entire collections, which removes all documents and the collection structure. This is the most efficient method.

2. **Points**: Deletes all points within each collection while preserving the collection structure. This method is useful if you want to keep the schema but remove all data.

## Safety Features

- **Dry Run Mode**: Use `--dry-run` to see what would be deleted without actually performing deletions
- **Logging**: Comprehensive logging to track cleanup operations
- **Error Handling**: Graceful handling of connection and operation errors
- **Environment Configuration**: Secure configuration via environment variables

## Authentication

If your Qdrant instance requires authentication, you must provide an API key:

```bash
# Using environment variable
export QDRANT_API_KEY="your-api-key-here"
./qdrant_cleanup.sh

# Or inline
QDRANT_API_KEY="your-api-key-here" ./qdrant_cleanup.sh

# For cloud instances
QDRANT_URL="https://your-cluster-id.eu-central.aws.cloud.qdrant.io:6333" \
QDRANT_API_KEY="your-api-key-here" \
./qdrant_cleanup.sh

# For local instances with API key but HTTP (not HTTPS)
QDRANT_API_KEY="your-api-key-here" QDRANT_HTTPS=false ./qdrant_cleanup.sh
```

### Important Note about API Keys and SSL/TLS

Some Qdrant deployments use API key authentication over HTTP rather than HTTPS. In these cases, you must explicitly set `QDRANT_HTTPS=false` to prevent SSL negotiation issues:

```bash
# If your Qdrant instance uses API key authentication over HTTP
QDRANT_API_KEY="your-api-key-here" QDRANT_HOST=localhost QDRANT_PORT=6333 QDRANT_HTTPS=false ./qdrant_cleanup.sh
```

This is necessary because the qdrant-client library may attempt to establish an SSL connection when an API key is provided, even if your server is configured for HTTP only.

## Troubleshooting

If you encounter issues:

1. Verify Qdrant is accessible at the configured host/port
2. Check that the API key is correct if authentication is enabled
3. Review the logs for specific error messages
4. Try using the dry-run mode first to verify the operation
5. If getting 401 Unauthorized errors, ensure QDRANT_API_KEY is set correctly