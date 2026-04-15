CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    occupation TEXT NOT NULL,
    location TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    industry TEXT,
    primary_use_case TEXT NOT NULL,
    preferred_tone TEXT NOT NULL,
    goals TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    mode TEXT NOT NULL,
    use_case TEXT NOT NULL,
    task TEXT NOT NULL,
    optimized_prompt TEXT NOT NULL,
    response_text TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_generations_user_created
    ON generations(user_id, created_at DESC);
