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
    const lat = parseFloat(url.searchParams.get('lat') ?? '')
    const lon = parseFloat(url.searchParams.get('lon') ?? '')
    const radius = parseFloat(url.searchParams.get('radius') ?? '50')
    const countParam = url.searchParams.get('count')
    const resultCount = countParam !== null ? parseInt(countParam) : null

    if (isNaN(lat) || isNaN(lon)) {
      return new Response(
        JSON.stringify({ error: 'lat と lon は必須パラメーターです' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      )
    }

    if (isNaN(radius) || radius <= 0) {
      return new Response(
        JSON.stringify({ error: 'radius は正の数値で指定してください（単位: km）' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      )
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    const { data, error } = await supabase.rpc('nearest_diving_points', {
      user_lat: lat,
      user_lon: lon,
      radius_km: radius,
      result_count: resultCount,
    })

    if (error) throw error

    return new Response(
      JSON.stringify({
        lat,
        lon,
        radius_km: radius,
        count: data?.length ?? 0,
        results: data ?? [],
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
    )
  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    )
  }
})
