CREATE TABLE IF NOT EXISTS users (
    user_id NUMERIC PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    login TEXT UNIQUE,
    password TEXT,
    department TEXT
);

CREATE TABLE IF NOT EXISTS computers (
    computer_id NUMERIC PRIMARY KEY,
    ip_address TEXT,
    hostname TEXT,
    port NUMERIC
);

CREATE TABLE IF NOT EXISTS connections (
    id SERIAL PRIMARY KEY,
    user_id NUMERIC REFERENCES users(user_id),
    computer_id NUMERIC REFERENCES computers(computer_id),
    public_ip TEXT,
    connect_time TIMESTAMP
);