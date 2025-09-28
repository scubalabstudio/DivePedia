import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4'
import { corsHeaders } from '../_shared/cors.ts'

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

interface CameraOptionResponse {
  camera: CameraInfo
  type: 'compact' | 'interchangeable'
  housings?: HousingInfo[]
  combinations?: Combination[]
}

serve(async (req) => {
  // CORS対応
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // URLパラメータを取得
    const url = new URL(req.url)
    const cameraName = url.searchParams.get('name')

    if (!cameraName) {
      return new Response(
        JSON.stringify({ message: 'Camera name is required.' }),
        {
          status: 422,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Supabaseクライアントを初期化
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    const supabase = createClient(supabaseUrl, supabaseAnonKey)

    // カメラを検索（大文字小文字を無視）
    let { data: cameras, error: cameraError } = await supabase
      .from('cameras')
      .select('*')
      .ilike('model', `%${cameraName}%`)

    if (cameraError) throw cameraError

    // 見つからない場合は完全一致も試す
    if (!cameras || cameras.length === 0) {
      const exactMatch = await supabase
        .from('cameras')
        .select('*')
        .eq('model', cameraName)
      
      cameras = exactMatch.data
    }

    if (!cameras || cameras.length === 0) {
      return new Response(
        JSON.stringify({ message: 'Camera not found.' }),
        {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    const camera = cameras[0]

    // システムチャートから組み合わせを取得
    const { data: charts, error: chartError } = await supabase
      .from('system_charts')
      .select(`
        *,
        cameras!camera_id(id, model),
        housings!housing_id(id, model),
        lenses!lens_id(id, model),
        ports!port_id(id, model),
        gears!gear_id(id, model)
      `)
      .eq('camera_id', camera.id)

    if (chartError) throw chartError

    // カメラタイプの判定（レンズIDがすべてnullならコンパクトカメラ）
    const isCompactCamera = charts?.every(chart => chart.lens_id === null) ?? true

    const cameraInfo: CameraInfo = {
      id: camera.id,
      name: camera.model
    }

    let response: CameraOptionResponse

    if (isCompactCamera) {
      // コンパクトカメラの場合
      const housingsMap = new Map<number, HousingInfo>()
      
      charts?.forEach(chart => {
        if (chart.housings) {
          housingsMap.set(chart.housings.id, {
            id: chart.housings.id,
            name: chart.housings.model
          })
        }
      })

      response = {
        camera: cameraInfo,
        type: 'compact',
        housings: Array.from(housingsMap.values()),
        combinations: []
      }
    } else {
      // レンズ交換式カメラの場合
      const combinationsMap = new Map<string, Combination>()
      
      charts?.forEach(chart => {
        if (chart.housings && chart.lenses) {
          const key = `${chart.housings.id}-${chart.lenses.id}`
          if (!combinationsMap.has(key)) {
            combinationsMap.set(key, {
              housing: {
                id: chart.housings.id,
                name: chart.housings.model
              },
              lens: {
                id: chart.lenses.id,
                name: chart.lenses.model
              }
            })
          }
        }
      })

      response = {
        camera: cameraInfo,
        type: 'interchangeable',
        combinations: Array.from(combinationsMap.values())
      }
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
