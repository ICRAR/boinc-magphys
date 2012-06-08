DROP SCHEMA IF EXISTS magphys_as;
CREATE SCHEMA magphys_as;
USE magphys_as;

CREATE TABLE work_unit (
  work_unit_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  point_name  VARCHAR(100) NOT NULL,
  i_sfh       FLOAT NOT NULL,
  i_ir        FLOAT NOT NULL,
  chi2        FLOAT NOT NULL,
  redshift    FLOAT NOT NULL,
  a           FLOAT,
  fmu_sfh     FLOAT,
  fmu_ir      FLOAT,
  mu          FLOAT,
  tauv        FLOAT,
  s_sfr       FLOAT,
  m           FLOAT,
  ldust       FLOAT,
  t_w_bc      FLOAT,
  t_c_ism     FLOAT,
  xi_c_tot    FLOAT,
  xi_pah_tot  FLOAT,
  xi_mir_tot  FLOAT,
  x_w_tot     FLOAT,
  tvism       FLOAT,
  mdust       FLOAT,
  sfr         FLOAT
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE work_unit_filter (
  filter_id                  BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  work_unit_id               BIGINT UNSIGNED NOT NULL,
  filter_name                VARCHAR(100) NOT NULL,
  observed_flux              FLOAT NOT NULL,
  observational_uncertainty  FLOAT NOT NULL,
  flux_bfm                   FLOAT NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE work_unit_parameter (
  parameter_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  work_unit_id BIGINT UNSIGNED NOT NULL,
  parameter_name     VARCHAR(100) NOT NULL,
  percentile2_5      FLOAT NOT NULL,
  percentile16       FLOAT NOT NULL,
  percentile50       FLOAT NOT NULL,
  percentile84       FLOAT NOT NULL,
  percentile97_5     FLOAT NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;


CREATE TABLE work_unit_histogram (
  histogram_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  parameter_id BIGINT UNSIGNED NOT NULL,
  x_axis      FLOAT NOT NULL,
  hist_value  FLOAT NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE INDEX work_unit_name_ix ON work_unit(point_name);
