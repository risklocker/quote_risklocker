-- Migration: Create insurance_companies table
-- Description: Stores insurance company information and detection configuration
-- Requirements: 22.2, 22.3, 22.4, 22.5, 22.6

CREATE TABLE IF NOT EXISTS insurance_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL CHECK (category IN ('Motor', 'Property', 'Construction', 'Fire')),
    logo_path VARCHAR(500),
    detection_phrases JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for faster lookups by name
CREATE INDEX IF NOT EXISTS idx_insurance_companies_name ON insurance_companies(name);

-- Index for filtering by category
CREATE INDEX IF NOT EXISTS idx_insurance_companies_category ON insurance_companies(category);

-- Index for filtering active companies
CREATE INDEX IF NOT EXISTS idx_insurance_companies_status ON insurance_companies(status);

-- Add comments for documentation
COMMENT ON TABLE insurance_companies IS 'Insurance company configurations for detection and template association';
COMMENT ON COLUMN insurance_companies.detection_phrases IS 'Array of text phrases used to detect this company from PDF content';
COMMENT ON COLUMN insurance_companies.category IS 'Insurance category: Motor, Property, Construction, or Fire';
