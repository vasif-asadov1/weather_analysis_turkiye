
  
  create view "my_db"."main"."stg_air_quality__dbt_tmp" as (
    select
    city,
    cast(time as timestamp) as measured_at,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    cast(pm10 as double) as pm10,
    cast(pm2_5 as double) as pm2_5,
    cast(nitrogen_dioxide as double) as nitrogen_dioxide,
    cast(european_aqi as double) as european_aqi
from "my_db"."main"."raw_air_quality"
where time is not null
  );
