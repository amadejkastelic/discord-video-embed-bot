-- Database
CREATE DATABASE embed_bot;

-- User
CREATE USER bot WITH ENCRYPTED PASSWORD 'bot';
GRANT ALL PRIVILEGES ON DATABASE embed_bot TO bot;

-- Django conf
ALTER ROLE bot SET client_encoding TO 'utf8';
ALTER ROLE bot SET default_transaction_isolation TO 'read committed';
ALTER ROLE bot SET timezone TO 'UTC';
