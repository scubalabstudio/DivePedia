-- 1. カメラマスターテーブル
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    model VARCHAR(200) NOT NULL UNIQUE,
    brand VARCHAR(100),                  -- NULL許可
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. ハウジングマスターテーブル
CREATE TABLE housings (
    id SERIAL PRIMARY KEY,
    model VARCHAR(200) NOT NULL UNIQUE,
    brand VARCHAR(100),                  -- NULL許可
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. レンズマスターテーブル
CREATE TABLE lenses (
    id SERIAL PRIMARY KEY,
    model VARCHAR(200) NOT NULL UNIQUE,
    brand VARCHAR(100),                  -- NULL許可
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. ギア（アクセサリー）マスターテーブル
CREATE TABLE gears (
    id SERIAL PRIMARY KEY,
    model VARCHAR(200) NOT NULL UNIQUE,
    brand VARCHAR(100),                  -- NULL許可
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. アダプターマスターテーブル
CREATE TABLE adapters (
    id SERIAL PRIMARY KEY,
    model VARCHAR(200) NOT NULL UNIQUE,
    brand VARCHAR(100),                  -- NULL許可
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. エクステンションマスターテーブル
CREATE TABLE extensions (
    id SERIAL PRIMARY KEY,
    model VARCHAR(200) NOT NULL UNIQUE,
    brand VARCHAR(100),                  -- NULL許可
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. ポートマスターテーブル
CREATE TABLE ports (
    id SERIAL PRIMARY KEY,
    model VARCHAR(200) NOT NULL UNIQUE,
    brand VARCHAR(100),                  -- NULL許可
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. システムチャート（組み合わせ）テーブル
CREATE TABLE system_charts (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    housing_id INTEGER REFERENCES housings(id),
    lens_id INTEGER REFERENCES lenses(id),
    gear_id INTEGER REFERENCES gears(id),
    adapter_id INTEGER REFERENCES adapters(id),
    extension1_id INTEGER REFERENCES extensions(id),
    extension2_id INTEGER REFERENCES extensions(id),
    extension3_id INTEGER REFERENCES extensions(id),
    port_id INTEGER REFERENCES ports(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(camera_id, housing_id, lens_id, port_id)
);

-- インデックス作成
CREATE INDEX idx_system_charts_camera ON system_charts(camera_id);
CREATE INDEX idx_system_charts_housing ON system_charts(housing_id);
CREATE INDEX idx_system_charts_lens ON system_charts(lens_id);

-- RLS無効化（開発中）
ALTER TABLE cameras DISABLE ROW LEVEL SECURITY;
ALTER TABLE housings DISABLE ROW LEVEL SECURITY;
ALTER TABLE lenses DISABLE ROW LEVEL SECURITY;
ALTER TABLE gears DISABLE ROW LEVEL SECURITY;
ALTER TABLE adapters DISABLE ROW LEVEL SECURITY;
ALTER TABLE extensions DISABLE ROW LEVEL SECURITY;
ALTER TABLE ports DISABLE ROW LEVEL SECURITY;
ALTER TABLE system_charts DISABLE ROW LEVEL SECURITY;
