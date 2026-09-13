{{ config(materialized='table') }}

with all_times as (
    select measured_at from {{ ref('stg_weather') }}
    union
    select measured_at from {{ ref('stg_air_quality') }}
)

select distinct
    measured_at,
    cast(measured_at as date) as date_day,
    extract(year from measured_at) as year,
    extract(month from measured_at) as month,
    extract(day from measured_at) as day,
    extract(hour from measured_at) as hour
from all_times
