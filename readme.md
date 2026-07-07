# DivePedia — ダイビングマスターデータ管理リポジトリ

スキューバダイビングに関するマスターデータを管理し、Supabase Edge Functions を通じてアプリへ提供するバックエンドリポジトリです。

---

## 概要

| 項目 | 内容 |
|---|---|
| データベース | Supabase (PostgreSQL 17) |
| API | Supabase Edge Functions (Deno / TypeScript) |
| スクリプト | Python 3.9 + supabase-py |
| プロジェクトID | `diving_API` |

管理するデータは大きく **3 カテゴリ** に分かれます。

1. **海洋生物** — 生き物マスターデータ（学名・生息域・水深・説明）
2. **ダイビングポイント** — 国内外のダイビングスポット（都道府県・緯度経度）
3. **水中撮影機材** — カメラ・ハウジング・レンズなどの組み合わせ（システムチャート）

---

## ディレクトリ構成

```
DivePedia/
├── data/
│   ├── backup/               # 全テーブルの CSV バックアップ
│   └── processed/            # インポート用に整形したデータ
│       ├── creature/         # 生き物データ（カテゴリ別 CSV）
│       ├── camera/           # カメラマスター JSON
│       ├── point/            # ダイビングスポット JSON
│       ├── systemchart/      # カメラ別システムチャート JSON
│       ├── strobe/           # ストロボマスター JSON
│       ├── light/            # ライトマスター JSON
│       └── accessory/        # アクセサリマスター JSON
├── script/                   # データ整形・インポートスクリプト
│   ├── export_backup.py      # 全テーブルを CSV にエクスポート
│   ├── import_backup.py      # CSV バックアップから復元
│   ├── creature/             # 生き物データ用スクリプト
│   ├── camera/               # カメラデータ用スクリプト
│   ├── point/                # ポイントデータ用スクリプト
│   ├── systemchart/          # システムチャート用スクリプト
│   ├── strobe/               # ストロボ用スクリプト
│   ├── light/                # ライト用スクリプト
│   └── accessory/            # アクセサリ用スクリプト
├── supabase/
│   ├── config.toml           # Supabase ローカル開発設定
│   ├── migrations/           # DDL マイグレーションファイル
│   │   ├── 001_initial_tables.sql
│   │   ├── 002_add_diving_points.sql
│   │   ├── 003_add_camera_gear_tables.sql
│   │   ├── 004_add_light_strobe_accessory_tables.sql
│   │   ├── 005_insert_light_strobe_accessory_data.sql
│   │   ├── 006_add_latlon_to_diving_points.sql
│   │   └── migrate.py        # マイグレーション実行スクリプト
│   └── functions/            # Edge Functions (Deno)
│       ├── get-creatures/
│       ├── search-creatures/
│       ├── camera-option/
│       ├── system-chart/
│       └── nearest-point/
├── functions.md              # Edge Functions 詳細仕様書
├── requirements.txt          # Python 依存パッケージ
└── .env                      # 環境変数（git 管理外）
```

---

## データベーススキーマ

### creatures（海洋生物マスター）

| カラム | 型 | 説明 |
|---|---|---|
| id | SERIAL PK | |
| name | VARCHAR(255) | 和名 |
| scientific_name | VARCHAR(255) | 学名 |
| category | VARCHAR(100) | カテゴリ（魚類・甲殻類など） |
| subcategory | VARCHAR(100) | サブカテゴリ |
| description | TEXT | 解説文 |
| distribution | TEXT | 分布域 |
| habitat | VARCHAR(255) | 生息環境 |
| size | VARCHAR(100) | 体長目安 |
| depth_range | VARCHAR(100) | 主な水深 |
| rarity | VARCHAR(50) | レア度 |

### diving_points（ダイビングポイント）

| カラム | 型 | 説明 |
|---|---|---|
| id | SERIAL PK | |
| name | VARCHAR(255) | スポット名 |
| code | VARCHAR(50) UNIQUE | 識別コード |
| url | TEXT | 参考 URL |
| prefecture | VARCHAR(20) | 都道府県 |
| latitude | DOUBLE PRECISION | 緯度 |
| longitude | DOUBLE PRECISION | 経度 |

### 水中撮影機材テーブル群

| テーブル | 内容 |
|---|---|
| cameras | カメラマスター（model, brand） |
| housings | ハウジングマスター |
| lenses | レンズマスター |
| gears | ギア（ズームギアなど） |
| adapters | アダプターマスター |
| extensions | エクステンションマスター |
| ports | ポートマスター |
| system_charts | 上記を組み合わせたシステムチャート |

`system_charts` は `(camera_id, housing_id, lens_id, port_id)` の組み合わせがユニーク制約付きで、水中カメラシステムの有効な構成を1レコードとして管理します。

---

## PostgreSQL RPC 関数

### `nearest_diving_points`

現在地から指定半径（km）以内のダイビングポイントを距離順で返します。Haversine 公式を使用。

```sql
SELECT * FROM nearest_diving_points(
  user_lat     => 35.6895,
  user_lon     => 139.6917,
  radius_km    => 50,
  result_count => 10       -- NULL で全件
);
```

返却カラム: `id, name, prefecture, latitude, longitude, distance_km`

---

## Edge Functions

詳細な仕様は [`functions.md`](functions.md) を参照してください。

| 関数名 | メソッド | 概要 |
|---|---|---|
| `get-creatures` | GET | 名前の前方一致で生き物を検索（3文字以上必須） |
| `search-creatures` | GET | ページネーション付き生き物検索（空クエリで全件） |
| `camera-option` | GET | カメラ名からハウジング・レンズの組み合わせを取得 |
| `system-chart` | GET | カメラ/ハウジング/レンズ ID からシステムチャート1件を取得 |
| `nearest-point` | GET | 現在地（緯度経度）から近いダイビングスポットを検索 |

### 認証キー

| 関数 | 使用キー |
|---|---|
| `get-creatures` / `search-creatures` / `nearest-point` | `SUPABASE_SERVICE_ROLE_KEY` |
| `camera-option` / `system-chart` | `SUPABASE_ANON_KEY` |

---

## セットアップ

### 1. 環境変数の設定

`.env` ファイルをプロジェクトルートに作成し、以下を設定します（`.env` は git 管理外）。

```env
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_ANON_KEY=<anon-key>
```

### 2. Python 環境の構築

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. マイグレーションの実行

```bash
cd supabase/migrations
python3 migrate.py
```

または Supabase CLI を使用:

```bash
supabase db push
```

---

## スクリプト

### バックアップのエクスポート

```bash
# 全テーブルを data/backup/ に CSV 出力
python3 script/export_backup.py

# テーブルを指定して出力
python3 script/export_backup.py cameras housings
```

### バックアップからの復元

```bash
python3 script/import_backup.py
```

### データインポート（各カテゴリ）

```bash
# 生き物データ
python3 script/creature/import_to_supabase.py

# カメラデータ
python3 script/camera/import_cameras.py
```

---

## ローカル開発

Supabase CLI でローカル環境を起動できます。

```bash
supabase start       # ローカル DB + Studio + Edge Functions 起動
supabase stop        # 停止
supabase db reset    # DB リセット（マイグレーション再適用）
```

ローカル Studio: http://127.0.0.1:54323

---

## データ管理フロー

```
data/processed/          # 整形済みデータ（CSV / JSON）
      ↓ script/*/import_*.py
Supabase DB              # 正規化されたマスターテーブル
      ↓ script/export_backup.py
data/backup/             # 定期 CSV バックアップ
```

`data/processed/` 配下のファイルを更新 → インポートスクリプトを実行、という流れでマスターデータを更新します。
