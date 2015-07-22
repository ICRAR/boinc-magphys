SELECT
table_schema, count(*) TABLES,
concat(round(sum(table_rows)/1000000,2),'M') rows,
concat(round(sum(data_length)/(1024*1024*1024),2),'G') DATA,
concat(round(sum(index_length)/(1024*1024*1024),2),'G') idx,
concat(round(sum(data_length+index_length)/(1024*1024*1024),2),'G') total_size,
round(sum(index_length)/sum(data_length),2) idxfrac
FROM information_schema.TABLES
group by table_schema;

select table_schema, table_name,
	round(((data_length) / (1024*1024)),2) as 'Data (M)',
	round(((index_length) / (1024*1024)),2) as 'Index (M)'
from information_schema.tables
where table_schema in ('magphys', 'pogs')
order by table_schema, table_name;

select status_id, count(*)
from galaxy
group by status_id;


-- update galaxy set status_id = 3
-- where galaxy_id >= 443
--       and galaxy_id <= 499
--       and status_id = 2;

SELECT CONCAT('OPTIMIZE TABLE ',table_schema,'.',table_name,';') OptimizeTableSQL
FROM information_schema.tables
WHERE table_schema in ('magphys','pogs')
      AND engine = 'InnoDB'
ORDER BY (data_length+index_length);

show variables like 'innodb%';

-- How to empty the database
-- truncate table result;
-- truncate table workunit;

-- truncate table pixel_result;
-- truncate table fits_header;
-- truncate table area_user;
-- delete from area;
-- truncate table image_filters_used;
-- truncate table tag_galaxy;
-- truncate table tag_register;
-- delete from tag;
-- truncate table user_pixel;
-- delete from galaxy;
-- delete from register;


-- Blocking the hosts of a user
--update host
--set max_results_day = -1
--where userid = <blah>;

-- Number of Galaxies
select max(galaxy_id)
from magphys.galaxy;

-- Number of areas
select max(area_id)
from magphys.area;

-- Number of pixels
select max(pxresult_id)
from magphys.pixel_result;

select count(*)
from register
where create_time is null;

--gets the count of integrated flux areas for this galaxy
select count(*)
from area
where galaxy_id = GALAXY_ID /*replace with galaxy id*/
AND area.top_x = -1;

--gets the count of radial areas for this galaxy.
select count(*)
from area
where galaxy_id = GALAXY_ID /*replace with galaxy id*/
AND area.top_x = -2;


-- pogs
-- Number active users
select count(*) 
from pogs.user
where expavg_credit > 0;

-- Number active hosts
select count(*) 
from pogs.host
where expavg_credit > 0;

-- SHow locks
SHOW FULL PROCESSLIST;
