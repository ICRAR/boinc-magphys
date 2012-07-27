from django.db import models

class Galaxy(models.Model):
    galaxy_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=384, unique=True)
    dimension_x = models.IntegerField()
    dimension_y = models.IntegerField()
    dimension_z = models.IntegerField()
    redshift = models.FloatField()
    class Meta:
        db_table = u'galaxy'
        
class Area(models.Model):
    area_id = models.BigIntegerField(primary_key=True)
    galaxy = models.ForeignKey(Galaxy, related_name='areas', on_delete=models.PROTECT)
    top_x = models.IntegerField(unique=True)
    top_y = models.IntegerField(unique=True)
    bottom_x = models.IntegerField(unique=True)
    bottom_y = models.IntegerField(unique=True)
    workunit_id = models.BigIntegerField(null=True, blank=True)
    class Meta:
        db_table = u'area'

class AreaUser(models.Model):
    areauser_id = models.BigIntegerField(primary_key=True)
    area = models.ForeignKey(Area, related_name='users', on_delete=models.PROTECT)
    userid = models.IntegerField()
    create_time = models.DateTimeField()
    class Meta:
        db_table = u'area_user'
        

class PixelResult(models.Model):
    pxresult_id = models.BigIntegerField()
    area = models.ForeignKey(Area, related_name='pixels', on_delete=models.PROTECT)
    galaxy = models.ForeignKey(Galaxy, related_name='pixels', on_delete=models.PROTECT)
    x = models.IntegerField(unique=True)
    y = models.IntegerField(unique=True)
    workunit_id = models.BigIntegerField(null=True, blank=True)
    i_sfh = models.FloatField(null=True, blank=True)
    i_ir = models.FloatField(null=True, blank=True)
    chi2 = models.FloatField(null=True, blank=True)
    redshift = models.FloatField(null=True, blank=True)
    fmu_sfh = models.FloatField(null=True, blank=True)
    fmu_ir = models.FloatField(null=True, blank=True)
    mu = models.FloatField(null=True, blank=True)
    tauv = models.FloatField(null=True, blank=True)
    s_sfr = models.FloatField(null=True, blank=True)
    m = models.FloatField(null=True, blank=True)
    ldust = models.FloatField(null=True, blank=True)
    t_w_bc = models.FloatField(null=True, blank=True)
    t_c_ism = models.FloatField(null=True, blank=True)
    xi_c_tot = models.FloatField(null=True, blank=True)
    xi_pah_tot = models.FloatField(null=True, blank=True)
    xi_mir_tot = models.FloatField(null=True, blank=True)
    x_w_tot = models.FloatField(null=True, blank=True)
    tvism = models.FloatField(null=True, blank=True)
    mdust = models.FloatField(null=True, blank=True)
    sfr = models.FloatField(null=True, blank=True)
    i_opt = models.FloatField(null=True, blank=True)
    dmstar = models.FloatField(null=True, blank=True)
    dfmu_aux = models.FloatField(null=True, blank=True)
    dz = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'pixel_result'

class PixelFilter(models.Model):
    pxfilter_id = models.BigIntegerField()
    pixelResult = models.ForeignKey(PixelResult, db_column='pxresult_id', related_name='filters', on_delete=models.PROTECT)
    filter_name = models.CharField(max_length=300)
    observed_flux = models.FloatField()
    observational_uncertainty = models.FloatField()
    flux_bfm = models.FloatField()
    class Meta:
        db_table = u'pixel_filter'

class PixelParameter(models.Model):
    pxparameter_id = models.BigIntegerField()
    pixelResult = models.ForeignKey(PixelResult, db_column='pxresult_id', related_name='parameters', on_delete=models.PROTECT)
    parameter_name = models.CharField(max_length=300)
    percentile2_5 = models.FloatField()
    percentile16 = models.FloatField()
    percentile50 = models.FloatField()
    percentile84 = models.FloatField()
    percentile97_5 = models.FloatField()
    class Meta:
        db_table = u'pixel_parameter'
        
class PixelHistogram(models.Model):
    pxhistogram_id = models.BigIntegerField()
    parameter = models.ForeignKey(PixelParameter, db_column='pxparameter_id', related_name='histograms', on_delete=models.PROTECT)
    pxresult_id = models.BigIntegerField()
    x_axis = models.FloatField()
    hist_value = models.FloatField()
    class Meta:
        db_table = u'pixel_histogram'

