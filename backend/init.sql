-- Database initialization script for DocuMind AI
-- This script sets up the initial database configuration

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance (will be created by Alembic, but good to have as backup)
-- These are just examples - actual indexes are managed by Alembic migrations

-- Set timezone
SET timezone = 'UTC';

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'DocuMind AI database initialized successfully';
END $$; 