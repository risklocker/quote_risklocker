-- Migration: Create users table
-- Description: Stores user accounts with authentication and role information
-- Requirements: 22.2, 22.3, 22.4, 22.5, 22.6

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('Staff', 'Manager', 'Admin')),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for faster email lookups during authentication
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Index for filtering active users
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- Index for role-based queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Add comment for documentation
COMMENT ON TABLE users IS 'User accounts with authentication credentials and role-based access control';
COMMENT ON COLUMN users.role IS 'User role: Staff (upload/edit own), Manager (view all), Admin (full access)';
COMMENT ON COLUMN users.status IS 'Account status: active users can login, inactive users are blocked';
