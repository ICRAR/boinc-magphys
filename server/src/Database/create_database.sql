DROP SCHEMA IF EXISTS magphys;
CREATE SCHEMA magphys;
USE magphys;

CREATE TABLE pixel_result (
  pxresult_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  point_name  VARCHAR(100) NOT NULL,
  workunit_id INTEGER,
  i_sfh       DOUBLE NOT NULL,
  i_ir        DOUBLE NOT NULL,
  chi2        DOUBLE NOT NULL,
  redshift    DOUBLE NOT NULL,
  fmu_sfh     DOUBLE,
  fmu_ir      DOUBLE,
  mu          DOUBLE,
  tauv        DOUBLE,
  s_sfr       DOUBLE,
  m           DOUBLE,
  ldust       DOUBLE,
  t_w_bc      DOUBLE,
  t_c_ism     DOUBLE,
  xi_c_tot    DOUBLE,
  xi_pah_tot  DOUBLE,
  xi_mir_tot  DOUBLE,
  x_w_tot     DOUBLE,
  tvism       DOUBLE,
  mdust       DOUBLE,
  sfr         DOUBLE,
  i_opt       DOUBLE,
  dmstar      DOUBLE,
  dfmu_aux    DOUBLE,
  dz          DOUBLE
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE pixel_filter (
  pxfilter_id                BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  pxresult_id                BIGINT UNSIGNED NOT NULL,
  filter_name                VARCHAR(100) NOT NULL,
  observed_flux              DOUBLE NOT NULL,
  observational_uncertainty  DOUBLE NOT NULL,
  flux_bfm                   DOUBLE NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE pixel_parameter (
  pxparameter_id     BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  pxresult_id        BIGINT UNSIGNED NOT NULL,
  parameter_name     VARCHAR(100) NOT NULL,
  percentile2_5      DOUBLE NOT NULL,
  percentile16       DOUBLE NOT NULL,
  percentile50       DOUBLE NOT NULL,
  percentile84       DOUBLE NOT NULL,
  percentile97_5     DOUBLE NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;


CREATE TABLE pixel_histogram (
  pxhistogram_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  pxparameter_id BIGINT UNSIGNED NOT NULL,
  x_axis         DOUBLE NOT NULL,
  hist_value     DOUBLE NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE pixel_user (
  pxuser_id                  BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  pxresult_id                BIGINT UNSIGNED NOT NULL,
  userid                     INTEGER NOT NULL,
  create_time                TIMESTAMP
) CHARACTER SET utf8 ENGINE=InnoDB;

ALTER TABLE pixel_filter ADD CONSTRAINT pxfilter_result_fk FOREIGN KEY(pxresult_id) REFERENCES pixel_result(pxresult_id);
ALTER TABLE pixel_parameter ADD CONSTRAINT pxparameter_result_fk FOREIGN KEY(pxresult_id) REFERENCES pixel_result(pxresult_id);
ALTER TABLE pixel_histogram ADD CONSTRAINT pxhistogram_parameter_fk FOREIGN KEY(pxparameter_id) REFERENCES pixel_parameter(pxparameter_id);
ALTER TABLE pixel_user ADD CONSTRAINT pxuser_result_fk FOREIGN KEY(pxresult_id) REFERENCES pixel_result(pxresult_id);

CREATE INDEX pixelresult_name_ix ON pixel_result(point_name);

CREATE TABLE galaxy (
  galaxy_id   BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(128) NOT NULL,
  dimension_x INT UNSIGNED NOT NULL,
  dimension_y INT UNSIGNED NOT NULL,
  dimension_z INT UNSIGNED NOT NULL,
  description TEXT DEFAULT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE square (
  square_id    BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_id    BIGINT UNSIGNED NOT NULL,
  top_x        INT UNSIGNED NOT NULL,
  top_y        INT UNSIGNED NOT NULL,
  size         INT UNSIGNED NOT NULL,
  wu_generated DATETIME DEFAULT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE pixel (
  pixel_id     BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  square_id    BIGINT UNSIGNED NOT NULL,
  x            INT UNSIGNED NOT NULL,
  y            INT UNSIGNED NOT NULL,
  redshift     DECIMAL(20,18) NOT NULL,
  pixel_values TEXT NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

ALTER TABLE square ADD CONSTRAINT square_galaxy_fk FOREIGN KEY(galaxy_id) REFERENCES galaxy(galaxy_id);
ALTER TABLE pixel  ADD CONSTRAINT pixel_square_fk FOREIGN KEY(square_id) REFERENCES square(square_id);


CREATE INDEX pixel_square_ix ON pixel(square_id);

-- Objects are referenced by name
CREATE UNIQUE INDEX galaxy_name_ix ON galaxy(name);

-- Squares within an object must be unique
CREATE UNIQUE INDEX square_ix ON square(galaxy_id, top_x, top_y, size);

-- Makes it easier to grab unprocessed squares (imagine if MySQL had had partial indices).
CREATE INDEX wu_generation_id ON square(wu_generated);

-- One pixel corresponds exactly to each (x, y) coordinate within an object
CREATE INDEX pixel_ix ON pixel(x, y);

