// supabase/functions/search-creatures/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req: Request) => {
  // CORS対応
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // URLパラメータを取得
    const url = new URL(req.url)
    const query = url.searchParams.get('q') || ''
    const category = url.searchParams.get('category') || null
    const limit = parseInt(url.searchParams.get('limit') || '100')
    const offset = parseInt(url.searchParams.get('offset') || '0')

    // 環境変数から認証情報を取得
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    // Supabaseクライアント作成
    const supabase = createClient(supabaseUrl, supabaseKey)

    // クエリ構築
    let queryBuilder = supabase
      .from('creatures')
      .select('*', { count: 'exact' })

    // 検索条件
    if (query) {
      queryBuilder = queryBuilder.ilike('name', `${query}%`)
    }

    // カテゴリーフィルター
    if (category) {
      queryBuilder = queryBuilder.eq('category', category)
    }

    // ソートとページネーション
    const { data, error, count } = await queryBuilder
      .order('category', { ascending: true })
      .order('name', { ascending: true })
      .range(offset, offset + limit - 1)

    if (error) throw error

    // レスポンス
    return new Response(
      JSON.stringify({
        query,
        category,
        total: count || 0,
        limit,
        offset,
        count: data?.length || 0,
        results: data || []
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ 
        error: error instanceof Error ? error.message : 'Unknown error'
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    )
  }
})
