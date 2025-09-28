# Diving API - Next.js Integration Guide

This guide provides everything needed to integrate the Diving API with a Next.js application.

## API Overview

The Diving API is built with Supabase and provides endpoints for marine life creatures, camera gear, and system charts for underwater photography.

**Base URL:** `http://127.0.0.1:54321/functions/v1/`

## Available Endpoints

### 1. Search Creatures
**Endpoint:** `GET /search-creatures`

Search for marine creatures with optional filtering.

**Parameters:**
- `q` (string, required): Search query (minimum 3 characters)
- `category` (string, optional): Filter by creature category
- `limit` (number, optional): Maximum results to return (default: 100)
- `offset` (number, optional): Pagination offset (default: 0)

**Response:**
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

### 2. Get Creatures
**Endpoint:** `GET /get-creatures`

Get creature details with prefix-based search.

**Parameters:**
- `q` (string, required): Search query (minimum 3 characters)
- `category` (string, optional): Filter by creature category

**Response:**
```typescript
{
  query: string
  searchPrefix: string
  searchLength: number
  count: number
  results: Creature[]
}
```

### 3. Camera Options
**Endpoint:** `GET /camera-option`

Get housing and lens options for a specific camera.

**Parameters:**
- `name` (string, required): Camera model name

**Response:**
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

### 4. System Chart
**Endpoint:** `GET /system-chart`

Get system chart configuration for camera, housing, and lens combination.

**Parameters:**
- `camera_id` (string, required): Camera ID
- `housing_id` (string, required): Housing ID
- `lens_id` (string, optional): Lens ID (null for compact cameras)

**Response:**
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

## TypeScript Types

```typescript
// Core Types
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

// API Response Types
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

## Next.js API Client

### Setup

1. Install dependencies:
```bash
npm install @supabase/supabase-js
```

2. Create environment variables (`.env.local`):
```env
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### API Client Implementation

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
  // Search creatures with pagination
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

  // Get creatures with prefix search
  getCreatures: (params: {
    q: string
    category?: string
  }): Promise<GetCreaturesResponse> => {
    return apiRequest('/get-creatures', {
      q: params.q,
      category: params.category,
    })
  },

  // Get camera options
  getCameraOptions: (cameraName: string): Promise<CameraOptionResponse> => {
    return apiRequest('/camera-option', { name: cameraName })
  },

  // Get system chart
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

### Custom Hooks for Data Fetching

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
        setError(err instanceof DivingApiError ? err.message : 'An error occurred')
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
        setError(err instanceof DivingApiError ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchCameraOptions()
  }, [cameraName])

  return { data, loading, error }
}
```

## Example Components

### Creature Search Component

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
          placeholder="Search creatures (min 3 characters)..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full p-2 border rounded"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full p-2 border rounded"
        >
          <option value="">All categories</option>
          <option value="fish">Fish</option>
          <option value="crustacean">Crustacean</option>
          <option value="sea_slug">Sea Slug</option>
        </select>
      </div>

      {loading && <div>Loading...</div>}
      {error && <div className="text-red-500">Error: {error}</div>}
      
      {data && (
        <div>
          <p className="mb-2">Found {data.count} results</p>
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

### Camera Options Component

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
            placeholder="Enter camera name..."
            value={cameraName}
            onChange={(e) => setCameraName(e.target.value)}
            className="flex-1 p-2 border rounded"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Search
          </button>
        </div>
      </form>

      {loading && <div>Loading...</div>}
      {error && <div className="text-red-500">Error: {error}</div>}
      
      {data && (
        <div>
          <h2 className="text-xl font-bold mb-4">{data.camera.name}</h2>
          <p className="mb-4">Type: <span className="font-semibold">{data.type}</span></p>
          
          {data.type === 'compact' && data.housings && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Available Housings:</h3>
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
              <h3 className="text-lg font-semibold mb-2">Housing & Lens Combinations:</h3>
              <div className="grid gap-2">
                {data.combinations.map((combo, index) => (
                  <div key={index} className="p-3 border rounded">
                    <div><strong>Housing:</strong> {combo.housing?.name}</div>
                    <div><strong>Lens:</strong> {combo.lens?.name}</div>
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

## Error Handling

The API includes proper error handling with meaningful error messages. Always wrap API calls in try-catch blocks and handle different error scenarios:

```typescript
try {
  const data = await divingApi.searchCreatures({ q: 'クマノミ' })
  // Handle success
} catch (error) {
  if (error instanceof DivingApiError) {
    if (error.status === 404) {
      // Handle not found
    } else if (error.status === 422) {
      // Handle validation error
    } else {
      // Handle other API errors
    }
  } else {
    // Handle network or other errors
  }
}
```

## Best Practices

1. **Debounce search inputs** to avoid excessive API calls
2. **Cache results** when appropriate using React Query or SWR
3. **Handle loading states** to provide good user experience
4. **Validate inputs** before making API calls (minimum 3 characters for searches)
5. **Use TypeScript** for better type safety and development experience
6. **Handle errors gracefully** with user-friendly error messages

## Authentication

The API uses JWT verification. Make sure to include the authorization header with your Supabase anon key in all requests.