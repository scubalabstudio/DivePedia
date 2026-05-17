# Supabase Edge Functions 一覧

## 概要

本プロジェクトのSupabase Edge Functionsは `/supabase/functions/` 以下に配置されています。

---

## 1. `get-creatures`

**パス:** `supabase/functions/get-creatures/index.ts`

### 概要
生き物データを名前の前方一致で検索します。**3文字以上**の入力が必要です。

### リクエスト

```
GET /functions/v1/get-creatures?q={検索ワード}&category={カテゴリー}
```

| パラメーター | 必須 | 型 | 説明 |
|---|---|---|---|
| `q` | 必須 | string | 検索ワード（3文字以上） |
| `category` | 任意 | string | カテゴリーでフィルター |

### レスポンス

```json
{
  "query": "クマノミ",
  "searchPrefix": "クマノミ",
  "searchLength": 4,
  "count": 3,
  "results": [ /* creaturesテーブルの行 */ ]
}
```

### バリデーション
- `q` が3文字未満の場合、ステータス200でエラーメッセージを返す

---

## 2. `search-creatures`

**パス:** `supabase/functions/search-creatures/index.ts`

### 概要
生き物データをページネーション付きで検索します。`q` が空の場合は全件取得。

### リクエスト

```
GET /functions/v1/search-creatures?q={検索ワード}&category={カテゴリー}&limit={件数}&offset={オフセット}
```

| パラメーター | 必須 | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| `q` | 任意 | string | `""` | 名前の前方一致検索 |
| `category` | 任意 | string | - | カテゴリーでフィルター |
| `limit` | 任意 | number | `100` | 取得件数 |
| `offset` | 任意 | number | `0` | 取得開始位置 |

### レスポンス

```json
{
  "query": "クマノミ",
  "category": null,
  "total": 10,
  "limit": 100,
  "offset": 0,
  "count": 10,
  "results": [ /* creaturesテーブルの行 */ ]
}
```

### ソート順
`category` 昇順 → `name` 昇順

---

## 3. `camera-option`

**パス:** `supabase/functions/camera-option/index.ts`

### 概要
カメラ名からそのカメラに対応するハウジング・レンズの組み合わせを返します。カメラタイプ（コンパクト／レンズ交換式）によってレスポンス形式が変わります。

### リクエスト

```
GET /functions/v1/camera-option?name={カメラ名}
```

| パラメーター | 必須 | 型 | 説明 |
|---|---|---|---|
| `name` | 必須 | string | カメラのモデル名（部分一致・大文字小文字無視） |

### レスポンス（コンパクトカメラ）

```json
{
  "camera": { "id": 1, "name": "TG-7" },
  "type": "compact",
  "housings": [
    { "id": 10, "name": "PT-059" }
  ],
  "combinations": []
}
```

### レスポンス（レンズ交換式カメラ）

```json
{
  "camera": { "id": 2, "name": "α7C" },
  "type": "interchangeable",
  "combinations": [
    {
      "housing": { "id": 20, "name": "MDX-a7C" },
      "lens": { "id": 30, "name": "FE 28-60mm F4-5.6" }
    }
  ]
}
```

### バリデーション
- `name` 未指定: `422`
- カメラが見つからない場合: `404`

---

## 4. `system-chart`

**パス:** `supabase/functions/system-chart/index.ts`

### 概要
カメラID・ハウジングID・レンズIDを指定して、対応するシステムチャート（機材の組み合わせ詳細）を1件返します。

### リクエスト

```
GET /functions/v1/system-chart?camera_id={ID}&housing_id={ID}&lens_id={ID}
```

| パラメーター | 必須 | 型 | 説明 |
|---|---|---|---|
| `camera_id` | 必須 | number | カメラID |
| `housing_id` | 必須 | number | ハウジングID |
| `lens_id` | 任意 | number | レンズID（コンパクトカメラは省略） |

### レスポンス

```json
{
  "id": 42,
  "camera":     { "id": 1,  "name": "α7C" },
  "housing":    { "id": 20, "name": "MDX-a7C" },
  "lens":       { "id": 30, "name": "FE 28-60mm F4-5.6" },
  "gear":       { "id": 5,  "name": "ズームギア" },
  "adapter":    null,
  "extension1": null,
  "extension2": null,
  "extension3": null,
  "port":       { "id": 8,  "name": "ドームポート 100mm" }
}
```

### バリデーション
- `camera_id` または `housing_id` 未指定: `422`
- 該当チャートが見つからない場合: `404`

---

## 5. `nearest-point`

**パス:** `supabase/functions/nearest-point/index.ts`

### 概要
現在地（緯度・経度）から指定半径内の近いダイビングスポットを検索します。内部でPostgreSQL RPC関数 `nearest_diving_points` を呼び出します。

### リクエスト

```
GET /functions/v1/nearest-point?lat={緯度}&lon={経度}&radius={半径km}&count={件数}
```

| パラメーター | 必須 | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| `lat` | 必須 | number | - | 緯度 |
| `lon` | 必須 | number | - | 経度 |
| `radius` | 任意 | number | `50` | 検索半径（km） |
| `count` | 任意 | number | null（全件） | 取得件数上限 |

### レスポンス

```json
{
  "lat": 35.6895,
  "lon": 139.6917,
  "radius_km": 50,
  "count": 5,
  "results": [ /* diving_pointsテーブルの行（距離付き） */ ]
}
```

### バリデーション
- `lat` または `lon` が数値でない場合: `400`
- `radius` が0以下の場合: `400`

---

## 共通仕様

- すべての関数はCORSに対応（`OPTIONS` リクエストを処理）
- エラー時は `{ "error": "..." }` または `{ "message": "..." }` 形式でJSONを返す
- 認証: `get-creatures` / `search-creatures` / `nearest-point` は `SUPABASE_SERVICE_ROLE_KEY`、`camera-option` / `system-chart` は `SUPABASE_ANON_KEY` を使用
