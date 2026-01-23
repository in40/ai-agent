# Timeout Configuration for AI Agent System

## Overview

This document explains the timeout configurations implemented to handle long-running AI model responses in the AI Agent system.

## Configuration Changes

### 1. Nginx Configuration
- **File**: `backend/nginx_config.py` and `backend/nginx_tls_config.py`
- **Change**: Increased proxy timeouts from 60 seconds to 600 seconds (10 minutes)
- **Settings**:
  - `proxy_connect_timeout`: 600s
  - `proxy_send_timeout`: 600s
  - `proxy_read_timeout`: 600s

### 2. Gateway Service
- **File**: `backend/services/gateway/app.py`
- **Change**: Added timeout parameter to all requests with value of 600 seconds (10 minutes)
- **Endpoints affected**:
  - All proxy routes (auth, agent, rag services)
  - All convenience API routes
  - File upload endpoint (increased to 600s from 300s)

### 3. Frontend Web Client
- **File**: `backend/web_client/index.html`
- **Change**: Increased JavaScript timeouts from 5 minutes to 10 minutes
- **Endpoints affected**:
  - Agent query: 10 minutes
  - RAG ingestion: 10 minutes
  - RAG lookup: 10 minutes
  - RAG query: 10 minutes

### 4. React Editor
- **File**: `gui/react_editor/src/App.js`
- **Change**: Increased JavaScript timeout from 30 seconds to 600 seconds (10 minutes)

## Impact

These changes allow the system to handle long-running AI model responses without prematurely returning 504 Gateway Timeout errors. The 10-minute timeout should accommodate even the most complex AI processing tasks.

## Considerations

- Monitor system resources as longer-running requests may consume more memory
- Consider implementing streaming responses for very long operations in future versions
- The timeout values can be adjusted based on observed performance and requirements

## Rollback

If needed, the timeout values can be reduced by reverting the changes in the configuration files mentioned above.