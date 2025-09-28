import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4'
import { corsHeaders } from '../_shared/cors.ts'

interface RelationItem {
  id: number
  name: string
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

serve(async (req) => {
  // CORS対応
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // URLパラメータを取得
    const url = new URL(req.url)
    const cameraId = url.searchParams.get('camera_id')
    const housingId = url.searchParams.get('housing_id')
    const lensId = url.searchParams.get('lens_id')

    // バリデーション
    if (!cameraId || !housingId) {
      return new Response(
        JSON.stringify({ message: 'camera_id and housing_id are required.' }),
        {
          status: 422,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Supabaseクライアント初期化
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    const supabase = createClient(supabaseUrl, supabaseAnonKey)

    // クエリ構築
    let query = supabase
      .from('system_charts')
      .select(`
        id,
        camera_id,
        housing_id,
        lens_id,
        gear_id,
        adapter_id,
        extension1_id,
        extension2_id,
        port_id,
        cameras!camera_id(id, model),
        housings!housing_id(id, model),
        lenses!lens_id(id, model),
        gears!gear_id(id, model),
        adapters!adapter_id(id, model),
        extension1:extensions!extension1_id(id, model),
        extension2:extensions!extension2_id(id, model),
        ports!port_id(id, model)
      `)
      .eq('camera_id', cameraId)
      .eq('housing_id', housingId)

    // lens_idの条件
    if (lensId) {
      query = query.eq('lens_id', lensId)
    } else {
      query = query.is('lens_id', null)
    }

    // 最初の1件を取得
    const { data: chart, error } = await query.limit(1).single()

    if (error || !chart) {
      return new Response(
        JSON.stringify({ message: 'System chart not found.' }),
        {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // レスポンス整形
    const formatRelation = (relation: any): RelationItem | null => {
      return relation ? {
        id: relation.id,
        name: relation.model || relation.name
      } : null
    }

    const response: SystemChartResponse = {
      id: chart.id,
      camera: formatRelation(chart.cameras),
      housing: formatRelation(chart.housings),
      lens: formatRelation(chart.lenses),
      gear: formatRelation(chart.gears),
      adapter: formatRelation(chart.adapters),
      extension1: formatRelation(chart.extension1),
      extension2: formatRelation(chart.extension2),
      extension3: null, // extension3がテーブルにない場合
      port: formatRelation(chart.ports)
    }

    return new Response(
      JSON.stringify(response),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ 
        message: 'Internal server error',
        error: error.message 
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})
