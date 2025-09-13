// supabase/functions/search-creatures/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const url = new URL(req.url)
    const query = url.searchParams.get('q') || ''
    const category = url.searchParams.get('category')
    
    // 最低3文字必要
    if (query.length < 3) {
      return new Response(
        JSON.stringify({
          error: '検索文字は3文字以上入力してください',
          query: query,
          results: []
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200
        }
      )
    }

    // 入力された文字数をそのまま使用（3文字以上）
    const searchPrefix = query

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    let queryBuilder = supabase
      .from('creatures')
      .select('*')
      // 入力された文字列全体で前方一致検索
      .ilike('name', `${searchPrefix}%`)

    if (category) {
      queryBuilder = queryBuilder.eq('category', category)
    }

    const { data, error } = await queryBuilder
      .order('name', { ascending: true })

    if (error) throw error

    return new Response(
      JSON.stringify({
        query: query,
        searchPrefix: searchPrefix,
        searchLength: searchPrefix.length,
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
