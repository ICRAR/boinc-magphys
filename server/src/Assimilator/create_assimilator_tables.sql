DROP SCHEMA IF EXISTS magphys_as;
CREATE SCHEMA magphys_as;
USE magphys_as;

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
