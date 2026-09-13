{{ config(materialized='table') }}

select
    w.city,
    w.measured_at,
    w.temperature_2m,
    w.relative_humidity_2m,
    w.apparent_temperature,
    w.precipitation,
    w.wind_speed_10m,
    a.pm10,
    a.pm2_5,
    a.nitrogen_dioxide,
    a.european_aqi
from {{ ref('stg_weather') }} w
left join {{ ref('stg_air_quality') }} a
    on w.city = a.city 
    and w.measured_at = a.measured_at
where w.measured_at is not null