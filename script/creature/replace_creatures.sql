-- Step 1: カラム追加
ALTER TABLE creatures
  ADD COLUMN IF NOT EXISTS scientific_name TEXT,
  ADD COLUMN IF NOT EXISTS distribution TEXT,
  ADD COLUMN IF NOT EXISTS habitat TEXT,
  ADD COLUMN IF NOT EXISTS size TEXT,
  ADD COLUMN IF NOT EXISTS depth_range TEXT,
  ADD COLUMN IF NOT EXISTS description TEXT;

-- Step 2: category の NOT NULL 制約を除去
ALTER TABLE creatures ALTER COLUMN category DROP NOT NULL;

-- Step 3: 一時テーブル作成（CSV構造に合わせる）
CREATE TEMP TABLE creatures_import (
    csv_id INT,
    name TEXT,
    scientific_name TEXT,
    distribution TEXT,
    habitat TEXT,
    size TEXT,
    depth_range TEXT,
    description TEXT
);

-- Step 4: CSVを一時テーブルに読み込み
\COPY creatures_import (csv_id, name, scientific_name, distribution, habitat, size, depth_range, description) FROM '/Users/toru.nakamichi/Desktop/diving_API/data/processed/creature/master_data.csv' WITH (FORMAT CSV, HEADER true);

-- Step 5: 既存データを全削除してIDシーケンスリセット
TRUNCATE TABLE creatures RESTART IDENTITY;

-- Step 6: 一時テーブルから本テーブルへ挿入（csv_id → original_id にマップ）
INSERT INTO creatures (name, scientific_name, distribution, habitat, size, depth_range, description, original_id)
SELECT name, scientific_name, distribution, habitat, size, depth_range, description, csv_id
FROM creatures_import;

-- 確認
SELECT COUNT(*) AS total FROM creatures;
SELECT id, name, scientific_name, distribution FROM creatures LIMIT 5;
