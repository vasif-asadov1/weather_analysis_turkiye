
    

    create  table
      "my_db"."main"."dim_location__dbt_tmp"
  
    
    as (
      

select distinct
    city,
    latitude,
    longitude
from "my_db"."main"."stg_weather"
    );
    
  