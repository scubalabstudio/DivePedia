CREATE TABLE IF NOT EXISTS diving_points (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    url TEXT,
    prefecture VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_diving_points_prefecture ON diving_points(prefecture);
CREATE INDEX idx_diving_points_name ON diving_points(name);
