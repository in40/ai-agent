# PostgreSQL Setup Guide for Authentication Service

This guide provides detailed instructions for setting up PostgreSQL as the database for the authentication service in the AI Agent system.

## Prerequisites

Before proceeding, ensure you have:
- PostgreSQL installed and running on your system
- Administrative access to create databases and users in PostgreSQL
- Basic knowledge of PostgreSQL administration

## Step-by-Step Setup

### 1. Install PostgreSQL (if not already installed)

On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

On CentOS/RHEL:
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
```

On macOS:
```bash
brew install postgresql
```

### 2. Start PostgreSQL Service

On most systems:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

On macOS:
```bash
brew services start postgresql
```

### 3. Create Database and User

Connect to PostgreSQL as the superuser:
```bash
sudo -u postgres psql
```

Execute the following SQL commands:
```sql
-- Create a dedicated user for the AI Agent application
CREATE USER ai_agent_user WITH PASSWORD 'secure_password';

-- Create the database
CREATE DATABASE ai_agent_db OWNER ai_agent_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ai_agent_db TO ai_agent_user;

-- Exit PostgreSQL
\q
```

### 4. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit the `.env` file to configure your PostgreSQL connection:
```bash
# Database Configuration
DB_TYPE=postgresql
DB_USERNAME=ai_agent_user
DB_PASSWORD=secure_password
DB_HOSTNAME=localhost
DB_PORT=5432
DB_NAME=ai_agent_db
DATABASE_URL=postgresql://ai_agent_user:secure_password@localhost:5432/ai_agent_db
```

### 5. Verify Database Connection

You can test the connection using the psql command:
```bash
psql -h localhost -U ai_agent_user -d ai_agent_db
```

### 6. Application Startup

When you start the authentication service, it will automatically:
1. Connect to the PostgreSQL database using the provided credentials
2. Create the `users` table if it doesn't exist
3. Begin managing user authentication and authorization

The `users` table schema is:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Security Best Practices

1. **Strong Passwords**: Use strong, unique passwords for database users
2. **Connection Encryption**: Consider using SSL connections in production
3. **Network Security**: Limit database access to trusted networks
4. **Regular Updates**: Keep PostgreSQL updated with security patches
5. **Principle of Least Privilege**: Grant minimal required permissions to the database user

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Verify PostgreSQL is running
   - Check that the hostname and port are correct
   - Ensure the firewall allows connections on port 5432

2. **Authentication Failed**:
   - Verify username and password are correct
   - Check that the user exists in PostgreSQL
   - Ensure the user has access to the specified database

3. **Permission Denied**:
   - Verify the database user has appropriate privileges
   - Check that the user owns the database or has been granted access

### Testing Database Connectivity

Use the following command to test your database connection:
```bash
python -c "import psycopg2; conn = psycopg2.connect('postgresql://ai_agent_user:secure_password@localhost:5432/ai_agent_db'); print('Connection successful')"
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_TYPE` | Database type | postgresql |
| `DB_USERNAME` | Database username | (required) |
| `DB_PASSWORD` | Database password | (required) |
| `DB_HOSTNAME` | Database hostname | localhost |
| `DB_PORT` | Database port | 5432 |
| `DB_NAME` | Database name | (required) |
| `DATABASE_URL` | Full database connection string | (constructed from above values) |

## Migration from Other Databases

If migrating from SQLite or another database system:
1. Export your existing user data
2. Update your environment configuration to use PostgreSQL
3. Start the authentication service - it will create the necessary tables
4. Import your user data, ensuring passwords are properly hashed

## Backup and Recovery

Regularly backup your authentication database:
```bash
pg_dump -h localhost -U ai_agent_user -d ai_agent_db > backup.sql
```

To restore from backup:
```bash
psql -h localhost -U ai_agent_user -d ai_agent_db < backup.sql
```