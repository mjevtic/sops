-- SupportOps Automator Database Initialization Script
-- This script sets up the initial database structure and security

-- Create database if it doesn't exist (handled by Docker)
-- CREATE DATABASE IF NOT EXISTS supportops;

-- Set timezone
SET timezone = 'UTC';

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE audit_severity AS ENUM ('info', 'warning', 'medium', 'high');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE integration_platform AS ENUM ('slack', 'trello', 'notion', 'google_sheets', 'zendesk', 'freshdesk', 'jira', 'github');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
-- These will be created by SQLModel/Alembic migrations

-- Set up row-level security (RLS) for enhanced security
-- This will be configured by the application

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO PUBLIC;
GRANT CREATE ON SCHEMA public TO PUBLIC;

-- Create application user if it doesn't exist
-- This is handled by Docker environment variables

-- Log initialization
INSERT INTO public.audit_logs (
    id,
    timestamp,
    user_id,
    username,
    action,
    resource_type,
    resource_id,
    details,
    ip_address,
    user_agent,
    status,
    severity,
    created_at
) VALUES (
    uuid_generate_v4(),
    CURRENT_TIMESTAMP,
    NULL,
    'system',
    'database_initialized',
    'system',
    NULL,
    'Database initialized successfully with security configurations',
    'localhost',
    'PostgreSQL Init Script',
    'success',
    'info',
    CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

-- Create indexes for performance (will be handled by migrations)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rules_is_active ON rules(is_active);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_integrations_platform ON integrations(platform);

COMMIT;

