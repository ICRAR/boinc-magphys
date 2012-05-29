DROP SCHEMA IF EXISTS magphys_wu;
CREATE SCHEMA magphys_wu;
USE magphys_wu;

CREATE TABLE object (
  id          BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(128) NOT NULL,
  dimension_x INT UNSIGNED NOT NULL,
  dimension_y INT UNSIGNED NOT NULL,
  dimension_z INT UNSIGNED NOT NULL,
  description TEXT DEFAULT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;
  
CREATE TABLE square (
	id           BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
	object_id    BIGINT UNSIGNED NOT NULL REFERENCES object(id) ON UPDATE CASCADE ON DELETE RESTRICT,
	top_x        INT UNSIGNED NOT NULL,
	top_y        INT UNSIGNED NOT NULL,
	size         INT UNSIGNED NOT NULL,
	wu_generated DATETIME DEFAULT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE pixel (
	id           BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
	object_id    BIGINT UNSIGNED NOT NULL REFERENCES object(id) ON UPDATE CASCADE ON DELETE RESTRICT,
	square_id    BIGINT UNSIGNED NOT NULL REFERENCES square(id) ON UPDATE CASCADE ON DELETE RESTRICT,
	x            INT UNSIGNED NOT NULL,
	y            INT UNSIGNED NOT NULL,
	pixel_values TEXT NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

-- Objects are referenced by name
CREATE UNIQUE INDEX uniqObjectName ON object(name);

-- Squares within an object must be unique
CREATE UNIQUE INDEX uniqSquare ON square(object_id, top_x, top_y, size);

-- One pixel corresponds exactly to each (x, y) coordinate within an object
CREATE UNIQUE INDEX uniqPixel ON pixel(object_id, x, y);

