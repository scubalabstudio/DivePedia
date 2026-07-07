-- diving_pointsにlatitude/longitudeカラムを追加
ALTER TABLE diving_points
  ADD COLUMN IF NOT EXISTS latitude  DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;

-- 現在地から半径radius_km以内のダイビングポイントを距離順で返すRPC関数
CREATE OR REPLACE FUNCTION nearest_diving_points(
  user_lat      DOUBLE PRECISION,
  user_lon      DOUBLE PRECISION,
  radius_km     DOUBLE PRECISION,
  result_count  INTEGER DEFAULT NULL
)
RETURNS TABLE(
  id           INTEGER,
  name         VARCHAR,
  prefecture   VARCHAR,
  latitude     DOUBLE PRECISION,
  longitude    DOUBLE PRECISION,
  distance_km  DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
  SELECT id, name, prefecture, latitude, longitude, distance_km
  FROM (
    SELECT
      id,
      name,
      prefecture,
      latitude,
      longitude,
      6371.0 * acos(
        LEAST(1.0,
          cos(radians(user_lat)) * cos(radians(latitude)) *
          cos(radians(longitude) - radians(user_lon)) +
          sin(radians(user_lat)) * sin(radians(latitude))
        )
      ) AS distance_km
    FROM diving_points
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
  ) sub
  WHERE distance_km <= radius_km
  ORDER BY distance_km
  LIMIT result_count;
$$;
