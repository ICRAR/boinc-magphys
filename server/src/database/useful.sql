SELECT
table_schema, count(*) TABLES,
concat(round(sum(table_rows)/1000000,2),'M')
rows,concat(round(sum(data_length)/(1024*1024*1024),2),'G')
DATA,concat(round(sum(index_length)/(1024*1024*1024),2),'G')
idx,concat(round(sum(data_length+index_length)/(1024*1024*1024),2),'G')
total_size,round(sum(index_length)/sum(data_length),2) idxfrac
FROM information_schema.TABLES group by table_schema;

select table_name, round(((data_length + index_length) / (1024*1024*1024)),2) as 'size in gigs' from information_schema.tables where table_schema = 'magphys';


select status_id, count(*)
from galaxy
group by status_id;


update galaxy set status_id = 3
where galaxy_id >= 443
      and galaxy_id <= 499
      and status_id = 2;

SELECT CONCAT('OPTIMIZE TABLE ',table_schema,'.',table_name,';') OptimizeTableSQL
FROM information_schema.tables
WHERE table_schema in ('magphys','pogs')
      AND engine = 'InnoDB'
ORDER BY (data_length+index_length);

show variables like 'innodb%';
