SELECT
table_schema, count(*) TABLES,
concat(round(sum(table_rows)/1000000,2),'M')
rows,concat(round(sum(data_length)/(1024*1024*1024),2),'G')
DATA,concat(round(sum(index_length)/(1024*1024*1024),2),'G')
idx,concat(round(sum(data_length+index_length)/(1024*1024*1024),2),'G')
total_size,round(sum(index_length)/sum(data_length),2) idxfrac
FROM information_schema.TABLES group by table_schema;

select table_name, round(((data_length + index_length) / (1024*1024)),2) as 'size in megs' from information_schema.tables where table_schema = 'magphys';
