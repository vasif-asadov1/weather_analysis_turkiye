select
    city,
    cast(time as timestamp) as measured_at,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    cast(temperature_2m as double) as temperature_2m,
    cast(relative_humidity_2m as double) as relative_humidity_2m,
    cast(apparent_temperature as double) as apparent_temperature,
    cast(precipitation as double) as precipitation,
    cast(wind_speed_10m as double) as wind_speed_10m
from {{ source('motherduck_raw', 'raw_weather') }}
where time is not null