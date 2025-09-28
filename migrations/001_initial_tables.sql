CREATE TABLE IF NOT EXISTS creatures (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    scientific_name VARCHAR(255),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    description TEXT,
    habitat VARCHAR(255),
    size VARCHAR(100),
    depth_range VARCHAR(100),
    rarity VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_creatures_name ON creatures(name);
CREATE INDEX idx_creatures_category ON creatures(category);