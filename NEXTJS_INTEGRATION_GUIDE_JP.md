# Diving API - Next.js 統合ガイド

このガイドは、Diving APIをNext.jsアプリケーションと統合するために必要なすべての情報を提供します。

## API概要

Diving APIはSupabaseで構築されており、海洋生物、カメラ機材、水中撮影のシステムチャートのエンドポイントを提供します。

**ベースURL:** `http://127.0.0.1:54321/functions/v1/`

## 利用可能なエンドポイント

### 1. 生物検索
**エンドポイント:** `GET /search-creatures`

オプションのフィルタリング機能付きで海洋生物を検索します。

**パラメータ:**
- `q` (string, 必須): 検索クエリ（最低3文字）
- `category` (string, オプション): 生物カテゴリでフィルタ
- `limit` (number, オプション): 返す結果の最大数（デフォルト: 100）
- `offset` (number, オプション): ページネーションオフセット（デフォルト: 0）

**レスポンス:**
```typescript
{
  query: string
  category: string | null
  total: number
  limit: number
  offset: number
  count: number
  results: Creature[]
}
```

### 2. 生物取得
**エンドポイント:** `GET /get-creatures`

前方一致検索で生物の詳細を取得します。

**パラメータ:**
- `q` (string, 必須): 検索クエリ（最低3文字）
- `category` (string, オプション): 生物カテゴリでフィルタ

**レスポンス:**
```typescript
{
  query: string
  searchPrefix: string
  searchLength: number
  count: number
  results: Creature[]
}
```

### 3. カメラオプション
**エンドポイント:** `GET /camera-option`

特定のカメラのハウジングとレンズオプションを取得します。

**パラメータ:**
- `name` (string, 必須): カメラモデル名

**レスポンス:**
```typescript
{
  camera: {
    id: number
    name: string
  }
  type: 'compact' | 'interchangeable'
  housings?: Array<{
    id: number
    name: string
  }>
  combinations?: Array<{
    housing: {
      id: number
      name: string
    } | null
    lens: {
      id: number
      name: string
    } | null
  }>
}
```

### 4. システムチャート
**エンドポイント:** `GET /system-chart`

カメラ、ハウジング、レンズの組み合わせのシステムチャート設定を取得します。

**パラメータ:**
- `camera_id` (string, 必須): カメラID
- `housing_id` (string, 必須): ハウジングID
- `lens_id` (string, オプション): レンズID（コンパクトカメラの場合はnull）

**レスポンス:**
```typescript
{
  id: number
  camera: RelationItem | null
  housing: RelationItem | null
  lens: RelationItem | null
  gear: RelationItem | null
  adapter: RelationItem | null
  extension1: RelationItem | null
  extension2: RelationItem | null
  extension3: RelationItem | null
  port: RelationItem | null
}
```

## TypeScript型定義

```typescript
// コア型
interface Creature {
  id: number
  name: string
  scientific_name?: string
  category?: string
  subcategory?: string
  description?: string
  habitat?: string
  size?: string
  depth_range?: string
  rarity?: string
  created_at: string
  updated_at: string
}

interface RelationItem {
  id: number
  name: string
}

interface CameraInfo {
  id: number
  name: string
}

interface HousingInfo {
  id: number
  name: string
}

interface LensInfo {
  id: number
  name: string
}

interface Combination {
  housing: HousingInfo | null
  lens: LensInfo | null
}

// APIレスポンス型
interface SearchCreaturesResponse {
  query: string
  category: string | null
  total: number
  limit: number
  offset: number
  count: number
  results: Creature[]
}

interface GetCreaturesResponse {
  query: string
  searchPrefix: string
  searchLength: number
  count: number
  results: Creature[]
}

interface CameraOptionResponse {
  camera: CameraInfo
  type: 'compact' | 'interchangeable'
  housings?: HousingInfo[]
  combinations?: Combination[]
}

interface SystemChartResponse {
  id: number
  camera: RelationItem | null
  housing: RelationItem | null
  lens: RelationItem | null
  gear: RelationItem | null
  adapter: RelationItem | null
  extension1: RelationItem | null
  extension2: RelationItem | null
  extension3: RelationItem | null
  port: RelationItem | null
}
```

## Next.js APIクライアント

### セットアップ

1. 依存関係をインストール:
```bash
npm install @supabase/supabase-js
```

2. 環境変数を作成（`.env.local`）:
```env
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### APIクライアント実装

```typescript
// lib/diving-api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL + '/functions/v1'

export class DivingApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'DivingApiError'
  }
}

async function apiRequest<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`)
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) url.searchParams.append(key, value)
    })
  }

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
      'Content-Type': 'application/json',
    }
  })

  if (!response.ok) {
    throw new DivingApiError(response.status, await response.text())
  }

  return response.json()
}

export const divingApi = {
  // ページネーション付き生物検索
  searchCreatures: (params: {
    q: string
    category?: string
    limit?: number
    offset?: number
  }): Promise<SearchCreaturesResponse> => {
    return apiRequest('/search-creatures', {
      q: params.q,
      category: params.category,
      limit: params.limit?.toString(),
      offset: params.offset?.toString(),
    })
  },

  // 前方一致検索で生物取得
  getCreatures: (params: {
    q: string
    category?: string
  }): Promise<GetCreaturesResponse> => {
    return apiRequest('/get-creatures', {
      q: params.q,
      category: params.category,
    })
  },

  // カメラオプション取得
  getCameraOptions: (cameraName: string): Promise<CameraOptionResponse> => {
    return apiRequest('/camera-option', { name: cameraName })
  },

  // システムチャート取得
  getSystemChart: (params: {
    camera_id: string
    housing_id: string
    lens_id?: string
  }): Promise<SystemChartResponse> => {
    return apiRequest('/system-chart', {
      camera_id: params.camera_id,
      housing_id: params.housing_id,
      lens_id: params.lens_id,
    })
  },
}
```

## React Hooks

### データ取得用カスタムフック

```typescript
// hooks/use-diving-api.ts
import { useState, useEffect } from 'react'
import { divingApi, DivingApiError } from '@/lib/diving-api'

export function useCreatureSearch(query: string, category?: string) {
  const [data, setData] = useState<SearchCreaturesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (query.length < 3) {
      setData(null)
      return
    }

    const searchCreatures = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const result = await divingApi.searchCreatures({ q: query, category })
        setData(result)
      } catch (err) {
        setError(err instanceof DivingApiError ? err.message : 'エラーが発生しました')
      } finally {
        setLoading(false)
      }
    }

    const debounceTimer = setTimeout(searchCreatures, 300)
    return () => clearTimeout(debounceTimer)
  }, [query, category])

  return { data, loading, error }
}

export function useCameraOptions(cameraName: string) {
  const [data, setData] = useState<CameraOptionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!cameraName) {
      setData(null)
      return
    }

    const fetchCameraOptions = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const result = await divingApi.getCameraOptions(cameraName)
        setData(result)
      } catch (err) {
        setError(err instanceof DivingApiError ? err.message : 'エラーが発生しました')
      } finally {
        setLoading(false)
      }
    }

    fetchCameraOptions()
  }, [cameraName])

  return { data, loading, error }
}
```

## コンポーネント例

### 生物検索コンポーネント

```tsx
// components/CreatureSearch.tsx
'use client'

import { useState } from 'react'
import { useCreatureSearch } from '@/hooks/use-diving-api'

export default function CreatureSearch() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const { data, loading, error } = useCreatureSearch(query, category)

  return (
    <div className="p-4">
      <div className="mb-4 space-y-2">
        <input
          type="text"
          placeholder="生物を検索（最低3文字）..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full p-2 border rounded"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full p-2 border rounded"
        >
          <option value="">すべてのカテゴリ</option>
          <option value="fish">魚類</option>
          <option value="crustacean">甲殻類</option>
          <option value="sea_slug">ウミウシ</option>
        </select>
      </div>

      {loading && <div>読み込み中...</div>}
      {error && <div className="text-red-500">エラー: {error}</div>}
      
      {data && (
        <div>
          <p className="mb-2">{data.count}件の結果が見つかりました</p>
          <div className="grid gap-2">
            {data.results.map((creature) => (
              <div key={creature.id} className="p-3 border rounded">
                <h3 className="font-bold">{creature.name}</h3>
                {creature.scientific_name && (
                  <p className="italic text-gray-600">{creature.scientific_name}</p>
                )}
                {creature.category && (
                  <span className="inline-block px-2 py-1 text-xs bg-blue-100 rounded">
                    {creature.category}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

### カメラオプションコンポーネント

```tsx
// components/CameraOptions.tsx
'use client'

import { useState } from 'react'
import { useCameraOptions } from '@/hooks/use-diving-api'

export default function CameraOptions() {
  const [cameraName, setCameraName] = useState('')
  const [submitted, setSubmitted] = useState('')
  const { data, loading, error } = useCameraOptions(submitted)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(cameraName)
  }

  return (
    <div className="p-4">
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="カメラ名を入力..."
            value={cameraName}
            onChange={(e) => setCameraName(e.target.value)}
            className="flex-1 p-2 border rounded"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            検索
          </button>
        </div>
      </form>

      {loading && <div>読み込み中...</div>}
      {error && <div className="text-red-500">エラー: {error}</div>}
      
      {data && (
        <div>
          <h2 className="text-xl font-bold mb-4">{data.camera.name}</h2>
          <p className="mb-4">タイプ: <span className="font-semibold">{data.type === 'compact' ? 'コンパクト' : 'レンズ交換式'}</span></p>
          
          {data.type === 'compact' && data.housings && (
            <div>
              <h3 className="text-lg font-semibold mb-2">利用可能なハウジング:</h3>
              <div className="grid gap-2">
                {data.housings.map((housing) => (
                  <div key={housing.id} className="p-2 border rounded">
                    {housing.name}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {data.type === 'interchangeable' && data.combinations && (
            <div>
              <h3 className="text-lg font-semibold mb-2">ハウジング&レンズの組み合わせ:</h3>
              <div className="grid gap-2">
                {data.combinations.map((combo, index) => (
                  <div key={index} className="p-3 border rounded">
                    <div><strong>ハウジング:</strong> {combo.housing?.name}</div>
                    <div><strong>レンズ:</strong> {combo.lens?.name}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

## エラーハンドリング

APIには意味のあるエラーメッセージによる適切なエラーハンドリングが含まれています。常にAPI呼び出しをtry-catchブロックで囲み、異なるエラーシナリオを処理してください：

```typescript
try {
  const data = await divingApi.searchCreatures({ q: 'クマノミ' })
  // 成功時の処理
} catch (error) {
  if (error instanceof DivingApiError) {
    if (error.status === 404) {
      // 見つからない場合の処理
    } else if (error.status === 422) {
      // バリデーションエラーの処理
    } else {
      // その他のAPIエラーの処理
    }
  } else {
    // ネットワークまたはその他のエラーの処理
  }
}
```

## ベストプラクティス

1. **検索入力をデバウンス**して過度なAPI呼び出しを避ける
2. **結果をキャッシュ**する（React QueryやSWRを使用）
3. **ローディング状態を処理**して良いユーザー体験を提供
4. **API呼び出し前に入力を検証**（検索は最低3文字）
5. **TypeScriptを使用**してより良い型安全性と開発体験を得る
6. **エラーを適切に処理**してユーザーフレンドリーなエラーメッセージを提供

## 認証

APIはJWT検証を使用します。すべてのリクエストでSupabase anonキーを含む認証ヘッダーを必ず含めてください。