DROP SCHEMA IF EXISTS magphys_as;
CREATE SCHEMA magphys_as;
USE magphys_as;

CREATE TABLE work_unit_result (
  wuresult_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  point_name  VARCHAR(100) NOT NULL,
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

CREATE TABLE work_unit_filter (
  wufilter_id                BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  wuresult_id                BIGINT UNSIGNED NOT NULL,
  filter_name                VARCHAR(100) NOT NULL,
  observed_flux              DOUBLE NOT NULL,
  observational_uncertainty  DOUBLE NOT NULL,
  flux_bfm                   DOUBLE NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE work_unit_parameter (
  wuparameter_id     BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  wuresult_id        BIGINT UNSIGNED NOT NULL,
  parameter_name     VARCHAR(100) NOT NULL,
  percentile2_5      DOUBLE NOT NULL,
  percentile16       DOUBLE NOT NULL,
  percentile50       DOUBLE NOT NULL,
  percentile84       DOUBLE NOT NULL,
  percentile97_5     DOUBLE NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;


CREATE TABLE work_unit_histogram (
  wuhistogram_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  wuparameter_id BIGINT UNSIGNED NOT NULL,
  x_axis         DOUBLE NOT NULL,
  hist_value     DOUBLE NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE work_unit_user (
  wuuser_id                  BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  wuresult_id                BIGINT UNSIGNED NOT NULL,
  userid                     INTEGER NOT NULL,
  create_time                TIMESTAMP
) CHARACTER SET utf8 ENGINE=InnoDB;

ALTER TABLE work_unit_filter ADD CONSTRAINT wufilter_result_fk FOREIGN KEY(wuresult_id) REFERENCES work_unit_result(wuresult_id);
ALTER TABLE work_unit_parameter ADD CONSTRAINT wuparameter_result_fk FOREIGN KEY(wuresult_id) REFERENCES work_unit_result(wuresult_id);
ALTER TABLE work_unit_histogram ADD CONSTRAINT wuhistogram_parameter_fk FOREIGN KEY(wuparameter_id) REFERENCES work_unit_parameter(wuparameter_id);
ALTER TABLE work_unit_user ADD CONSTRAINT wuuser_result_fk FOREIGN KEY(wuresult_id) REFERENCES work_unit_result(wuresult_id);

CREATE INDEX work_unit_name_ix ON work_unit_result(point_name);
