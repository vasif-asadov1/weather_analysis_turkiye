{{ config(materialized='table') }}

select distinct
    city,
    latitude,
    longitude
from {{ ref('stg_weather') }}