-- Migration: Add 'stops' column to search_requests table
-- This column stores the number of stops preference (0-3) as per SerpAPI documentation

ALTER TABLE search_requests 
ADD COLUMN IF NOT EXISTS stops INTEGER DEFAULT 0 CHECK (stops >= 0 AND stops <= 3);

-- Update existing records to have default value of 0 (Any number of stops)
UPDATE search_requests SET stops = 0 WHERE stops IS NULL;

