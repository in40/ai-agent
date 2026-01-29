#!/bin/bash
# Example cron job setup for Qdrant cleanup

# To set up automatic cleanup, you can add this line to your crontab (using 'crontab -e'):
# This example runs the cleanup every day at 2 AM

# 0 2 * * * cd /root/qwen/ai_agent && /usr/bin/python3 /root/qwen/ai_agent/qdrant_cleanup.py --method collections >> /var/log/qdrant_cleanup.log 2>&1

# Or using the shell wrapper:
# 0 2 * * * /root/qwen/ai_agent/qdrant_cleanup.sh >> /var/log/qdrant_cleanup.log 2>&1

# If your Qdrant instance is not on localhost, set the environment variables:
# 0 2 * * * cd /root/qwen/ai_agent && QDRANT_HOST=qdrant.example.com QDRANT_PORT=6333 /usr/bin/python3 /root/qwen/ai_agent/qdrant_cleanup.py --method collections >> /var/log/qdrant_cleanup.log 2>&1

echo "Example cron job entries for Qdrant cleanup:"
echo "# Run cleanup daily at 2 AM"
echo "0 2 * * * cd /root/qwen/ai_agent && /usr/bin/python3 /root/qwen/ai_agent/qdrant_cleanup.py --method collections >> /var/log/qdrant_cleanup.log 2>&1"
echo ""
echo "# Or using the shell wrapper"
echo "0 2 * * * /root/qwen/ai_agent/qdrant_cleanup.sh >> /var/log/qdrant_cleanup.log 2>&1"