insert into galaxy (name, dimension_x, dimension_y, dimension_z, redshift)
values ('Test 1', 2400, 2400, 0, 0.);
  
insert into area (galaxy_id, top_x, top_y, bottom_x, bottom_y)
values (1, 7, 7, 13, 13);
 
insert into area_user (area_id, userid)
values (1, 2);

insert into area (galaxy_id, top_x, top_y, bottom_x, bottom_y)
values (1, 13, 7, 20, 13);

insert into area_user (area_id, userid)
values (2, 2);

insert into area (galaxy_id, top_x, top_y, bottom_x, bottom_y)
values (1, 7, 13, 13, 20);

insert into area_user (area_id, userid)
values (3, 2);

insert into area (galaxy_id, top_x, top_y, bottom_x, bottom_y)
values (1, 13, 7, 20, 20);

insert into area_user (area_id, userid)
values (4, 2);

insert into pixel_result (area_id, galaxy_id, x, y)
values (1, 1, 1, 1);

insert into pixel_result (area_id, galaxy_id, x, y)
values (1, 1, 1, 2);

commit;