-- Initialize PgVector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant permissions to the user
GRANT ALL ON SCHEMA public TO user;

-- Optional: Create a sample table to demonstrate vector capabilities
-- Uncomment the lines below if you want to test vector functionality
-- CREATE TABLE IF NOT EXISTS embeddings (
--     id SERIAL PRIMARY KEY,
--     content TEXT,
--     embedding vector(1536),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Grant permissions on the table
-- GRANT ALL PRIVILEGES ON TABLE embeddings TO user;
-- GRANT USAGE, SELECT ON SEQUENCE embeddings_id_seq TO user;