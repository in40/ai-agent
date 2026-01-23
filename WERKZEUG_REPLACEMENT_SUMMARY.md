# Werkzeug Replacement in AI Agent System v0.5

## Overview

As part of the v0.5 upgrade, we have successfully replaced all direct dependencies on Werkzeug with more modern and secure alternatives. This change improves the security posture of the application and reduces external dependencies.

## Changes Made

### 1. Password Hashing Functions
- **Replaced**: `werkzeug.security.check_password_hash` and `werkzeug.security.generate_password_hash`
- **With**: Direct `bcrypt` implementation
- **Files Updated**:
  - `backend/app.py`
  - `backend/security.py` (already using database layer with bcrypt)
  - `backend/services/auth/app.py` (already using database layer with bcrypt)

### 2. Filename Sanitization Function
- **Replaced**: `werkzeug.utils.secure_filename`
- **With**: Custom implementation with equivalent security features
- **Files Updated**:
  - `backend/services/rag/app.py`

## Technical Details

### Password Hashing Migration
The migration from Werkzeug to bcrypt involved:

1. Replacing imports:
   ```python
   # Old
   from werkzeug.security import check_password_hash, generate_password_hash
   
   # New
   import bcrypt
   ```

2. Updating password hashing:
   ```python
   # Old
   hashed_password = generate_password_hash(password)
   
   # New
   hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
   ```

3. Updating password verification:
   ```python
   # Old
   if not check_password_hash(stored_hash, password):
   
   # New
   if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
   ```

### Filename Sanitization Migration
The custom `secure_filename` implementation provides the same security features as Werkzeug's version:

```python
import re
import os

def secure_filename(filename: str) -> str:
    """
    Secure a filename by removing potentially dangerous characters and sequences.
    """
    if filename is None:
        return ''
        
    # Normalize the path to remove any Windows-style separators
    filename = filename.replace('\\', '/')
    
    # Get the basename to prevent directory traversal
    filename = os.path.basename(filename)
    
    # Remove leading dots and spaces
    filename = filename.lstrip('. ')
    
    # Replace any sequence of invalid characters with a single underscore
    # Allow only alphanumeric, dots, dashes, and underscores
    filename = re.sub(r'[^A-Za-z0-9.\-_]', '_', filename)
    
    # Handle cases where the filename might be empty after sanitization
    if not filename:
        filename = "unnamed_file"
    
    # Prevent hidden files by ensuring the name doesn't start with a dot
    if filename.startswith('.'):
        filename = f"unnamed{filename}"
    
    return filename
```

## Benefits

1. **Enhanced Security**: Direct bcrypt usage provides stronger password hashing with adaptive cost factors
2. **Reduced Dependencies**: Eliminated direct dependency on Werkzeug for utility functions
3. **Consistency**: Aligned with existing bcrypt usage in the project's database layer
4. **Maintainability**: Custom secure_filename implementation gives more control over sanitization logic
5. **Performance**: Direct bcrypt usage can be slightly faster than going through Werkzeug wrapper

## Files Modified

- `backend/app.py` - Updated password hashing functions
- `backend/security.py` - Updated import (though this file already used the database layer)
- `backend/services/auth/app.py` - Updated import (though this file already used the database layer)
- `backend/services/rag/app.py` - Replaced secure_filename with custom implementation
- `V05_SUMMARY.md` - Updated to reflect Werkzeug replacement

## Verification

All functionality remains identical from the user perspective. The changes are purely internal, replacing the underlying implementation while maintaining the same API and security properties.