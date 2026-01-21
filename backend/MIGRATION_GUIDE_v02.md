# Migration Guide: AI Agent v0.2 Security Enhancements

This document outlines the security enhancements introduced in version 0.2 and how to migrate your applications to use them.

## New Security Features

### 1. Role-Based Access Control (RBAC)
- Users now have roles (admin, user, guest, service_account)
- Each role has specific permissions
- API endpoints require appropriate permissions

### 2. Rate Limiting
- All API endpoints now have rate limiting
- Limits vary by endpoint (e.g., 30 requests/minute for agent queries)
- Implemented using Redis or in-memory fallback

### 3. Enhanced Input Validation
- All API endpoints validate input against schemas
- Automatic sanitization of potentially dangerous content
- Detailed error messages for validation failures

### 4. Audit Logging
- All user actions are logged
- Includes user ID, action, resource, IP address, and success/failure status
- Helpful for security monitoring and compliance

### 5. Session Management
- Improved session handling
- Sessions tied to IP address and user agent
- Automatic expiration

## Breaking Changes

### Authentication
- Previously, any valid JWT token could access most endpoints
- Now, endpoints require specific permissions
- Example: `/api/agent/query` now requires `write:agent` permission

### Rate Limits
- New rate limits are enforced on all endpoints
- Exceeding limits returns HTTP 429 (Too Many Requests)

### Input Validation
- Stricter validation on all inputs
- Previously accepted malformed requests may now fail

## Migration Steps

### 1. Update Your Client Applications

#### For API Consumers
```python
# OLD WAY (v0.1)
headers = {
    'Authorization': f'Bearer {token}'
}
response = requests.post('/api/agent/query', json=data, headers=headers)

# NEW WAY (v0.2)
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
response = requests.post('/api/agent/query', json=data, headers=headers)

# Check for rate limiting
if response.status_code == 429:
    print("Rate limit exceeded, retry after delay")
```

#### For Web Clients
- Update your JavaScript to handle new error codes
- Implement retry logic for rate-limited requests
- Update UI to reflect permission-based access

### 2. Update Permissions for Existing Users

The system creates users with default permissions. For existing users, you may need to assign appropriate roles:

```python
# In your user management system
from backend.security import UserRole

# Assign admin role to existing admin users
users_db['existing_admin']['role'] = UserRole.ADMIN
```

### 3. Handle New Error Types

Your applications should now handle:

- HTTP 403 (Forbidden) - Insufficient permissions
- HTTP 429 (Too Many Requests) - Rate limit exceeded
- Validation errors with detailed messages

## New API Endpoints

### Session Management
- `POST /auth/login` - Returns session ID in addition to token
- Session IDs are tied to IP and user agent for security

### Enhanced Service Information
- `GET /api/services` - Now includes required permissions for each endpoint

## Security Best Practices

### For Developers
1. Always validate that your application has the required permissions
2. Implement proper error handling for security-related responses
3. Use rate-limiting-aware retry logic
4. Monitor audit logs for suspicious activity

### For Administrators
1. Regularly review user roles and permissions
2. Monitor rate limiting to adjust limits appropriately
3. Review audit logs regularly
4. Ensure Redis is properly secured if used for rate limiting

## Troubleshooting

### Common Issues

**Issue**: Getting HTTP 403 errors after upgrade
**Solution**: Verify your user has the required permissions for the endpoint

**Issue**: Rate limit errors (HTTP 429)
**Solution**: Implement exponential backoff in your client, or contact admin to adjust limits

**Issue**: Validation errors on previously working requests
**Solution**: Check the error message for specific validation requirements

## Rollback Plan

If you need to rollback to v0.1 temporarily:

1. Switch to the `v0.1` branch/tag
2. Revert your client applications to the old authentication method
3. Note that this removes all the security enhancements

## Support

For questions about migrating to v0.2 security features, please contact the development team or refer to the updated API documentation.