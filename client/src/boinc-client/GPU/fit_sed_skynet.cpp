// Comments prefixed with F77 are original Fortran code.

// {F77} c     ===========================================================================
// {F77}       PROGRAM FIT_SED
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Authors :   E. da Cunha & S. Charlot
// {F77} c     Latest revision :   Sep. 16th, 2010
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Model & Method descibed in detail in:
// {F77} c     da Cunha, Charlot & Elbaz, 2008, MNRAS 388, 1595
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Compares model fluxes with observed fluxes from the ultraviolet to the
// {F77} c     far-infrared by computing the chi^2 goodness-of-fit of each model.
// {F77} c     The probability of each model is exp(-1/2 chi^2)
// {F77} c     The code also builds the likelihood distribution of each parameter
// {F77} c
// {F77} c     INPUTS:
// {F77} c     - filter file - define USER_FILTERS in .galsbit_tcshrc
// {F77} c     - file with redshifts & observed fluxes of the
// {F77} c     galaxies - define USER_OBS in .magphys_tcshrc
// {F77} c     - file with redshifts at which libraries
// {F77} c     were computed "zlibs.dat"
// {F77} c     - .lbr files generated with get_optic_colors.f
// {F77} c     & get_infrared_colors.f
// {F77} c     - number of the galaxy to fit: i_gal
// {F77} c
// {F77} c     OUTPUTS: - "name".fit file containing:
// {F77} c     -- observed fluxes
// {F77} c     -- mininum chi2
// {F77} c     -- best-fit model parameters & fluxes
// {F77} c     -- likelihood distribution of each parameter
// {F77} c     -- 2.5th, 16th, 50th, 84th, 97.5th percentile
// {F77} c     of each parameter
// {F77} c     - "name".sed file containing the best-fit SED
// {F77} c     ===========================================================================
// {F77} 
// {F77} 
// {F77} c     ===========================================================================
// {F77} c     Author : Kevin Vinsen
// {F77} c    Date : 29th May 2012
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Added minor changes to allow the code to run from the command line and not
// {F77} c     to perform the normalisation against the models. Instead it writes the
// {F77} c     parameters required to normalise it later.
// {F77} c     The skyNet project is a citizen science project and we cannot expect the
// {F77} c     general public to download the 3 large .bin files
// {F77} c     ===========================================================================
// {F77} 

#include <iostream>
#include <fstream>
#include <sstream>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <string.h>

#define NMAX 50
#define GALMAX 5000
#define NMOD 50001
#define NPROP_SFH 24
#define NPROP_IR 8
#define NZMAX 5000
#define NBINMAX1 3000
#define NBINMAX2 300
#define MIN_HPBV 0.00001

//Function prototypes for old FORTRAN functions.
double get_cosmol_c(double h,double omega,double omega_lambda,double* q);
double get_funl(double x);
void get_midpnt(double (*func)(double),double a,double b,double* s,double n);
double get_dl(double h,double q,double z);
void sort2(double arr1[],double arr2[], int left, int right);
void get_histgrid(double dv,double vmin,double vmax,int* nbin,double vout[]);
void get_percentiles(int n,double par[],double probability[],double percentile[]);
void degrade_hist(double delta,double min,double max,int nbin1,int * nbin2,double hist1[], double hist2[],double prob1[],double prob2[]);
double get_hpbv(double hist1[],double hist2[],int nbin);

// TODO : Bad! Get rid of this eventually.
static double omega0;

using namespace std;


int main(int argc, char *argv[]){
// Mimic output to that of fortran write.
    cout.precision(15);
   // cout.setf(ios::scientific);

// {F77}       implicit none
// {F77}       integer isave,i,j,k,i_gal,io,largo
   int isave,i,j,k,i_gal,io,largo;
// {F77}       integer nmax,galmax,nmod
// {F77}       parameter(nmax=50,galmax=5000) !nmax: maxium number of photometric points/filters
// {F77}       integer n_obs,n_models,ibin  !galmax: maximum number of galaxies in one input file
   static int n_obs,n_models,ibin;
// {F77}       integer kfilt_sfh(nmax),kfilt_ir(nmax),nfilt_sfh,nfilt_ir,nfilt_mix
   static int kfilt_sfh[NMAX],kfilt_ir[NMAX],nfilt_sfh,nfilt_ir,nfilt_mix;
// {F77}       integer nprop_sfh,nprop_ir
// {F77}       integer n_sfh,n_ir,i_ir,i_sfh,ir_sav,sfh_sav
   static int n_sfh,n_ir,i_ir,i_sfh,ir_sav,sfh_sav;
// {F77}       integer nfilt,filt_id(nmax),fit(nmax),ifilt
   static int nfilt,filt_id[NMAX],fit[NMAX],ifilt;
// {F77}       parameter(nmod=50001,nprop_sfh=24,nprop_ir=8)
// {F77}       character*12 filt_name(nmax)
   static char filt_name[NMAX][12];
// {F77}       character*100 outfile1,outfile2
   static char outfile1[100],outfile2[100];
// {F77}       character*500 filter_header
   static char filter_header[500];
// {F77}       character*30 gal_name(galmax),aux_name
   static char gal_name[GALMAX][30],aux_name[30];
// {F77}       character*6 numz
   static char numz[7];
// {F77}       character optlib*34,irlib*26
   static char optlib[35],irlib[27];
// {F77}       character filters*80,obs*80
   static char filters[81],obs[81];
// {F77} c     redshift libs
// {F77}       integer nz,nzmax
   static int nz;
// {F77}       parameter(nzmax=5000)
// {F77}       real*8 zlib(nzmax),diffz(nzmax)
   static double zlib[NZMAX],diffz[NZMAX];
// {F77} c     observations, filters, etc.
// {F77}       real*8 w(galmax,nmax),redshift(galmax),dist(galmax)
   static double w[NMAX][GALMAX],redshift[GALMAX],dist[GALMAX];
// {F77}       real*8 flux_obs(galmax,nmax),sigma(galmax,nmax),aux
   static double flux_obs[NMAX][GALMAX],sigma[NMAX][GALMAX],aux;
// {F77}       real*8 flux_sfh(nmod,nmax),ssfr(nmod)
   static double flux_sfh[NMAX][NMOD],ssfr[NMOD];
// {F77}       real*8 lambda_eff(nmax),lambda_rest(nmax)
   static double lambda_eff[NMAX],lambda_rest[NMAX];
// {F77} c     model libraries, parameters, etc.
// {F77}       integer n_flux,indx(nmod)
   static int n_flux,indx[NMOD];
// {F77}       real*8 fprop_sfh(nmod,nprop_sfh),fmu_sfh(nmod)
   static double fprop_sfh[NPROP_SFH][NMOD],fmu_sfh[NMOD];
// {F77}       real*8 fprop_ir(nmod,nprop_ir),fmu_ir(nmod)
   static double fprop_ir[NPROP_IR][NMOD],fmu_ir[NMOD];
// {F77}       real*8 ldust(nmod),mstr1(nmod),logldust(nmod),lssfr(nmod)
   static double ldust[NMOD],mstr1[NMOD],logldust[NMOD],lssfr[NMOD];
// {F77}       real*8 flux_ir(nmod,nmax),tvism(nmod),tauv(nmod),mu(nmod)
   static double flux_ir[NMAX][NMOD],tvism[NMOD],tauv[NMOD],mu[NMOD];
// {F77}       real*8 tbg1(nmod),tbg2(nmod),xi1(nmod),xi2(nmod),xi3(nmod)
   static double tbg1[NMOD],tbg2[NMOD],xi1[NMOD],xi2[NMOD],xi3[NMOD];
// {F77}       real*8 fmu_ism(nmod),mdust(nmod),lmdust(nmod)
   static double fmu_ism[NMOD],mdust[NMOD],lmdust[NMOD];
// {F77} c     chi2, scaling factors, etc.
// {F77}       real*8 flux_mod(nmax)
   static double flux_mod[NMAX];
// {F77}       real*8 chi2,chi2_sav,chi2_new,df
   static double chi2,chi2_sav,chi2_new,df;
// {F77}       real*8 a,num,den,a_sav
   static double a,num,den,a_sav;
// {F77}       real*8 ptot,prob,chi2_new_opt,chi2_new_ir
   static double ptot,prob,chi2_new_opt,chi2_new_ir;
// {F77}       real*8 chi2_opt,chi2_ir,chi2_sav_opt,chi2_sav_ir
   static double chi2_opt,chi2_ir,chi2_sav_opt,chi2_sav_ir;
// {F77} c     histograms
// {F77}       real*8 fmu_min,fmu_max,dfmu
   static double fmu_min,fmu_max,dfmu;
// {F77}       real*8 ssfr_min,ssfr_max,dssfr
   static double ssfr_min,ssfr_max,dssfr;
// {F77}       real*8 fmuism_min,fmuism_max,dfmu_ism
   static double fmuism_min,fmuism_max,dfmu_ism;
// {F77}       real*8 mu_min,mu_max,dmu
   static double mu_min,mu_max,dmu;
// {F77}       real*8 tv_min,tv_max,dtv,dtvism
   static double tv_min,tv_max,dtv,dtvism;
// {F77}       real*8 sfr_min,sfr_max,dsfr
   static double sfr_min,sfr_max,dsfr;
// {F77}       real*8 a_min,a_max,da
   static double a_min,a_max,da;
// {F77}       real*8 md_min,md_max,dmd
   static double md_min,md_max,dmd;
// {F77}       real*8 ld_min,ld_max,dldust
   static double ld_min,ld_max,dldust;
// {F77}       real*8 tbg1_min,tbg1_max,dtbg,tbg2_min,tbg2_max
   static double tbg1_min,tbg1_max,dtbg,tbg2_min,tbg2_max;
// {F77}       real*8 xi_min,xi_max,dxi
   static double xi_min,xi_max,dxi;
// {F77}       real*8 pct_sfr(5),pct_fmu_sfh(5),pct_fmu_ir(5)
   static double pct_sfr[5],pct_fmu_sfh[5],pct_fmu_ir[5];
// {F77}       real*8 pct_mu(5),pct_tv(5),pct_mstr(5)
   static double pct_mu[5],pct_tv[5],pct_mstr[5];
// {F77}       real*8 pct_ssfr(5),pct_ld(5),pct_tbg2(5)
   static double pct_ssfr[5],pct_ld[5],pct_tbg2[5];
// {F77}       real*8 pct_tbg1(5),pct_xi1(5),pct_xi2(5)
   static double pct_tbg1[5],pct_xi1[5],pct_xi2[5];
// {F77}       real*8 pct_xi3(5),pct_tvism(5),pct_ism(5),pct_md(5)
   static double pct_xi3[5],pct_tvism[5],pct_ism[5],pct_md[5];
// {F77}       integer nbinmax1,nbinmax2
// {F77} c theSkyNet parameter (nbinmax1=1500,nbinmax2=150)
// {F77}       parameter (nbinmax1=3000,nbinmax2=300)
// {F77}       real*8 psfh2(nbinmax2),pir2(nbinmax2),pmu2(nbinmax2)
   static double psfh2[NBINMAX2],pir2[NBINMAX2],pmu2[NBINMAX2];
// {F77}       real*8 ptv2(nbinmax2),pxi2_2(nbinmax2),pssfr2(nbinmax2)
   static double ptv2[NBINMAX2],pxi2_2[NBINMAX2],pssfr2[NBINMAX2];
// {F77}       real*8 pa2(nbinmax2),pldust2(nbinmax2)
   static double pa2[NBINMAX2],pldust2[NBINMAX2];
// {F77}       real*8 ptbg1_2(nbinmax2),ptbg2_2(nbinmax2),pxi1_2(nbinmax2)
   static double ptbg1_2[NBINMAX2],ptbg2_2[NBINMAX2],pxi1_2[NBINMAX2];
// {F77}       real*8 ptvism2(nbinmax2),pism2(nbinmax2),pxi3_2(nbinmax2)
   static double ptvism2[NBINMAX2],pism2[NBINMAX2],pxi3_2[NBINMAX2];
// {F77}       real*8 fmuism2_hist(nbinmax2),md2_hist(nbinmax2)
   static double fmuism2_hist[NBINMAX2],md2_hist[NBINMAX2];
// {F77}       real*8 ssfr2_hist(nbinmax2),psfr2(nbinmax2),pmd_2(nbinmax2)
   static double ssfr2_hist[NBINMAX2],psfr2[NBINMAX2],pmd_2[NBINMAX2];
// {F77}       real*8 fmu2_hist(nbinmax2),mu2_hist(nbinmax2),tv2_hist(nbinmax2)
   static double fmu2_hist[NBINMAX2],mu2_hist[NBINMAX2],tv2_hist[NBINMAX2];
    
// {F77}       real*8 sfr2_hist(nbinmax2),a2_hist(nbinmax2),ld2_hist(nbinmax2)
   static double sfr2_hist[NBINMAX2],a2_hist[NBINMAX2],ld2_hist[NBINMAX2];
// {F77}       real*8 tbg1_2_hist(nbinmax2),tbg2_2_hist(nbinmax2),xi2_hist(nbinmax2)
   static double tbg1_2_hist[NBINMAX2],tbg2_2_hist[NBINMAX2],xi2_hist[NBINMAX2];
// {F77}       real*8 tvism2_hist(nbinmax2)
   static double tvism2_hist[NBINMAX2];
// {F77} c theSkyNet
// {F77} c     The highest probability bin values
// {F77}        real*8 hpbv, get_hpbv
   static double hpbv;
// {F77}        real*8 min_hpbv
// {F77}        parameter(min_hpbv = 0.00001)
// {F77} c theSkyNet
// {F77}       integer nbin_fmu,nbin_mu,nbin_tv,nbin_a,nbin2_tvism
   static int nbin_fmu,nbin_mu,nbin_tv,nbin_a,nbin2_tvism;
// {F77}       integer nbin_tbg1,nbin_tbg2,nbin_xi,nbin_sfr,nbin_ld
   static int nbin_tbg1,nbin_tbg2,nbin_xi,nbin_sfr,nbin_ld;
// {F77}       integer nbin2_fmu,nbin2_mu,nbin2_tv,nbin2_a,nbin_fmu_ism
   static int nbin2_fmu,nbin2_mu,nbin2_tv,nbin2_a,nbin_fmu_ism;
// {F77}       integer nbin2_fmu_ism,nbin_md,nbin2_md,nbin_ssfr,nbin2_ssfr
   static int nbin2_fmu_ism,nbin_md,nbin2_md,nbin_ssfr,nbin2_ssfr;
// {F77}       integer nbin2_tbg1,nbin2_tbg2,nbin2_xi,nbin2_sfr,nbin2_ld
   static int nbin2_tbg1,nbin2_tbg2,nbin2_xi,nbin2_sfr,nbin2_ld;
// {F77}       real*8 fmu_hist(nbinmax1),psfh(nbinmax1),pism(nbinmax1)
   static double fmu_hist[NBINMAX1],psfh[NBINMAX1],pism[NBINMAX1];
// {F77}       real*8 pir(nbinmax1),ptbg1(nbinmax1)
   static double pir[NBINMAX1],ptbg1[NBINMAX1];
// {F77}       real*8 mu_hist(nbinmax1),pmu(nbinmax1),ptbg2(nbinmax1)
   static double mu_hist[NBINMAX1],pmu[NBINMAX1],ptbg2[NBINMAX1];
// {F77}       real*8 tv_hist(nbinmax1),ptv(nbinmax1),ptvism(nbinmax1)
   static double tv_hist[NBINMAX1],ptv[NBINMAX1],ptvism[NBINMAX1];
// {F77}       real*8 sfr_hist(nbinmax1),psfr(nbinmax1),fmuism_hist(nbinmax1)
   static double sfr_hist[NBINMAX1],psfr[NBINMAX1],fmuism_hist[NBINMAX1];
// {F77}       real*8 pssfr(nbinmax1),a_hist(nbinmax1),pa(nbinmax1)
   static double pssfr[NBINMAX1],a_hist[NBINMAX1],pa[NBINMAX1];
// {F77}       real*8 ld_hist(nbinmax1),pldust(nbinmax1)
   static double ld_hist[NBINMAX1],pldust[NBINMAX1];
// {F77}       real*8 tbg1_hist(nbinmax1),tbg2_hist(nbinmax1)
   static double tbg1_hist[NBINMAX1],tbg2_hist[NBINMAX1];
// {F77}       real*8 ssfr_hist(nbinmax1),xi_hist(nbinmax1),pxi1(nbinmax1)
   static double ssfr_hist[NBINMAX1],xi_hist[NBINMAX1],pxi1[NBINMAX1];
// {F77}       real*8 pxi2(nbinmax1),pxi3(nbinmax1)
   static double pxi2[NBINMAX1],pxi3[NBINMAX1];
// {F77}       real*8 md_hist(nbinmax1),pmd(nbinmax1)
   static double md_hist[NBINMAX1],pmd[NBINMAX1];
// {F77}       real*8 i_fmu_sfh(nmod),i_fmu_ir(nmod)
   static double i_fmu_sfh[NMOD],i_fmu_ir[NMOD];
// {F77}       real*8 i_mu(nmod),i_tauv(nmod),i_tvism(nmod)
   static double i_mu[NMOD],i_tauv[NMOD],i_tvism[NMOD];
// {F77}       real*8 i_lssfr(nmod),i_fmu_ism(nmod)
   static double i_lssfr[NMOD],i_fmu_ism[NMOD];
// {F77}       real*8 i_tbg1(nmod),i_xi1(nmod),i_xi2(nmod),i_xi3(nmod)
   static double i_tbg1[NMOD],i_xi1[NMOD],i_xi2[NMOD],i_xi3[NMOD];
// {F77}       real*8 i_tbg2(nmod)
   static double i_tbg2[NMOD];
// {F77} c     cosmological parameters
// {F77}       real*8 h,omega,omega_lambda,clambda,q
   static double h,omega,omega_lambda,clambda,q;
// {F77}       real*8 cosmol_c,dl
   static double cosmol_c,dl;
// {F77} c     histogram parameters: min,max,bin width
// {F77}       data fmu_min/0./,fmu_max/1.0005/,dfmu/0.001/
    fmu_min=0,fmu_max=1.0005,dfmu=0.001;
// {F77}       data fmuism_min/0./,fmuism_max/1.0005/,dfmu_ism/0.001/
    fmuism_min=0,fmuism_max=1.0005,dfmu_ism=0.001;
// {F77}       data mu_min/0./,mu_max/1.0005/,dmu/0.001/
    mu_min=0,mu_max=1.0005,dmu=0.001;
// {F77}       data tv_min/0./,tv_max/6.0025/,dtv/0.005/
    tv_min=0,tv_max=6.0025,dtv=0.005;
// {F77}       data ssfr_min/-13./,ssfr_max/-5.9975/,dssfr/0.05/
    ssfr_min=-13,ssfr_max=-5.9975,dssfr=0.05;
// {F77} c theSkyNet data sfr_min/-3./,sfr_max/3.5005/,dsfr/0.005/
// {F77} c theSkyNet data a_min/7./,a_max/13.0025/,da/0.005/
// {F77} c theSkyNet data ld_min/7./,ld_max/13.0025/,dldust/0.005/
// {F77}       data sfr_min/-8./,sfr_max/3.5005/,dsfr/0.005/
    sfr_min=-8,sfr_max=3.5005,dsfr=0.005;
// {F77}       data a_min/2./,a_max/13.0025/,da/0.005/
    a_min=2,a_max=13.0025,da=0.005;
// {F77}       data ld_min/2./,ld_max/13.0025/,dldust/0.005/
    ld_min=2,ld_max=13.0025,dldust=0.005;
// {F77}       data tbg1_min/30./,tbg1_max/60.0125/,dtbg/0.025/
    tbg1_min=30,tbg1_max=60.0125,dtbg=0.025;
// {F77}       data tbg2_min/15./,tbg2_max/25.0125/
    tbg2_min=15,tbg2_max=25.0125;
// {F77}       data xi_min/0./,xi_max/1.0001/,dxi/0.001/
    xi_min=0,xi_max=1.0001,dxi=0.001;
// {F77} c theSkyNet data md_min/3./,md_max/9./,dmd/0.005/
// {F77}       data md_min/-2./,md_max/9./,dmd/0.005/
    md_min=-2,md_max=9,dmd=0.005;
// {F77} c     cosmology
// {F77}       data h/70./,omega/0.30/,omega_lambda/0.70/
    h=70,omega=0.30,omega_lambda=0.70;
// {F77}       data isave/0/
    isave=0;

// {F77} c     save parameters
// {F77}       save flux_ir,flux_sfh,fmu_ir,fmu_sfh
// {F77}       save mstr1,ssfr,ldust,mu,tauv,fmu_ism
// {F77}       save lssfr,logldust,tvism
// {F77}       save tbg1,tbg2,xi1,xi2,xi3
// {F77}       save flux_obs,sigma,dist
// {F77}       save mdust
// {F77} 
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Are we in skynet mode
// {F77} c     ---------------------------------------------------------------------------
// {F77}       integer numargs
// {F77}       character*80 arg
// {F77}       logical skynet
    static bool skynet;
// {F77}       integer ios
// {F77}       character*100 buffer1, buffer2
// {F77}       logical found_old_entry
// {F77}       integer gal_number_found
// {F77} 
// {F77}       numargs = iargc ( )
// {F77}       if (numargs .eq. 0) then
   if(argc == 1){
// {F77} c     Do nothing as this is the normal model
// {F77}           skynet = .FALSE.
        skynet = false;
// {F77}       else if (numargs .eq. 3) then
   } else if(argc == 4){
// {F77}           skynet = .TRUE.
        skynet = true;
// {F77}           call getarg ( 1, arg )
// {F77}           read( arg, *) i_gal
        // We subtract 1 from i_gal to suit C standard array indexing.
        i_gal = atoi(argv[1])-1;
// {F77}           call getarg( 2, filters)
        strcpy(filters,argv[2]);
// {F77}           call getarg( 3, obs)
        strcpy(obs,argv[3]);
// {F77}       else
    } else{
// {F77}         write(*,*) "Requires arguments: pixel to fit, filters file, observations file"
        cout << "Requires arguments: pixel to fit, filters file, observations file" << endl; 
// {F77} 		call EXIT(-1)
        exit(-1);
// {F77} 	  endif
    }
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Set things up: what filters to use, observations and models:
// {F77} c     ---------------------------------------------------------------------------
// {F77} 
// {F77} c     READ FILTER FILE: "filters.dat"
// {F77}       if (skynet .eqv. .FALSE.) then
// {F77}           call getenv('USER_FILTERS',filters)
// {F77}       endif
    char * env;
    if(!skynet){
        env = getenv("USER_FILTERS");
        if(env){
            strcpy(filters,env);
        } else {
            exit(-1);
        }
    }
// {F77}       close(22)
// {F77}       open(22,file=filters,status='old')
// {F77}       do i=1,1
// {F77}          read(22,*)
// {F77}       enddo
// {F77}       io=0
// {F77}       ifilt=0
// {F77}       do while(io.eq.0)
// {F77}          ifilt=ifilt+1
// {F77}          read(22,*,iostat=io) filt_name(ifilt),lambda_eff(ifilt),filt_id(ifilt),fit(ifilt)
// {F77}       enddo
// {F77}       nfilt=ifilt-1
// {F77}       close(22)
    ifstream infs;
    infs.open(filters);
    if(!infs.is_open()){
        cerr << "Error opening filters file: " << filters << endl;
        exit(-1);
    }
    stringstream ss;
    nfilt=0;
    string line;
    while(getline(infs,line)){
        if(line[0] != '#'){
            ss.str("");
            ss.clear();
            ss << line;
            ss >> filt_name[nfilt] >> lambda_eff[nfilt] >> filt_id[nfilt] >> fit[nfilt];
            nfilt++;
        }
    }
    infs.close();
// {F77} 
// {F77} c     READ FILE WITH OBSERVATIONS:
// {F77}       if (skynet .eqv. .FALSE.) then
// {F77}           call getenv('USER_OBS',obs)
// {F77}       endif
    if(!skynet){
        env = getenv("USER_OBS");
        if(env){
            strcpy(obs,env);
        }
    }
// {F77}       close(20)
// {F77}       open(20,file=obs,status='old')
// {F77}       do i=1,1
// {F77}          read(20,*)
// {F77}       enddo
// {F77}       io=0stringstream format
// {F77}       n_obs=0
// {F77}       do while(io.eq.0)
// {F77}          n_obs=n_obs+1
// {F77}          read(20,*,iostat=io) gal_name(n_obs),redshift(n_obs),
// {F77}      +        (flux_obs(n_obs,k),sigma(n_obs,k),k=1,nfilt)
// {F77}       enddo
// {F77}       n_obs=n_obs-1
// {F77}       close(20)
    infs.open(obs);
    if(!infs.is_open()){
        cerr << "Error opening observations file: " << obs << endl;
        exit(-1);
    }
    n_obs=0;
    while(getline(infs,line)){
        if(line[0] != '#'){
           ss.str("");
           ss.clear();
           ss << line;
           ss >> gal_name[n_obs] >> redshift[n_obs]; 
           for(k=0; k < nfilt; k++){
                ss >> flux_obs[k][n_obs] >> sigma[k][n_obs];
           }
           n_obs++;
        }
    }
    infs.close();

// {F77} 
// {F77} c     READ FILE WITH REDSHIFTS OF THE MODEL LIBRARIES
// {F77}       close(24)
// {F77}       open(24,file='zlibs.dat',status='old')
// {F77}       io=0
// {F77}       nz=0
// {F77}       do while(io.eq.0)
// {F77}          nz=nz+1
// {F77}          read(24,*,iostat=io) i,zlib(nz)
// {F77}          enddo
// {F77}          nz=nz-1
// {F77}       close(24)
// {F77} 
    infs.open("zlibs.dat");
    if(!infs.is_open()){
        cerr << "Error opening zlibs.dat" << endl;
        exit(-1);
    }
    nz=0;
    while(getline(infs,line)){
        if(line[0] != '#'){
           ss.str("");
           ss.clear();
           ss << line;
           ss >> i >> zlib[nz]; 
           nz++;
        }
    }
    infs.close();
// {F77} c     CHOOSE GALAXY TO FIT (enter corresponding i)
// {F77}       if (skynet .eqv. .FALSE.) then
// {F77}           write (6,'(x,a,$)') 'Choose galaxy - enter i_gal: '
// {F77}           read (5,*) i_gal
// {F77}       endif
// {F77}       write(*,*) i_gal, n_obs
    if(!skynet){
        // TODO: Take input
    }
    cout << i_gal+1 << "\t" << n_obs << endl;
// {F77} 
// {F77} c     Do we have the observation
// {F77}       if (i_gal .gt. n_obs) then
// {F77}          write(*,*) 'Observation does not exist'
// {F77}          call EXIT(0)
// {F77}       endif
    if(i_gal+1 > n_obs){
        cerr << "Observation does not exist" << endl;
        exit(-1);
    }
// {F77} 
// {F77} c     WHAT OBSERVATIONS DO YOU WANT TO FIT?
// {F77} c     fit(ifilt)=1: fit flux from filter ifilt
// {F77} c     fit(ifilt)=0: do not fit flux from filter ifilt (set flux=-99)
// {F77}       do ifilt=1,nfilt
// {F77}          if (fit(ifilt).eq.0) then
// {F77}             flux_obs(i_gal,ifilt)=-99.
// {F77}             sigma(i_gal,ifilt)=-99.
// {F77}          endif
// {F77}       enddo
    for(ifilt=0; ifilt < nfilt; ifilt++){
        if(fit[ifilt] == 0){
            flux_obs[ifilt][i_gal]=-99;
            sigma[ifilt][i_gal]=-99;
        }
    }
// {F77} 
// {F77} c     Count number of non-zero fluxes (i.e. detections) to fit
// {F77}       n_flux=0
// {F77}       do k=1,nfilt
// {F77}          if (flux_obs(i_gal,k).gt.0) then
// {F77}             n_flux=n_flux+1
// {F77}          endif
// {F77}       enddo
    n_flux=0;
    for(k=0; k < nfilt; k++){
        if(flux_obs[k][i_gal] > 0){
            n_flux++;
        }
    }
// {F77} 
// {F77} c theSkyNet
// {F77}          write(*,*) 'n_flux =',n_flux
// {F77}       if (n_flux < 4) then
// {F77}          call EXIT(0)
// {F77}       endif
    cout << "n_flux = " << n_flux << endl;
    if(n_flux < 4){
        exit(-1);
    }
// {F77} c theSkyNet
// {F77} 
// {F77} c     COMPUTE LUMINOSITY DISTANCE from z given cosmology
// {F77} c     Obtain cosmological constant and q
// {F77}       clambda=cosmol_c(h,omega,omega_lambda,q)
   clambda=get_cosmol_c(h,omega,omega_lambda,&q);
// {F77} 
// {F77} c     Compute distance in Mpc from the redshifts z
// {F77}       dist(i_gal)=dl(h,q,redshift(i_gal))
// {F77}       dist(i_gal)=dist(i_gal)*3.086e+24/dsqrt(1.+redshift(i_gal))
    dist[i_gal]=get_dl(h,q,redshift[i_gal]);
    dist[i_gal]=dist[i_gal]*(3.086e+24)/sqrt(1+redshift[i_gal]);
// {F77} 
// {F77} 
// {F77} c     OUTPUT FILES
// {F77} c     name.fit: fit results, PDFs etc
// {F77} c     name.sed: best-fit SED
// {F77}       aux_name=gal_name(i_gal)
// {F77}       close(31)
// {F77} c     ---------------------------------------------------------------------------
// {F77}       if (skynet .eqv. .FALSE.) then
// {F77} 	      outfile1=aux_name(1:largo(aux_name))//'.fit'
// {F77} 	      outfile2=aux_name(1:largo(aux_name))//'.sed'
// {F77} 	      open (31, file=outfile1, status='unknown')
// {F77} c     ---------------------------------------------------------------------------
// {F77}       else
// {F77}           write(outfile1, '(I0,a)') i_gal, '.fit'
// {F77}           open (31, file=outfile1, status='unknown')
// {F77}           write(31, *) '####### ',gal_name(i_gal)
// {F77}       endif
    strcpy(aux_name,gal_name[i_gal]);
    FILE * fitfp;

    if (!skynet){
        // TODO : Handle manual
    } else {
        sprintf(outfile1, "%d.fit",i_gal+1);
        fitfp = fopen(outfile1,"w");
        if(!fitfp){
            cerr << "Could not open fit file: " << outfile1 << endl;
        }
        fprintf(fitfp," ####### %s\n",gal_name[i_gal]);
    }
// {F77} 
// {F77} c     Choose libraries according to the redshift of the source
// {F77} c     Find zlib(i) closest of the galaxie's redshift
// {F77}       do i=1,nz
// {F77}          diffz(i)=abs(zlib(i)-redshift(i_gal))
// {F77}       enddo
    for(i=0; i<nz; i++){
        diffz[i]=fabs(zlib[i]-redshift[i_gal]);
    }
// {F77}       call sort2(nz,diffz,zlib)
    sort2(diffz,zlib,0,nz-1);
// {F77} c     diff(1): minimum difference
// {F77} c     zlib(1): library z we use for this galaxy
// {F77} c              (if diffz(1) not gt 0.005)
// {F77}       if (diffz(1).gt.0.005.and.mod(redshift(i_gal)*1000,10.).ne.5) then
// {F77}          write(*,*) 'No model library at this galaxy redshift...'
// {F77}          stop
// {F77}       endif
    if(diffz[0] > 0.005 && fmod(redshift[i_gal]*1000,10) != 5){
        cerr << "No model library at this galaxy redshift..." << endl;
        exit(-1);
    }
// {F77} 
// {F77}       write(numz,'(f6.4)') zlib(1)
// {F77}       optlib = 'starformhist_cb07_z'//numz//'.lbr'
// {F77}       irlib = 'infrared_dce08_z'//numz//'.lbr'
// {F77} 
// {F77}       write(*,*) 'z= ',redshift(i_gal)
// {F77}       write(*,*) 'optlib=',optlib
// {F77}       write(*,*) 'irlib=',irlib

    snprintf(numz, 7, "%f6.4",zlib[0]);
    snprintf(optlib, 35, "starformhist_cb07_z%s.lbr",numz);
    snprintf(irlib, 27, "infrared_dce08_z%s.lbr",numz);

    cout << "z = " << redshift[i_gal] << endl;
    cout << "optlib = " << optlib << endl;
    cout << "irlib = " << irlib <<endl;
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     What part of the SED are the filters sampling at the redshift of the galaxy?
// {F77} c     - lambda(rest-frame) < 2.5 mic : emission purely stellar (attenuated by dust)
// {F77} c     - 2.5 mic < lambda(rest-frame) < 10 mic : stellar + dust emission
// {F77} c     - lambda(rest-frame) > 10 mic : emission purely from dust
// {F77} c     ---------------------------------------------------------------------------
// {F77} 
// {F77}          nfilt_sfh=0            !nr of filters sampling the stellar emission
// {F77}          nfilt_ir=0             !nr of filters sampling the dust emission
// {F77}          nfilt_mix=0            !nr of filters sampling stellar+dust emission
// {F77}          do i=1,nfilt
// {F77}             lambda_rest(i)=lambda_eff(i)/(1.+redshift(i_gal))
// {F77}             if (lambda_rest(i).lt.10.) then
// {F77}                nfilt_sfh=nfilt_sfh+1
// {F77}                kfilt_sfh(nfilt_sfh)=i
// {F77}             endif
// {F77}             if (lambda_rest(i).gt.2.5) then
// {F77}                nfilt_ir=nfilt_ir+1
// {F77}                kfilt_ir(nfilt_ir)=i
// {F77}             endif
// {F77}             if (lambda_rest(i).gt.2.5.and.lambda_rest(i).le.10) then
// {F77}                nfilt_mix=nfilt_mix+1
// {F77}             endif
// {F77}          enddo
// {F77} 
// {F77}          write(*,*) '   '
// {F77}          write(*,*) 'At this redshift: '
    nfilt_sfh = nfilt_ir = nfilt_mix = 0;
    for(i=0; i<nfilt; i++){
        lambda_rest[i] = lambda_eff[i]/(1+redshift[i_gal]);
        if(lambda_rest[i] < 10){
            kfilt_sfh[nfilt_sfh]=i;
            nfilt_sfh++;
        }
        if(lambda_rest[i] > 2.5){
            kfilt_ir[nfilt_ir]=i;
            nfilt_ir++;
        }
        if (lambda_rest[i] > 2.5 && lambda_rest[i] <= 10){
            nfilt_mix++;
        }
    }
    cout << "   " << endl;   
    cout << "At this redshift: " << endl;
// {F77} 
// {F77}          do k=1,nfilt_sfh-nfilt_mix
// {F77}             write(*,*) 'purely stellar... ',filt_name(k)
// {F77}          enddo
// {F77}          do k=nfilt_sfh-nfilt_mix+1,nfilt_sfh
// {F77}             write(*,*) 'mix stars+dust... ',filt_name(k)
// {F77}          enddo
// {F77}          do k=nfilt_sfh+1,nfilt
// {F77}             write(*,*) 'purely dust... ',filt_name(k)
// {F77}          enddo
    for(k=0; k < (nfilt_sfh-nfilt_mix); k++){
        cout << "purely stellar... " << filt_name[k] << endl;
    }

    for(k=nfilt_sfh-nfilt_mix; k < nfilt_sfh; k++){
        cout << "mix stars+dust... " << filt_name[k] << endl;
    }
    for(k=nfilt_sfh; k < nfilt; k++){
        cout << "purely dust... " << filt_name[k] << endl;
    }
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     MODELS: read libraries of models with parameters + AB mags at z
// {F77} c     attenuated stellar emission - optlib: starformhist_cb07_z###.lbr
// {F77} c     --> nfilt_sfh model absolute AB mags
// {F77} c     dust emission - irlib: infrared_dce08_z###.lbr
// {F77} c     --> nfilt_ir model absolute AB mags
// {F77} c     ---------------------------------------------------------------------------
// {F77} 
// {F77}          if (isave.eq.0) then
// {F77}             io=0
    if(isave == 0){
// {F77} 
// {F77} c     READ OPTLIB
// {F77}             close(21)
// {F77}             open(21,file=optlib,status='old')
// {F77}             do i=1,2
// {F77}                read(21,*) !2 lines of header
// {F77}             enddo
// {F77}             write(*,*) 'Reading SFH library...'
// {F77}             i_sfh=0
// {F77}             io=0
// {F77}             do while(io.eq.0)
// {F77}                i_sfh=i_sfh+1
// {F77}                read(21,*,iostat=io) indx(i_sfh),(fprop_sfh(i_sfh,j),j=1,nprop_sfh),
// {F77}      +              (flux_sfh(i_sfh,j),j=1,nfilt_sfh)
// {F77}                if (io.eq.0) then
// {F77} c     Relevant physical parameters
// {F77}                   fmu_sfh(i_sfh)=fprop_sfh(i_sfh,22)            ! fmu parameter Ld(ISM)/Ld(tot) - optical
// {F77}                   mstr1(i_sfh)=fprop_sfh(i_sfh,6)               ! stellar mass
// {F77}                   ldust(i_sfh)=fprop_sfh(i_sfh,21)/mstr1(i_sfh) ! total luminosity of dust (normalize to Mstar)
// {F77}                   logldust(i_sfh)=dlog10(ldust(i_sfh))          ! log(Ldust)
// {F77}                   mu(i_sfh)=fprop_sfh(i_sfh,5)                  ! mu parameter (CF00 model)
// {F77}                   tauv(i_sfh)=fprop_sfh(i_sfh,4)                ! optical V-band depth tauV (CF00 model)
// {F77}                   ssfr(i_sfh)=fprop_sfh(i_sfh,10)/mstr1(i_sfh)  ! recent SSFR_0.01Gyr / stellar mass
// {F77}                   lssfr(i_sfh)=dlog10(ssfr(i_sfh))              ! log(SSFR_0.01Gyr)
// {F77}                   tvism(i_sfh)=mu(i_sfh)*tauv(i_sfh)            ! mu*tauV=V-band optical depth for ISM
// {F77} c     .lbr contains absolute AB magnitudes -> convert to fluxes Fnu in Lo/Hz
// {F77} c     Convert all magnitudes to Lo/Hz (except H lines luminosity: in Lo)
// {F77} c     Normalise SEDs to stellar mass
// {F77}                   do k=1,nfilt_sfh
// {F77}                      flux_sfh(i_sfh,k)=3.117336e+6
// {F77}      +                    *10**(-0.4*(flux_sfh(i_sfh,k)+48.6))
// {F77}                      flux_sfh(i_sfh,k)=flux_sfh(i_sfh,k)/mstr1(i_sfh)
// {F77} c     1+z factor which is required in model fluxes
// {F77}                      flux_sfh(i_sfh,k)=flux_sfh(i_sfh,k)/(1+redshift(i_gal))
// {F77}                   enddo
// {F77}                endif
// {F77}             enddo
// {F77}             close(21)
// {F77}             n_sfh=i_sfh-1
        infs.open(optlib);
        if(!infs.is_open()){
            cerr << "Failed to open SFH library: " << optlib << endl;
            exit(-1);
        }
        cout << "Reading SFH library..." << endl;
        n_sfh=0;
        while(getline(infs,line)){
            if(line[0] != '#'){
               ss.str("");
               ss.clear();
               ss << line;
               ss >> indx[n_sfh]; 
               for(j=0; j < NPROP_SFH; j++){
                    ss >> fprop_sfh[j][n_sfh];
               }
               for(j=0; j < nfilt_sfh; j++){
                    ss >> flux_sfh[j][n_sfh];
               }

               // We need to subtract array index by 1 due to fortran difference.
               fmu_sfh[n_sfh]=fprop_sfh[22-1][n_sfh];
               mstr1[n_sfh]=fprop_sfh[6-1][n_sfh]; 
               ldust[n_sfh]=fprop_sfh[21-1][n_sfh]/mstr1[n_sfh];
               logldust[n_sfh]=log10(ldust[n_sfh]);
               mu[n_sfh]=fprop_sfh[5-1][n_sfh];
               tauv[n_sfh]=fprop_sfh[4-1][n_sfh]; 
               ssfr[n_sfh]=fprop_sfh[10-1][n_sfh]/mstr1[n_sfh];
               lssfr[n_sfh]=log10(ssfr[n_sfh]);
               tvism[n_sfh]=mu[n_sfh]*tauv[n_sfh];

               for(k=0; k < nfilt_sfh; k++){
                 flux_sfh[k][n_sfh]=3.117336e+6*pow(10,-0.4*(flux_sfh[k][n_sfh]+48.6));
                 flux_sfh[k][n_sfh]=flux_sfh[k][n_sfh]/mstr1[n_sfh];
                 flux_sfh[k][n_sfh]=flux_sfh[k][n_sfh]/(1+redshift[i_gal]);
               }
               n_sfh++;
            }
        }
        infs.close();
// {F77} 
// {F77} c     READ IRLIB
// {F77}             close(20)
// {F77}             open(20,file=irlib,status='old')
// {F77}             do i=1,2
// {F77}                read(20,*)  !2 lines of header
// {F77}             enddo
// {F77}             write(*,*) 'Reading IR dust emission library...'
// {F77}             i_ir=0
// {F77}             io=0
// {F77}             do while(io.eq.0)
// {F77}                i_ir=i_ir+1
// {F77}                read(20,*,iostat=io) (fprop_ir(i_ir,j),j=1,nprop_ir),
// {F77}      +              (flux_ir(i_ir,j),j=1,nfilt_ir)
// {F77} c     IR model parameters
// {F77}                fmu_ir(i_ir)=fprop_ir(i_ir,1)       ! fmu parameter Ld(ISM)/Ld(tot) - infrared
// {F77}                fmu_ism(i_ir)=fprop_ir(i_ir,2)      ! xi_C^ISM [cont. cold dust to Ld(ISM)]
// {F77}                tbg2(i_ir)=fprop_ir(i_ir,4)         ! T_C^ISM [eq. temp. cold dust in ISM]
// {F77}                tbg1(i_ir)=fprop_ir(i_ir,3)         ! T_W^BC [eq. temp. warm dust in birth clouds]
// {F77}                xi1(i_ir)=fprop_ir(i_ir,5)          ! xi_PAH^BC Ld(PAH)/Ld(BC)
// {F77}                xi2(i_ir)=fprop_ir(i_ir,6)          ! xi_MIR^BC Ld(MIR)/Ld(BC)
// {F77}                xi3(i_ir)=fprop_ir(i_ir,7)          ! xi_W^BC Ld(warm)/Ld(BC)
// {F77}                mdust(i_ir)=fprop_ir(i_ir,8) !dust mass
// {F77} c     .lbr contains absolute AB magnitudes -> convert to fluxes Fnu in Lo/Hz
// {F77} c     Convert all magnitudes to Lo/Hz
// {F77}                do k=1,nfilt_ir
// {F77}                   flux_ir(i_ir,k)=3.117336e+6
// {F77}      +                 *10**(-0.4*(flux_ir(i_ir,k)+48.6))
// {F77}                   flux_ir(i_ir,k)=flux_ir(i_ir,k)/(1+redshift(i_gal))
// {F77}                enddo
// {F77} c     Re-define IR parameters: xi^tot
// {F77}                xi1(i_ir)=xi1(i_ir)*(1.-fmu_ir(i_ir))+
// {F77}      +              0.550*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_PAH^tot Ld(PAH)/Ld(tot)
// {F77}                xi2(i_ir)=xi2(i_ir)*(1.-fmu_ir(i_ir))+
// {F77}      +              0.275*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_MIR^tot Ld(MIR)/Ld(tot)
// {F77}                xi3(i_ir)=xi3(i_ir)*(1.-fmu_ir(i_ir))+
// {F77}      +              0.175*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_W^tot Ld(warm)/Ld(tot)
// {F77}                fmu_ism(i_ir)=fmu_ism(i_ir)*fmu_ir(i_ir)  ! xi_C^tot Ld(cold)/Ld(tot)
// {F77}             enddo
// {F77}  201        format(0p7f12.3,1pe12.3,1p14e12.3,1p3e12.3)
// {F77}             close(20)
// {F77}             n_ir=i_ir-1
        infs.open(irlib);
        if(!infs.is_open()){
            cerr << "Failed to open IR dust emission library: " << irlib << endl;
            exit(-1);
        }
        cout << "Reading IR dust emission library..." << endl;
        n_ir=0;
        while(getline(infs,line)){
            if(line[0] != '#'){
               ss.str("");
               ss.clear();
               ss << line;
               for(j=0; j < NPROP_IR; j++){
                    ss >> fprop_ir[j][n_ir];
               }
               for(j=0; j < nfilt_ir; j++){
                    ss >> flux_ir[j][n_ir];
               }

               // We need to subtract array index by 1 due to fortran difference.
               fmu_ir[n_ir]=fprop_ir[1-1][n_ir];
               fmu_ism[n_ir]=fprop_ir[2-1][n_ir];
               tbg2[n_ir]=fprop_ir[4-1][n_ir];
               tbg1[n_ir]=fprop_ir[3-1][n_ir];
               xi1[n_ir]=fprop_ir[5-1][n_ir];
               xi2[n_ir]=fprop_ir[6-1][n_ir];
               xi3[n_ir]=fprop_ir[7-1][n_ir];
               mdust[n_ir]=fprop_ir[8-1][n_ir];
               
               for(k=0; k < nfilt_ir; k++){
                 flux_ir[k][n_ir]=3.117336e+6*pow(10,-0.4*(flux_ir[k][n_ir]+48.6));
                 flux_ir[k][n_ir]=flux_ir[k][n_ir]/(1+redshift[i_gal]);
               }

               xi1[n_ir]=xi1[n_ir]*(1-fmu_ir[n_ir])+0.550*(1-fmu_ism[n_ir])*fmu_ir[n_ir];
               xi2[n_ir]=xi2[n_ir]*(1-fmu_ir[n_ir])+0.275*(1-fmu_ism[n_ir])*fmu_ir[n_ir];
               xi3[n_ir]=xi3[n_ir]*(1-fmu_ir[n_ir])+0.175*(1-fmu_ism[n_ir])*fmu_ir[n_ir];
               fmu_ism[n_ir]=fmu_ism[n_ir]*fmu_ir[n_ir]; 

               n_ir++;
            }
        }
        infs.close();
// {F77}             isave=1
// {F77}          endif
        isave=1;
    }
    
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     COMPARISON BETWEEN MODELS AND OBSERVATIONS:
// {F77} c
// {F77} c     Compare everything in the sample units:
// {F77} c     Lnu (i.e. luminosity per unit frequency) in Lsun/Hz
// {F77} c
// {F77} c     Model fluxes: already converted from AB mags to Lnu in Lsun/Hz
// {F77} c     Fluxes and physical parameters from optical library per unit Mstar=1 Msun
// {F77} c     Fluxes and physical parameters from infrared library per unit Ldust=1 Lsun
// {F77} c
// {F77} c     Observed fluxes & uncertainties
// {F77} c     Convert from Fnu in Jy to Lnu in Lo/Hz [using luminosity distance dist(i_gal)]
// {F77} c     ---------------------------------------------------------------------------
// {F77} 
// {F77} c     Observed fluxes: Jy -> Lsun/Hz
// {F77}          do k=1,nfilt
// {F77}             if (flux_obs(i_gal,k).gt.0) then
// {F77}                flux_obs(i_gal,k)=flux_obs(i_gal,k)*1.e-23
// {F77}      +              *3.283608731e-33*(dist(i_gal)**2)
// {F77}                sigma(i_gal,k)=sigma(i_gal,k)*1.e-23
// {F77}      +              *3.283608731e-33*(dist(i_gal)**2)
// {F77}             endif
// {F77}             if (sigma(i_gal,k).lt.0.05*flux_obs(i_gal,k)) then
// {F77}                sigma(i_gal,k)=0.05*flux_obs(i_gal,k)
// {F77}             endif
// {F77}          enddo
// {F77} 
// {F77}          do k=1,nfilt
// {F77}             if (sigma(i_gal,k).gt.0.0) then
// {F77}                w(i_gal,k) = 1.0 / (sigma(i_gal,k)**2)
// {F77}             endif
// {F77}          enddo
    for(k=0; k<nfilt; k++){
        if (flux_obs[k][i_gal] > 0){
            flux_obs[k][i_gal]=flux_obs[k][i_gal]*1.0e-23*3.283608731e-33*pow(dist[i_gal],2);
            sigma[k][i_gal]=sigma[k][i_gal]*1.0e-23*3.283608731e-33*pow(dist[i_gal],2);
        } 
        if (sigma[k][i_gal] < 0.05*flux_obs[k][i_gal]){
            sigma[k][i_gal]=0.05*flux_obs[k][i_gal];
        }
    }
    for(k=0; k<nfilt; k++){
        if (sigma[k][i_gal] > 0.0){
            w[k][i_gal] = 1.0/(pow(sigma[k][i_gal],2));
        }
    }
    
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Initialize variables:
// {F77}          n_models=0
// {F77}          chi2_sav=1.e+30
// {F77}          ptot=0.
// {F77}          prob=0.
// {F77}          do k=1,nfilt
// {F77}             flux_mod(k)=0.
// {F77}          enddo
    n_models=0;
    chi2_sav=1.0e30;
    ptot=0;
    prob=0;
    for(k=0; k<nfilt; k++){
        flux_mod[k]=0;
    }
// {F77} 
// {F77} c theSkyNet do i=1,1500
// {F77}          do i=1,3000
// {F77}             psfh(i)=0.
// {F77}             pir(i)=0.
// {F77}             pmu(i)=0.
// {F77}             ptv(i)=0.
// {F77}             ptvism(i)=0.
// {F77}             pssfr(i)=0.
// {F77}             psfr(i)=0.
// {F77}             pa(i)=0.
// {F77}             pldust(i)=0.
// {F77}             ptbg1(i)=0.
// {F77}             ptbg2(i)=0.
// {F77}             pism(i)=0.
// {F77}             pxi1(i)=0.
// {F77}             pxi2(i)=0.
// {F77}             pxi3(i)=0.
// {F77}             pmd(i)=0.
// {F77}          enddo
    for(i=0; i<3000; i++){
        psfh[i]=0;
        pir[i]=0;
        pmu[i]=0;
        ptv[i]=0;
        ptvism[i]=0;
        pssfr[i]=0;
        psfr[i]=0;
        pa[i]=0;
        pldust[i]=0;
        ptbg1[i]=0;
        ptbg2[i]=0;
        pism[i]=0;
        pxi1[i]=0;
        pxi2[i]=0;
        pxi3[i]=0;
        pmd[i]=0;
    }      
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Compute histogram grids of the parameter likelihood distributions before
// {F77} c     starting the big loop in which we compute chi^2 for each allowed combination
// {F77} c     of stellar+dust emission model (to save time).
// {F77} c
// {F77} c     The high-resolution marginalized likelihood distributions will be
// {F77} c     computed on-the-run
// {F77} c     ---------------------------------------------------------------------------
// {F77} 
// {F77} c     f_mu (SFH) & f_mu (IR)
// {F77}          call get_histgrid(dfmu,fmu_min,fmu_max,nbin_fmu,fmu_hist)
    get_histgrid(dfmu,fmu_min,fmu_max,&nbin_fmu,fmu_hist);
// {F77} c     mu parameter
// {F77}          call get_histgrid(dmu,mu_min,mu_max,nbin_mu,mu_hist)
    get_histgrid(dmu,mu_min,mu_max,&nbin_mu,mu_hist);
// {F77} c     tauv (dust optical depth)
// {F77}          call get_histgrid(dtv,tv_min,tv_max,nbin_tv,tv_hist)
    get_histgrid(dtv,tv_min,tv_max,&nbin_tv,tv_hist);
// {F77} c     sSFR
// {F77}          call get_histgrid(dssfr,ssfr_min,ssfr_max,nbin_ssfr,ssfr_hist)
    get_histgrid(dssfr,ssfr_min,ssfr_max,&nbin_ssfr,ssfr_hist);
// {F77} c     SFR
// {F77}          call get_histgrid(dsfr,sfr_min,sfr_max,nbin_sfr,sfr_hist)
    get_histgrid(dsfr,sfr_min,sfr_max,&nbin_sfr,sfr_hist);
// {F77} c     Mstars
// {F77}          call get_histgrid(da,a_min,a_max,nbin_a,a_hist)
    get_histgrid(da,a_min,a_max,&nbin_a,a_hist);
// {F77} c     Ldust
// {F77}          call get_histgrid(dldust,ld_min,ld_max,nbin_ld,ld_hist)
    get_histgrid(dldust,ld_min,ld_max,&nbin_ld,ld_hist);
// {F77} c     fmu_ism
// {F77}          call get_histgrid(dfmu_ism,fmuism_min,fmuism_max,nbin_fmu_ism,
// {F77}      +        fmuism_hist)
    get_histgrid(dfmu_ism,fmuism_min,fmuism_max,&nbin_fmu_ism,fmuism_hist);
// {F77} c     T_BGs (ISM)
// {F77}          call get_histgrid(dtbg,tbg1_min,tbg1_max,nbin_tbg1,tbg1_hist)
    get_histgrid(dtbg,tbg1_min,tbg1_max,&nbin_tbg1,tbg1_hist);
// {F77} c     T_BGs (BC)
// {F77}          call get_histgrid(dtbg,tbg2_min,tbg2_max,nbin_tbg2,tbg2_hist)
    get_histgrid(dtbg,tbg2_min,tbg2_max,&nbin_tbg2,tbg2_hist);
// {F77} c     xi's (PAHs, VSGs, BGs)
// {F77}          call get_histgrid(dxi,xi_min,xi_max,nbin_xi,xi_hist)
    get_histgrid(dxi,xi_min,xi_max,&nbin_xi,xi_hist);
// {F77} c     Mdust
// {F77}          call get_histgrid(dmd,md_min,md_max,nbin_md,md_hist)
    get_histgrid(dmd,md_min,md_max,&nbin_md,md_hist);
// {F77} 
// {F77} c     Compute histogram indexes for each parameter value
// {F77} c     [makes code faster -- implemented by the Nottingham people]
// {F77}          do i_sfh=1, n_sfh
// {F77}             aux=((fmu_sfh(i_sfh)-fmu_min)/(fmu_max-fmu_min))*nbin_fmu
// {F77}             i_fmu_sfh(i_sfh) = 1 + dint(aux)
// {F77} 
// {F77}             aux = ((mu(i_sfh)-mu_min)/(mu_max-mu_min)) * nbin_mu
// {F77}             i_mu(i_sfh) = 1 + dint(aux)
// {F77} 
// {F77}             aux=((tauv(i_sfh)-tv_min)/(tv_max-tv_min)) * nbin_tv
// {F77}             i_tauv(i_sfh) = 1 + dint(aux)
// {F77} 
// {F77}             aux=((tvism(i_sfh)-tv_min)/(tv_max-tv_min)) * nbin_tv
// {F77}             i_tvism(i_sfh) = 1 + dint(aux)
// {F77} 
// {F77}             if (lssfr(i_sfh).lt.ssfr_min) then
// {F77}                lssfr(i_sfh)=ssfr_min !set small sfrs to sfr_min
// {F77}             endif
// {F77}             aux=((lssfr(i_sfh)-ssfr_min)/(ssfr_max-ssfr_min))* nbin_ssfr
// {F77}             i_lssfr(i_sfh) = 1 + dint(aux)
// {F77}          enddo
    for(i_sfh=0; i_sfh<n_sfh; i_sfh++){
        aux=((fmu_sfh[i_sfh]-fmu_min)/(fmu_max-fmu_min)) * nbin_fmu;
        i_fmu_sfh[i_sfh] = (int)(aux);
        
        aux =((mu[i_sfh]-mu_min)/(mu_max-mu_min)) * nbin_mu;
        i_mu[i_sfh] = (int)(aux);
        
        aux=((tauv[i_sfh]-tv_min)/(tv_max-tv_min)) * nbin_tv;
        i_tauv[i_sfh] = (int)(aux);
        
        aux=((tvism[i_sfh]-tv_min)/(tv_max-tv_min)) * nbin_tv;
        i_tvism[i_sfh] = (int)(aux);
        
        if (lssfr[i_sfh] < ssfr_min){
            lssfr[i_sfh]=ssfr_min;
        }
        
        aux=((lssfr[i_sfh]-ssfr_min)/(ssfr_max-ssfr_min)) * nbin_ssfr;
        i_lssfr[i_sfh] = (int)(aux);
    }           
// {F77} 
// {F77}          do i_ir=1, n_ir
// {F77}             aux=((fmu_ir(i_ir)-fmu_min)/(fmu_max-fmu_min)) * nbin_fmu
// {F77}             i_fmu_ir(i_ir) = 1+dint(aux)
// {F77} 
// {F77}             aux=((fmu_ism(i_ir)-fmuism_min)/(fmuism_max-fmuism_min))*nbin_fmu_ism
// {F77}             i_fmu_ism(i_ir) = 1+dint(aux)
// {F77} 
// {F77}             aux=((tbg1(i_ir)-tbg1_min)/(tbg1_max-tbg1_min))* nbin_tbg1
// {F77}             i_tbg1(i_ir) = 1+dint(aux)
// {F77} 
// {F77}             aux=((tbg2(i_ir)-tbg2_min)/(tbg2_max-tbg2_min))* nbin_tbg2
// {F77}             i_tbg2(i_ir) = 1+dint(aux)
// {F77} 
// {F77}             aux=((xi1(i_ir)-xi_min)/(xi_max-xi_min)) * nbin_xi
// {F77}             i_xi1(i_ir) = 1+dint(aux)
// {F77} 
// {F77}             aux=((xi2(i_ir)-xi_min)/(xi_max-xi_min)) * nbin_xi
// {F77}             i_xi2(i_ir) = 1+dint(aux)
// {F77} 
// {F77}             aux=((xi3(i_ir)-xi_min)/(xi_max-xi_min)) * nbin_xi
// {F77}             i_xi3(i_ir) = 1+dint(aux)
// {F77}          enddo
// {F77} 

    for(i_ir=0; i_ir<n_ir; i_ir++){
        aux=((fmu_ir[i_ir]-fmu_min)/(fmu_max-fmu_min)) * nbin_fmu;
        i_fmu_ir[i_ir] = (int)(aux);

        aux=((fmu_ism[i_ir]-fmuism_min)/(fmuism_max-fmuism_min))*nbin_fmu_ism;
        i_fmu_ism[i_ir] = (int)(aux);

        aux=((tbg1[i_ir]-tbg1_min)/(tbg1_max-tbg1_min))* nbin_tbg1;
        i_tbg1[i_ir] = (int)(aux);

        aux=((tbg2[i_ir]-tbg2_min)/(tbg2_max-tbg2_min))* nbin_tbg2;
        i_tbg2[i_ir] = (int)(aux);

        aux=((xi1[i_ir]-xi_min)/(xi_max-xi_min)) * nbin_xi;
        i_xi1[i_ir] = (int)(aux);

        aux=((xi2[i_ir]-xi_min)/(xi_max-xi_min)) * nbin_xi;
        i_xi2[i_ir] = (int)(aux);

        aux=((xi3[i_ir]-xi_min)/(xi_max-xi_min)) * nbin_xi;
        i_xi3[i_ir] = (int)(aux);
    }

// {F77} c     ---------------------------------------------------------------------------
// {F77} c     HERE STARTS THE ACTUAL FIT
// {F77} c
// {F77} c     For each model in the stellar library, find all the models in the infrared
// {F77} c     dust emission library for which the proportion of dust luminosity from stellar
// {F77} c     birth clouds and diffuse ISM is the same, i.e. same "fmu" parameter (+/- df)
// {F77} c     Scale each infrared model satisfying this condition to the total dust
// {F77} c     luminosity Ldust predicted by the stellar+attenuation model
// {F77} c     [this satisfies the energy balance]
// {F77} c
// {F77} c
// {F77} c     For each combination of model, compute the chi^2 goodness-of-fit
// {F77} c     by comparing the observed UV-to-IR fluxes with the model predictions
// {F77} c
// {F77} c     The scaling factor "a" is in practice the stellar mass of the model
// {F77} c     since all the fluxes are normalised to Mstar
// {F77} c
// {F77} c     The probability of each model is p=exp(-chi^2/2)
// {F77} c     Compute marginal likelihood distributions of each parameter
// {F77} c     and build high-resolution histogram of each PDF
// {F77} c     ---------------------------------------------------------------------------
// {F77}          write(*,*) 'Starting fit.......'
// {F77}          DO i_sfh=1,n_sfh
    cout << "Starting fit......." << endl;
    for(i_sfh=0; i_sfh < n_sfh; i_sfh++){
// {F77} c     Check progress of the fit...
// {F77}             if (i_sfh.eq.(n_sfh/4)) then
// {F77}                write (*,*) '25% done...', i_sfh, " / ", n_sfh, " opt. models"
// {F77}             else if (i_sfh.eq.(n_sfh/2)) then
// {F77}                write (*,*) '50% done...', i_sfh, " / ", n_sfh, " opt. models"
// {F77}             else if (i_sfh.eq.(3*n_sfh/4)) then
// {F77}                write (*,*) '75% done...', i_sfh, " / ", n_sfh, " opt. models"
// {F77}             else if (i_sfh/n_sfh.eq.1) then
// {F77}                write (*,*) '100% done...', n_sfh, " opt. models - fit finished"
// {F77}             endif
        if ((i_sfh+1) == (n_sfh/4)){
            cout << " 25% done... " << i_sfh+1 << "/" << n_sfh << " opt. models" << endl;
        } else if((i_sfh+1) == (n_sfh/2)){
            cout << " 50% done... " << i_sfh+1 << "/" << n_sfh << " opt. models" << endl;
        } else if((i_sfh+1) == (3*n_sfh/4)){
            cout << " 75% done... " << i_sfh+1 << "/" << n_sfh << " opt. models" << endl;
        } else if((i_sfh+1)/n_sfh == 1){
            cout << "100% done... " << n_sfh << " opt. models - fit finished" << endl;
        }
    
// {F77} 
// {F77}             df=0.15             !fmu_opt=fmu_ir +/- dfmu
        df=0.15;
// {F77} 
// {F77} c     Search for the IR models with f_mu within the range set by df
// {F77}             DO i_ir=1,n_ir
            for(i_ir=0; i_ir<n_ir; i_ir++){
// {F77} 
// {F77}                num=0.
// {F77}                den=0.
// {F77}                chi2=0.
// {F77}                chi2_opt=0.
// {F77}                chi2_ir=0.
                num=0;
                den=0;
                chi2=0;
                chi2_opt=0;
                chi2_ir=0;
// {F77} 
// {F77}                if (abs(fmu_sfh(i_sfh)-fmu_ir(i_ir)).le.df) then
                    if(fabs(fmu_sfh[i_sfh]-fmu_ir[i_ir]) <= df){
// {F77} 
// {F77}                   n_models=n_models+1 !to keep track of total number of combinations
                        n_models=n_models+1;
// {F77} 
// {F77} c     Build the model flux array by adding SFH & IR
// {F77}                   do k=1,nfilt_sfh-nfilt_mix
// {F77}                      flux_mod(k)=flux_sfh(i_sfh,k)
// {F77}                   enddo
                        for(k=0; k < nfilt_sfh-nfilt_mix; k++){
                            flux_mod[k]=flux_sfh[k][i_sfh];
                        }
// {F77}                   do k=nfilt_sfh-nfilt_mix+1,nfilt_sfh
// {F77}                      flux_mod(k)=flux_sfh(i_sfh,k)+
// {F77}      +                    ldust(i_sfh)*flux_ir(i_ir,k-nfilt_sfh+nfilt_mix) !k-(nfilt_sfh-nfilt_mix)
// {F77}                   enddo
                        for(k=nfilt_sfh-nfilt_mix; k<nfilt_sfh; k++){
                            flux_mod[k]=flux_sfh[k][i_sfh]+ldust[i_sfh]*flux_ir[k-nfilt_sfh+nfilt_mix][i_ir];
                        }
// {F77}                   do k=nfilt_sfh+1,nfilt
// {F77}                      flux_mod(k)=ldust(i_sfh)*flux_ir(i_ir,k-nfilt_sfh+nfilt_mix)
// {F77}                   enddo
                        for(k=nfilt_sfh; k<nfilt; k++){
                            flux_mod[k]=ldust[i_sfh]*flux_ir[k-nfilt_sfh+nfilt_mix][i_ir];
                        }
// {F77} c     Compute scaling factor "a" - this is the number that minimizes chi^2
// {F77}                   do k=1,nfilt
// {F77}                      if (flux_obs(i_gal,k).gt.0) then
// {F77}                         num=num+(flux_mod(k)*flux_obs(i_gal,k)*w(i_gal,k))
// {F77}                         den=den+((flux_mod(k)**2)*w(i_gal,k))
// {F77}                      endif
// {F77}                   enddo
// {F77}                   a=num/den
                        for(k=0; k<nfilt; k++){
                            if(flux_obs[k][i_gal] > 0) {
                                num=num+(flux_mod[k]*flux_obs[k][i_gal]*w[k][i_gal]);
                                den=den+(pow(flux_mod[k],2)*w[k][i_gal]);
                            }
                        }
                        a=num/den;
// {F77} c     Compute chi^2 goodness-of-fit
// {F77}                   do k=1,nfilt_sfh
// {F77}                      if (flux_obs(i_gal,k).gt.0) then
// {F77}                         chi2=chi2+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
// {F77}      +                       **2)*w(i_gal,k))
// {F77}                         chi2_opt=chi2
// {F77}                      endif
// {F77}                   enddo
                        for(k=0;k<nfilt_sfh;k++){
                            if(flux_obs[k][i_gal] > 0){
                                chi2=chi2+((pow(flux_obs[k][i_gal]-(a*flux_mod[k]),2))*w[k][i_gal]);
                                chi2_opt=chi2;
                            }
                        }
// {F77} 
// {F77}                   if (chi2.lt.600.) then
// {F77}                      do k=nfilt_sfh+1,nfilt
// {F77}                         if (flux_obs(i_gal,k).gt.0) then
// {F77}                            chi2=chi2+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
// {F77}      +                          **2)*w(i_gal,k))
// {F77}                            chi2_ir=chi2_ir+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
// {F77}      +                          **2)*w(i_gal,k))
// {F77}                         endif
// {F77}                      enddo
// {F77}                   endif
                        if(chi2 < 600){
                            for(k=nfilt_sfh;k<nfilt;k++){
                                if (flux_obs[k][i_gal] > 0){
                                    chi2=chi2+((pow(flux_obs[k][i_gal]-(a*flux_mod[k]),2))*w[k][i_gal]);
                                    chi2_ir=chi2_ir+((pow(flux_obs[k][i_gal]-(a*flux_mod[k]),2))*w[k][i_gal]);
                                }
                            }
                        }
// {F77} c     Probability
// {F77}                   prob=dexp(-0.5*chi2)
// {F77}                   ptot=ptot+prob
                        prob=exp(-0.5*chi2);
                        ptot=ptot+prob;
// {F77} c     Best fit model
// {F77}                   chi2_new=chi2
// {F77}                   chi2_new_opt=chi2_opt
// {F77}                   chi2_new_ir=chi2_ir
// {F77}                   if (chi2_new.lt.chi2_sav) then
// {F77}                      chi2_sav=chi2_new
// {F77}                      sfh_sav=i_sfh
// {F77}                      ir_sav=i_ir
// {F77}                      a_sav=a
// {F77}                      chi2_sav_opt=chi2_new_opt
// {F77}                      chi2_sav_ir=chi2_new_ir
// {F77}                   endif
                        
                        chi2_new=chi2;
                        chi2_new_opt=chi2_opt;
                        chi2_new_ir=chi2_ir;
                        if(chi2_new < chi2_sav){
                            chi2_sav=chi2_new;
                            sfh_sav=i_sfh;
                            ir_sav=i_ir;
                            a_sav=a;
                            chi2_sav_opt=chi2_new_opt;
                            chi2_sav_ir=chi2_new_ir;
                        }
// {F77} 
// {F77} c     MARGINAL PROBABILITY DENSITY FUNCTIONS
// {F77} c     Locate each value on the corresponding histogram bin
// {F77} c     and compute probability histogram
// {F77} c     (normalize only in the end of the big loop)
// {F77} c     for now just add up probabilities in each bin
// {F77} 
// {F77} c     f_mu (SFH)
// {F77}                   ibin= i_fmu_sfh(i_sfh)
// {F77}                   ibin = max(1,min(ibin,nbin_fmu))
// {F77}                   psfh(ibin)=psfh(ibin)+prob
                        ibin=i_fmu_sfh[i_sfh];
                        ibin=max(1,min(ibin,nbin_fmu));
                        psfh[ibin]=psfh[ibin]+prob;
// {F77} c     f_mu (IR)
// {F77}                   ibin = i_fmu_ir(i_ir)
// {F77}                   ibin = max(1,min(ibin,nbin_fmu))
// {F77}                   pir(ibin)=pir(ibin)+prob
                        ibin=i_fmu_ir[i_ir];
                        ibin = max(1,min(ibin,nbin_fmu));
                        pir[ibin]=pir[ibin]+prob;
// {F77} c     mu
// {F77}                   ibin= i_mu(i_sfh)
// {F77}                   ibin = max(1,min(ibin,nbin_mu))
// {F77}                   pmu(ibin)=pmu(ibin)+prob
                        ibin=i_mu[i_sfh];
                        ibin=max(1,min(ibin,nbin_mu));
                        pmu[ibin]=pmu[ibin]+prob;
// {F77} c     tauV
// {F77}                   ibin= i_tauv(i_sfh)
// {F77}                   ibin = max(1,min(ibin,nbin_tv))
// {F77}                   ptv(ibin)=ptv(ibin)+prob
                        ibin=i_tauv[i_sfh];
                        ibin=max(1,min(ibin,nbin_tv));
                        ptv[ibin]=ptv[ibin]+prob;
// {F77} c     tvism
// {F77}                   ibin= i_tvism(i_sfh)
// {F77}                   ibin = max(1,min(ibin,nbin_tv))
// {F77}                   ptvism(ibin)=ptvism(ibin)+prob
                        ibin=i_tvism[i_sfh];
                        ibin=max(1,min(ibin,nbin_tv));
                        ptvism[ibin]=ptvism[ibin]+prob;
// {F77} c     sSFR_0.1Gyr
// {F77}                   ibin= i_lssfr(i_sfh)
// {F77}                   ibin = max(1,min(ibin,nbin_sfr))
// {F77}                   pssfr(ibin)=pssfr(ibin)+prob
                        ibin=i_lssfr[i_sfh];
                        ibin=max(1,min(ibin,nbin_sfr));
                        pssfr[ibin]=pssfr[ibin]+prob;
// {F77} c     Mstar
// {F77}                   a=dlog10(a)
// {F77}                   aux=((a-a_min)/(a_max-a_min)) * nbin_a
// {F77}                   ibin=1+dint(aux)
// {F77}                   ibin = max(1,min(ibin,nbin_a))
// {F77}                   pa(ibin)=pa(ibin)+prob
                        a=log10(a);
                        aux=((a-a_min)/(a_max-a_min)) * nbin_a;
                        ibin=(int)(aux);
                        ibin=max(1,min(ibin,nbin_a));
                        pa[ibin]=pa[ibin]+prob;
// {F77} c     SFR_0.1Gyr
// {F77}                   aux=((lssfr(i_sfh)+a-sfr_min)/(sfr_max-sfr_min))
// {F77}      +                 * nbin_sfr
// {F77}                   ibin= 1+dint(aux)
// {F77}                   ibin = max(1,min(ibin,nbin_sfr))
// {F77}                   psfr(ibin)=psfr(ibin)+prob
                        aux=((lssfr[i_sfh]+a-sfr_min)/(sfr_max-sfr_min))* nbin_sfr;
                        ibin=(int)(aux);
                        ibin=max(1,min(ibin,nbin_sfr));
                        psfr[ibin]=psfr[ibin]+prob;
// {F77} c     Ldust
// {F77}                   aux=((logldust(i_sfh)+a-ld_min)/(ld_max-ld_min))
// {F77}      +                 * nbin_ld
// {F77}                   ibin=1+dint(aux)
// {F77}                   ibin = max(1,min(ibin,nbin_ld))
// {F77}                   pldust(ibin)=pldust(ibin)+prob
                        aux=((logldust[i_sfh]+a-ld_min)/(ld_max-ld_min))* nbin_ld;
                        ibin=(int)(aux);
                        ibin=max(1,min(ibin,nbin_ld));
                        pldust[ibin]=pldust[ibin]+prob;
                        
// {F77} c     xi_C^tot
// {F77}                   ibin= i_fmu_ism(i_ir)
// {F77}                   ibin = max(1,min(ibin,nbin_fmu_ism))
// {F77}                   pism(ibin)=pism(ibin)+prob
                       ibin=i_fmu_ism[i_ir];
                       ibin=max(1,min(ibin,nbin_fmu_ism));
                       pism[ibin]=pism[ibin]+prob;
// {F77} c     T_C^ISM
// {F77}                   ibin= i_tbg1(i_ir)
// {F77}                   ibin = max(1,min(ibin,nbin_tbg1))
// {F77}                   ptbg1(ibin)=ptbg1(ibin)+prob
                       ibin=i_tbg1[i_ir];
                       ibin=max(1,min(ibin,nbin_tbg1));
                       ptbg1[ibin]=ptbg1[ibin]+prob;
// {F77} c     T_W^BC
// {F77}                   ibin= i_tbg2(i_ir)
// {F77}                   ibin = max(1,min(ibin,nbin_tbg2))
// {F77}                   ptbg2(ibin)=ptbg2(ibin)+prob
                       ibin=i_tbg2[i_ir];
                       ibin=max(1,min(ibin,nbin_tbg2));
                       ptbg2[ibin]=ptbg2[ibin]+prob;
// {F77} c     xi_PAH^tot
// {F77}                   ibin= i_xi1(i_ir)
// {F77}                   ibin = max(1,min(ibin,nbin_xi))
// {F77}                   pxi1(ibin)=pxi1(ibin)+prob
                       ibin=i_xi1[i_ir];
                       ibin=max(1,min(ibin,nbin_xi));
                       pxi1[ibin]=pxi1[ibin]+prob;
// {F77} c     xi_MIR^tot
// {F77}                   ibin= i_xi2(i_ir)
// {F77}                   ibin = max(1,min(ibin,nbin_xi))
// {F77}                   pxi2(ibin)=pxi2(ibin)+prob
                       ibin=i_xi2[i_ir];
                       ibin=max(1,min(ibin,nbin_xi));
                       pxi2[ibin]=pxi2[ibin]+prob;
// {F77} c     xi_W^tot
// {F77}                   ibin= i_xi3(i_ir)
// {F77}                   ibin = max(1,min(ibin,nbin_xi))
// {F77}                   pxi3(ibin)=pxi3(ibin)+prob
                       ibin=i_xi3[i_ir];
                       ibin=max(1,min(ibin,nbin_xi));
                       pxi3[ibin]=pxi3[ibin]+prob;
// {F77} c     Mdust
// {F77}                   lmdust(i_ir)=dlog10(mdust(i_ir)*ldust(i_sfh)*10.0**a)
// {F77}                   aux=((lmdust(i_ir)-md_min)/(md_max-md_min))*nbin_md
// {F77}                   ibin=1+dint(aux)
// {F77}                   ibin = max(1,min(ibin,nbin_md))
// {F77}                   pmd(ibin)=pmd(ibin)+prob
                       lmdust[i_ir]=log10(mdust[i_ir]*ldust[i_sfh]*pow(10.0,a));
                       aux=((lmdust[i_ir]-md_min)/(md_max-md_min))*nbin_md;
                       ibin=(int)(aux);
                       ibin=max(1,min(ibin,nbin_md));
                       pmd[ibin]=pmd[ibin]+prob;
// {F77} 
// {F77}                endif            !df condition
// {F77}             ENDDO               !loop in i_ir
// {F77}          ENDDO                  !loop in i_sfh
                    }
                        
            }
    }
// {F77} 
// {F77} c     Chi2-weighted models: normalize to total probability ptot
// {F77}          write(*,*) 'Number of random SFH models:       ', n_sfh
// {F77}          write(*,*) 'Number of IR dust emission models: ', n_ir
// {F77}          write(*,*) 'Value of df:                       ', df
// {F77}          write(*,*) 'Total number of models:            ', n_models
// {F77}          write(*,*) 'ptot= ',ptot
// {F77}          write(*,*) 'chi2_optical= ',chi2_sav_opt
// {F77}          write(*,*) 'chi2_infrared= ',chi2_sav_ir
    cout << "      Number of random SFH models: " << n_sfh << endl;
    cout << "Number of IR dust emission models: " << n_ir << endl;
    cout << "                      Value of df: " << df << endl;
    cout << "           Total number of models: " << n_models << endl;
    cout << "                             ptot: " << ptot << endl;
    cout << "                     chi2_optical: " << chi2_sav_opt << endl;
    cout << "                    chi2_infrared: " << chi2_sav_ir << endl;
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Compute percentiles of the (normalized) likelihood distributions
// {F77} c     ---------------------------------------------------------------------------
// {F77} c theSkyNet do i=1,1500
// {F77}          do i=1,3000
// {F77}             psfh(i)=psfh(i)/ptot
// {F77}             pir(i)=pir(i)/ptot
// {F77}             pmu(i)=pmu(i)/ptot
// {F77}             ptv(i)=ptv(i)/ptot
// {F77}             ptvism(i)=ptvism(i)/ptot
// {F77}             psfr(i)=psfr(i)/ptot
// {F77}             pssfr(i)=pssfr(i)/ptot
// {F77}             pa(i)=pa(i)/ptot
// {F77}             pldust(i)=pldust(i)/ptot
// {F77}             pism(i)=pism(i)/ptot
// {F77}             ptbg1(i)=ptbg1(i)/ptot
// {F77}             ptbg2(i)=ptbg2(i)/ptot
// {F77}             pxi1(i)=pxi1(i)/ptot
// {F77}             pxi2(i)=pxi2(i)/ptot
// {F77}             pxi3(i)=pxi3(i)/ptot
// {F77}             pmd(i)=pmd(i)/ptot
// {F77}          enddo
    for(i=0; i<3000; i++){
        psfh[i]=psfh[i]/ptot;
        pir[i]=pir[i]/ptot;
        pmu[i]=pmu[i]/ptot;
        ptv[i]=ptv[i]/ptot;
        ptvism[i]=ptvism[i]/ptot;
        psfr[i]=psfr[i]/ptot;
        pssfr[i]=pssfr[i]/ptot;
        pa[i]=pa[i]/ptot;
        pldust[i]=pldust[i]/ptot;
        pism[i]=pism[i]/ptot;
        ptbg1[i]=ptbg1[i]/ptot;
        ptbg2[i]=ptbg2[i]/ptot;
        pxi1[i]=pxi1[i]/ptot;
        pxi2[i]=pxi2[i]/ptot;
        pxi3[i]=pxi3[i]/ptot;
        pmd[i]=pmd[i]/ptot;
    }
// {F77} 
// {F77}          call get_percentiles(nbin_fmu,fmu_hist,psfh,pct_fmu_sfh)
// {F77}          call get_percentiles(nbin_fmu,fmu_hist,pir,pct_fmu_ir)
// {F77}          call get_percentiles(nbin_mu,mu_hist,pmu,pct_mu)
// {F77}          call get_percentiles(nbin_tv,tv_hist,ptv,pct_tv)
// {F77}          call get_percentiles(nbin_tv,tv_hist,ptvism,pct_tvism)
// {F77}          call get_percentiles(nbin_ssfr,ssfr_hist,pssfr,pct_ssfr)
// {F77}          call get_percentiles(nbin_sfr,sfr_hist,psfr,pct_sfr)
// {F77}          call get_percentiles(nbin_a,a_hist,pa,pct_mstr)
// {F77}          call get_percentiles(nbin_ld,ld_hist,pldust,pct_ld)
// {F77}          call get_percentiles(nbin_fmu_ism,fmuism_hist,pism,pct_ism)
// {F77}          call get_percentiles(nbin_tbg1,tbg1_hist,ptbg1,pct_tbg1)
// {F77}          call get_percentiles(nbin_tbg2,tbg2_hist,ptbg2,pct_tbg2)
// {F77}          call get_percentiles(nbin_xi,xi_hist,pxi1,pct_xi1)
// {F77}          call get_percentiles(nbin_xi,xi_hist,pxi2,pct_xi2)
// {F77}          call get_percentiles(nbin_xi,xi_hist,pxi3,pct_xi3)
// {F77}          call get_percentiles(nbin_md,md_hist,pmd,pct_md)
    get_percentiles(nbin_fmu,fmu_hist,psfh,pct_fmu_sfh);
    get_percentiles(nbin_fmu,fmu_hist,pir,pct_fmu_ir);
    get_percentiles(nbin_mu,mu_hist,pmu,pct_mu);
    get_percentiles(nbin_tv,tv_hist,ptv,pct_tv);
    get_percentiles(nbin_tv,tv_hist,ptvism,pct_tvism);
    get_percentiles(nbin_ssfr,ssfr_hist,pssfr,pct_ssfr);
    get_percentiles(nbin_sfr,sfr_hist,psfr,pct_sfr);
    get_percentiles(nbin_a,a_hist,pa,pct_mstr);
    get_percentiles(nbin_ld,ld_hist,pldust,pct_ld);
    get_percentiles(nbin_fmu_ism,fmuism_hist,pism,pct_ism);
    get_percentiles(nbin_tbg1,tbg1_hist,ptbg1,pct_tbg1);
    get_percentiles(nbin_tbg2,tbg2_hist,ptbg2,pct_tbg2);
    get_percentiles(nbin_xi,xi_hist,pxi1,pct_xi1);
    get_percentiles(nbin_xi,xi_hist,pxi2,pct_xi2);
    get_percentiles(nbin_xi,xi_hist,pxi3,pct_xi3);
    get_percentiles(nbin_md,md_hist,pmd,pct_md);
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Degrade the resolution od the likelihood distribution histograms
// {F77} c     from 3000 max bins to 100 max bins for storing in output file + plotting
// {F77} c     ---------------------------------------------------------------------------
// {F77}          do i=1,100
// {F77}             psfh2(i)=0.
// {F77}             pir2(i)=0.
// {F77}             pmu2(i)=0.
// {F77}             ptv2(i)=0.
// {F77}             ptvism2(i)=0.
// {F77}             pssfr2(i)=0.
// {F77}             psfr2(i)=0.
// {F77}             pa2(i)=0.
// {F77}             pldust2(i)=0.
// {F77}             pism2(i)=0.
// {F77}             ptbg1_2(i)=0.
// {F77}             ptbg2_2(i)=0.
// {F77}             pxi1_2(i)=0.
// {F77}             pxi2_2(i)=0.
// {F77}             pxi3_2(i)=0.
// {F77}             pmd_2(i)=0.
// {F77}          enddo
    for(i=0;i<100;i++){
        psfh2[i]=0;
        pir2[i]=0;
        pmu2[i]=0;
        ptv2[i]=0;
        ptvism2[i]=0;
        pssfr2[i]=0;
        psfr2[i]=0;
        pa2[i]=0;
        pldust2[i]=0;
        pism2[i]=0;
        ptbg1_2[i]=0;
        ptbg2_2[i]=0;
        pxi1_2[i]=0;
        pxi2_2[i]=0;
        pxi3_2[i]=0;
        pmd_2[i]=0;
    }
// {F77} 
// {F77} c     New histogram parameters
// {F77}          dfmu=0.05
// {F77}          fmu_min=0.
// {F77}          fmu_max=1.
// {F77}          dfmu_ism=0.05
// {F77}          fmuism_min=0.
// {F77}          fmuism_max=1.
// {F77}          dtv=0.125
// {F77}          dtvism=0.075
// {F77}          tv_min=0.
// {F77}          tv_max=6.
// {F77}          dssfr=0.10
// {F77}          ssfr_min=-13.0
// {F77}          ssfr_max=-6.0
// {F77}          dsfr=0.10
    dfmu=0.05;
    fmu_min=0;
    fmu_max=1;
    dfmu_ism=0.05;
    fmuism_min=0;
    fmuism_max=1;
    dtv=0.125;
    dtvism=0.075;
    tv_min=0;
    tv_max=6;
    dssfr=0.10;
    ssfr_min=-13.0;
    ssfr_max=-6.0;
    dsfr=0.10;
// {F77} c theSkyNet sfr_min=-3.
// {F77}          sfr_min=-8.
// {F77}          sfr_max=3.
// {F77}          da=0.10
    sfr_min=-8;
    sfr_max=3;
    da=0.10;
// {F77} c theSkyNet a_min=7.0
// {F77}          a_min=2.0
// {F77}          a_max=13.0
// {F77}          dtbg=1.
// {F77}          tbg2_min=15.
// {F77}          tbg2_max=25.
// {F77}          tbg1_min=30.
// {F77}          tbg1_max=60.
// {F77}          dxi=0.05
// {F77}          dmd=0.10
    a_min=2.0;
    a_max=13.0;
    dtbg=1;
    tbg2_min=15;
    tbg2_max=25;
    tbg1_min=30;
    tbg1_max=60;
    dxi=0.05;
    dmd=0.10;
// {F77} c theSkyNet md_min=3.
// {F77}          md_min=-2.
// {F77}          md_max=9.
    md_min=-2;
    md_max=9;
// {F77} 
// {F77}          call degrade_hist(dfmu,fmu_min,fmu_max,nbin_fmu,nbin2_fmu,
// {F77}      +        fmu_hist,fmu2_hist,psfh,psfh2)
// {F77}          call degrade_hist(dfmu,fmu_min,fmu_max,nbin_fmu,nbin2_fmu,
// {F77}      +        fmu_hist,fmu2_hist,pir,pir2)
// {F77}          call degrade_hist(dfmu,fmu_min,fmu_max,nbin_mu,nbin2_mu,
// {F77}      +        mu_hist,mu2_hist,pmu,pmu2)
// {F77}          call degrade_hist(dtv,tv_min,tv_max,nbin_tv,nbin2_tv,tv_hist,
// {F77}      +        tv2_hist,ptv,ptv2)
// {F77}          call degrade_hist(dtvism,tv_min,tv_max,nbin_tv,nbin2_tvism,
// {F77}      +        tv_hist,tvism2_hist,ptvism,ptvism2)
// {F77}          call degrade_hist(dssfr,ssfr_min,ssfr_max,nbin_ssfr,nbin2_ssfr,
// {F77}      +        ssfr_hist,ssfr2_hist,pssfr,pssfr2)
// {F77}          call degrade_hist(dsfr,sfr_min,sfr_max,nbin_sfr,nbin2_sfr,
// {F77}      +        sfr_hist,sfr2_hist,psfr,psfr2)
// {F77}          call degrade_hist(da,a_min,a_max,nbin_a,nbin2_a,a_hist,
// {F77}      +        a2_hist,pa,pa2)
// {F77}          call degrade_hist(da,a_min,a_max,nbin_ld,nbin2_ld,ld_hist,
// {F77}      +        ld2_hist,pldust,pldust2)
// {F77}          call degrade_hist(dfmu_ism,fmuism_min,fmuism_max,
// {F77}      +        nbin_fmu_ism,nbin2_fmu_ism,
// {F77}      +        fmuism_hist,fmuism2_hist,pism,pism2)
// {F77}          call degrade_hist(dtbg,tbg1_min,tbg1_max,nbin_tbg1,
// {F77}      +        nbin2_tbg1,
// {F77}      +        tbg1_hist,tbg1_2_hist,ptbg1,ptbg1_2)
// {F77}          call degrade_hist(dtbg,tbg2_min,tbg2_max,nbin_tbg2,
// {F77}      +        nbin2_tbg2,
// {F77}      +        tbg2_hist,tbg2_2_hist,ptbg2,ptbg2_2)
// {F77}          call degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,nbin2_xi,
// {F77}      +        xi_hist,xi2_hist,pxi1,pxi1_2)
// {F77}          call degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,nbin2_xi,
// {F77}      +        xi_hist,xi2_hist,pxi2,pxi2_2)
// {F77}          call degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,nbin2_xi,
// {F77}      +        xi_hist,xi2_hist,pxi3,pxi3_2)
// {F77}          call degrade_hist(dmd,md_min,md_max,nbin_md,nbin2_md,
// {F77}      +        md_hist,md2_hist,pmd,pmd_2)
    degrade_hist(dfmu,fmu_min,fmu_max,nbin_fmu,&nbin2_fmu,fmu_hist,fmu2_hist,psfh,psfh2);
    degrade_hist(dfmu,fmu_min,fmu_max,nbin_fmu,&nbin2_fmu,fmu_hist,fmu2_hist,pir,pir2);
    degrade_hist(dfmu,fmu_min,fmu_max,nbin_mu,&nbin2_mu,mu_hist,mu2_hist,pmu,pmu2);
    degrade_hist(dtv,tv_min,tv_max,nbin_tv,&nbin2_tv,tv_hist,tv2_hist,ptv,ptv2);
    degrade_hist(dtvism,tv_min,tv_max,nbin_tv,&nbin2_tvism,tv_hist,tvism2_hist,ptvism,ptvism2);
    degrade_hist(dssfr,ssfr_min,ssfr_max,nbin_ssfr,&nbin2_ssfr,ssfr_hist,ssfr2_hist,pssfr,pssfr2);
    degrade_hist(dsfr,sfr_min,sfr_max,nbin_sfr,&nbin2_sfr,sfr_hist,sfr2_hist,psfr,psfr2);
    degrade_hist(da,a_min,a_max,nbin_a,&nbin2_a,a_hist,a2_hist,pa,pa2);
    degrade_hist(da,a_min,a_max,nbin_ld,&nbin2_ld,ld_hist,ld2_hist,pldust,pldust2);
    degrade_hist(dfmu_ism,fmuism_min,fmuism_max,nbin_fmu_ism,&nbin2_fmu_ism,fmuism_hist,fmuism2_hist,pism,pism2);
    degrade_hist(dtbg,tbg1_min,tbg1_max,nbin_tbg1,&nbin2_tbg1,tbg1_hist,tbg1_2_hist,ptbg1,ptbg1_2);
    degrade_hist(dtbg,tbg2_min,tbg2_max,nbin_tbg2,&nbin2_tbg2,tbg2_hist,tbg2_2_hist,ptbg2,ptbg2_2);
    degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,&nbin2_xi,xi_hist,xi2_hist,pxi1,pxi1_2);
    degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,&nbin2_xi,xi_hist,xi2_hist,pxi2,pxi2_2);
    degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,&nbin2_xi,xi_hist,xi2_hist,pxi3,pxi3_2);
    degrade_hist(dmd,md_min,md_max,nbin_md,&nbin2_md,md_hist,md2_hist,pmd,pmd_2);
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Store fit results in .fit output file
// {F77} c     ---------------------------------------------------------------------------
// {F77}          write(31,702)
// {F77}  702     format('# OBSERVED FLUXES (and errors):')   
    fprintf(fitfp,"# OBSERVED FLUXES (and errors):\n");
// {F77}          write(filter_header,*) (filt_name(k),k=1,nfilt)
// {F77}          write(31,*) '#  '//filter_header(1:largo(filter_header))    
    fprintf(fitfp," #  ");
    for(k=0;k<nfilt;k++){
        fprintf(fitfp," %s ",filt_name[k]);
    }
    fprintf(fitfp,"\n");
// {F77} 
// {F77}          write(31,701) (flux_obs(i_gal,k),k=1,nfilt)
// {F77}          write(31,701) (sigma(i_gal,k),k=1,nfilt)
// {F77}          write(31,703)
// {F77}  703     format('#')
   for(k=0;k<nfilt;k++){
       fprintf(fitfp,"%12.3E",flux_obs[k][i_gal]);
   }
   fprintf(fitfp,"\n");
   for(k=0;k<nfilt;k++){
       fprintf(fitfp,"%12.3E",sigma[k][i_gal]);
   }
   fprintf(fitfp,"\n");
   fprintf(fitfp,"#\n");


// {F77} 
// {F77}          write(31,800)
// {F77}  800     format('# ... Results of fitting the fluxes to the model.....')
// {F77}  802     format('#.fmu(SFH)...fmu(IR)........mu......tauv',
// {F77}      +        '........sSFR..........M*.......Ldust',
// {F77}      +        '......T_W^BC.....T_C^ISM....xi_C^tot',
// {F77}      +        '..xi_PAH^tot..xi_MIR^tot....xi_W^tot.....tvism',
// {F77}      +        '.......Mdust.....SFR')
// {F77}  803     format(0p4f10.3,1p3e12.3,0p2f10.1,0p5f10.3,1p2e12.3)
// {F77} 
   fprintf(fitfp,"# ... Results of fitting the fluxes to the model.....\n");
// {F77}          write(31,703)
   fprintf(fitfp,"#\n");
// {F77}          write(31,804)
// {F77}  804     format('# BEST FIT MODEL: (i_sfh, i_ir, chi2, redshift)')
   fprintf(fitfp,"# BEST FIT MODEL: (i_sfh, i_ir, chi2, redshift)\n");
// {F77}          write(31,311) indx(sfh_sav),ir_sav,chi2_sav/n_flux,
// {F77}      +        redshift(i_gal)
// {F77}  311     format(2i10,0pf10.3,0pf12.6)
    // Adding 1 to ir_sav to get total number
   
   fprintf(fitfp," %10i %10i %10.3f %12.6f\n",indx[sfh_sav],ir_sav+1,chi2_sav/n_flux,redshift[i_gal]);
// {F77}          write(31,802)
   fprintf(fitfp,"#.fmu(SFH)...fmu(IR)........mu......tauv");;
   fprintf(fitfp,"........sSFR..........M*.......Ldust");
   fprintf(fitfp,"......T_W^BC.....T_C^ISM....xi_C^tot");
   fprintf(fitfp,"..xi_PAH^tot..xi_MIR^tot....xi_W^tot.....tvism");
   fprintf(fitfp,".......Mdust.....SFR");
   fprintf(fitfp,"\n");
// {F77}          write(31,803) fmu_sfh(sfh_sav),fmu_ir(ir_sav),mu(sfh_sav),
// {F77}      +        tauv(sfh_sav),ssfr(sfh_sav),a_sav,
// {F77}      +        ldust(sfh_sav)*a_sav,tbg1(ir_sav),tbg2(ir_sav),
// {F77}      +        fmu_ism(ir_sav),xi1(ir_sav),
// {F77}      +        xi2(ir_sav),xi3(ir_sav),
// {F77}      +        tvism(sfh_sav),mdust(ir_sav)*a_sav*ldust(sfh_sav),
// {F77}      +        ssfr(sfh_sav)*a_sav
// {F77} 
   fprintf(fitfp," %10.3f %10.3f %10.3f %10.3f %12.3E %12.3E %12.3E %10.1f %10.1f %10.3f %10.3f %10.3f %10.3f %10.3f %12.3E %12.3E",
           fmu_sfh[sfh_sav],fmu_ir[ir_sav],mu[sfh_sav],
           tauv[sfh_sav],ssfr[sfh_sav],a_sav,ldust[sfh_sav]*a_sav,
           tbg1[ir_sav],tbg2[ir_sav],fmu_ism[ir_sav],xi1[ir_sav],
           xi2[ir_sav],xi3[ir_sav],tvism[sfh_sav],
           mdust[ir_sav]*a_sav*ldust[sfh_sav],ssfr[sfh_sav]*a_sav);
   fprintf(fitfp,"\n");
// {F77}          write(31,*) '#  '//filter_header(1:largo(filter_header))
    fprintf(fitfp," #  ");
    for(k=0;k<nfilt;k++){
        fprintf(fitfp," %s ",filt_name[k]);
    }
    fprintf(fitfp,"\n");
// {F77}          write(31,701) (a_sav*flux_sfh(sfh_sav,k),k=1,nfilt_sfh-nfilt_mix),
// {F77}      +        (a_sav*(flux_sfh(sfh_sav,k)
// {F77}      +        +flux_ir(ir_sav,k-nfilt_sfh+nfilt_mix)*ldust(sfh_sav)),
// {F77}      +        k=nfilt_sfh-nfilt_mix+1,nfilt_sfh),
// {F77}      +        (a_sav*flux_ir(ir_sav,k-nfilt_sfh+nfilt_mix)*ldust(sfh_sav),
// {F77}      +        k=nfilt_sfh+1,nfilt)
    for(k=0;k<nfilt_sfh-nfilt_mix;k++){
       fprintf(fitfp," %12.3E ",a_sav*flux_sfh[k][sfh_sav]);
    }
    for(k=nfilt_sfh-nfilt_mix; k<nfilt_sfh; k++){
       fprintf(fitfp," %12.3E ",a_sav*flux_sfh[k][sfh_sav]+flux_ir[k-nfilt_sfh+nfilt_mix][ir_sav]*ldust[sfh_sav]);
    }
    for(k=nfilt_sfh;k<nfilt;k++){
       fprintf(fitfp," %12.3E ",a_sav*flux_ir[k-nfilt_sfh+nfilt_mix][ir_sav]*ldust[sfh_sav]);
    }
    fprintf(fitfp,"\n");
// {F77}  701     format(1p50e12.3)
// {F77} 

// {F77}          write(31,703)
// {F77}          write(31,805)
// {F77}  805     format('# MARGINAL PDF HISTOGRAMS FOR EACH PARAMETER......')
// {F77} 
    fprintf(fitfp,"#\n");
    fprintf(fitfp,"# MARGINAL PDF HISTOGRAMS FOR EACH PARAMETER......\n");    
// {F77}  807     format(0pf10.4,1pe12.3e3)
// {F77}  60      format('#....percentiles of the PDF......')
// {F77}  61      format(0p5f8.3)
// {F77}  62      format(1p5e12.3e3)
// {F77} 
// {F77} c theSkyNet
// {F77}  900     format('# theSkyNet2')
// {F77}  901     format(4(0pf10.4))
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,806)
// {F77}  806     format('# ... f_mu (SFH) ...')
// {F77}          do ibin=1,nbin2_fmu
// {F77} c theSkyNet
// {F77}             write(31,807) fmu2_hist(ibin),psfh2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... f_mu (SFH) ...\n");
    for(ibin=0; ibin<nbin2_fmu; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",fmu2_hist[ibin],psfh2[ibin]);
    }
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_fmu_sfh(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_fmu_sfh[k]);
    }
    fprintf(fitfp,"\n");

// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(psfh2, fmu2_hist, nbin2_fmu)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, fmu2_hist(1), fmu2_hist(nbin2_fmu), fmu2_hist(2) - fmu2_hist(1)
    hpbv = get_hpbv(psfh2,fmu2_hist,nbin2_fmu);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,fmu2_hist[0],fmu2_hist[nbin2_fmu-1]);
    fprintf(fitfp,"%10.4f\n",fmu2_hist[1] - fmu2_hist[0]);
    
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,808)
// {F77}  808     format('# ... f_mu (IR) ...')
// {F77}          do ibin=1,nbin2_fmu
// {F77} c theSkyNet
// {F77}             write(31,807) fmu2_hist(ibin),pir2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... f_mu (IR) ...\n");
    for(ibin=0; ibin<nbin2_fmu; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",fmu2_hist[ibin],pir2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_fmu_ir(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_fmu_ir[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pir2, fmu2_hist, nbin2_fmu)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, fmu2_hist(1), fmu2_hist(nbin2_fmu), fmu2_hist(2) - fmu2_hist(1)
    hpbv = get_hpbv(pir2,fmu2_hist,nbin2_fmu);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,fmu2_hist[0],fmu2_hist[nbin2_fmu-1]);
    fprintf(fitfp,"%10.4f\n",fmu2_hist[1] - fmu2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,809)
// {F77}  809     format('# ... mu parameter ...')
// {F77}          do ibin=1,nbin2_mu
// {F77} c theSkyNet
// {F77}             write(31,807) mu2_hist(ibin),pmu2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... mu parameter ...\n");
    for(ibin=0; ibin<nbin2_mu; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",mu2_hist[ibin],pmu2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_mu(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
       fprintf(fitfp,"%8.3f",pct_mu[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pmu2, mu2_hist, nbin2_mu)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, mu2_hist(1), mu2_hist(nbin2_mu), mu2_hist(2) - mu2_hist(1)
    hpbv = get_hpbv(pmu2,mu2_hist,nbin2_mu);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,mu2_hist[0],mu2_hist[nbin2_mu-1]);
    fprintf(fitfp,"%10.4f\n",mu2_hist[1] - mu2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,810)
// {F77}  810     format('# ... tau_V ...')
// {F77}          do ibin=1,nbin2_tv
// {F77} c theSkyNet
// {F77}             write(31,807) tv2_hist(ibin),ptv2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... tau_V ...\n");
    for(ibin=0; ibin<nbin2_tv; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",tv2_hist[ibin],ptv2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_tv(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_tv[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(ptv2, tv2_hist, nbin2_tv)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, tv2_hist(1), tv2_hist(nbin2_tv), tv2_hist(2) - tv2_hist(1)
    hpbv = get_hpbv(ptv2, tv2_hist, nbin2_tv);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,tv2_hist[0],tv2_hist[nbin2_tv-1]);
    fprintf(fitfp,"%10.4f\n",tv2_hist[1] - tv2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,811)
// {F77}  811     format('# ... sSFR_0.1Gyr ...')
// {F77}          do ibin=1,nbin2_ssfr
// {F77} c theSkyNet
// {F77}             write(31,812) ssfr2_hist(ibin),pssfr2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... sSFR_0.1Gyr ...\n");
    for(ibin=0; ibin<nbin2_ssfr; ibin++){
        fprintf(fitfp,"%12.3E%12.3E\n",ssfr2_hist[ibin],pssfr2[ibin]);
    }
// {F77}         
// {F77}  812     format(1p2e12.3e3)
// {F77}          write(31,60)
// {F77}          write(31,62) (pct_ssfr(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%12.3E",pct_ssfr[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pssfr2, ssfr2_hist, nbin2_ssfr)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, ssfr2_hist(1), ssfr2_hist(nbin2_ssfr), ssfr2_hist(2) - ssfr2_hist(1)
    hpbv = get_hpbv(pssfr2, ssfr2_hist, nbin2_ssfr);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,ssfr2_hist[0],ssfr2_hist[nbin2_ssfr-1]);
    fprintf(fitfp,"%10.4f\n",ssfr2_hist[1] - ssfr2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,813)
// {F77}  813     format('# ... M(stars) ...')
// {F77}          do ibin=1,nbin2_a
// {F77} c theSkyNet
// {F77}             write(31,812) a2_hist(ibin),pa2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... M(stars) ...\n");
    for(ibin=0; ibin<nbin2_a; ibin++){
        fprintf(fitfp,"%12.3E%12.3E\n",a2_hist[ibin],pa2[ibin]);
    }
// {F77}          write(31,60)
// {F77}          write(31,62) (pct_mstr(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%12.3E",pct_mstr[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pa2, a2_hist, nbin2_a)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, a2_hist(1), a2_hist(nbin2_a), a2_hist(2) - a2_hist(1)
    hpbv = get_hpbv(pa2, a2_hist, nbin2_a);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,a2_hist[0],a2_hist[nbin2_a-1]);
    fprintf(fitfp,"%10.4f\n",a2_hist[1] - a2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,814)
// {F77}  814     format('# ... Ldust ...')
// {F77}          do ibin=1,nbin2_ld
// {F77} c theSkyNet
// {F77}             write(31,812) ld2_hist(ibin),pldust2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... Ldust ...\n");
    for(ibin=0; ibin<nbin2_ld; ibin++){
        fprintf(fitfp,"%12.3E%12.3E\n",ld2_hist[ibin],pldust2[ibin]);
    }
// {F77}          write(31,60)
// {F77}          write(31,62) (pct_ld(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%12.3E",pct_ld[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pldust2, ld2_hist, nbin2_ld)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, ld2_hist(1), ld2_hist(nbin2_ld), ld2_hist(2) - ld2_hist(1)
    hpbv = get_hpbv(pldust2, ld2_hist, nbin2_ld);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,ld2_hist[0],ld2_hist[nbin2_ld-1]);
    fprintf(fitfp,"%10.4f\n",ld2_hist[1] - ld2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,815)
// {F77}  815     format('# ... T_C^ISM ...')
// {F77}          do ibin=1,nbin2_tbg2
// {F77} c theSkyNet
// {F77}             write(31,807) tbg2_2_hist(ibin),ptbg2_2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... T_C^ISM ...\n");
    for(ibin=0; ibin<nbin2_tbg2; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",tbg2_2_hist[ibin],ptbg2_2[ibin]);
    }
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_tbg2(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_tbg2[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(ptbg2_2, tbg2_2_hist, nbin2_tbg2)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, tbg2_2_hist(1), tbg2_2_hist(nbin2_tbg2), tbg2_2_hist(2) - tbg2_2_hist(1)
    hpbv = get_hpbv(ptbg2_2, tbg2_2_hist, nbin2_tbg2);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,tbg2_2_hist[0],tbg2_2_hist[nbin2_tbg2-1]);
    fprintf(fitfp,"%10.4f\n",tbg2_2_hist[1] - tbg2_2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,820)
// {F77}  820     format('# ... T_W^BC ...')
// {F77}          do ibin=1,nbin2_tbg1
// {F77} c theSkyNet
// {F77}             write(31,807) tbg1_2_hist(ibin),ptbg1_2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... T_W^BC ...\n");
    for(ibin=0; ibin<nbin2_tbg1; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",tbg1_2_hist[ibin],ptbg1_2[ibin]);
    }
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_tbg1(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_tbg1[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(ptbg1_2, tbg1_2_hist, nbin2_tbg1)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, tbg1_2_hist(1), tbg1_2_hist(nbin2_tbg1), tbg1_2_hist(2) - tbg1_2_hist(1)
    hpbv = get_hpbv(ptbg1_2, tbg1_2_hist, nbin2_tbg1);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,tbg1_2_hist[0],tbg1_2_hist[nbin2_tbg1-1]);
    fprintf(fitfp,"%10.4f\n",tbg1_2_hist[1] - tbg1_2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,821)
// {F77}  821     format('# ... xi_C^tot ...')
// {F77}          do ibin=1,nbin2_fmu_ism
// {F77} c theSkyNet
// {F77}             write(31,807) fmuism2_hist(ibin),pism2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... xi_C^tot ...\n");
    for(ibin=0; ibin<nbin2_fmu_ism; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",fmuism2_hist[ibin],pism2[ibin]);
    }
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_ism(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%10.3f",pct_ism[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pism2, fmuism2_hist, nbin2_fmu_ism)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, fmuism2_hist(1), fmuism2_hist(nbin2_fmu_ism), fmuism2_hist(2) - fmuism2_hist(1)
    hpbv = get_hpbv(pism2, fmuism2_hist, nbin2_fmu_ism);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,fmuism2_hist[0],fmuism2_hist[nbin2_fmu_ism-1]);
    fprintf(fitfp,"%10.4f\n",fmuism2_hist[1] - fmuism2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,816)
// {F77}  816     format('# ... xi_PAH^tot ...')
// {F77}          do ibin=1,nbin2_xi
// {F77} c theSkyNet
// {F77}             write(31,807) xi2_hist(ibin),pxi1_2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... xi_PAH^tot ...\n");
    for(ibin=0; ibin<nbin2_xi; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",xi2_hist[ibin],pxi1_2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_xi1(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_xi1[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pxi1_2, xi2_hist, nbin2_xi)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, xi2_hist(1), xi2_hist(nbin2_xi), xi2_hist(2) - xi2_hist(1)
    hpbv = get_hpbv(pxi1_2, xi2_hist, nbin2_xi);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,xi2_hist[0],xi2_hist[nbin2_xi-1]);
    fprintf(fitfp,"%10.4f\n",xi2_hist[1] - xi2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,817)
// {F77}  817     format('# ... xi_MIR^tot ...')
// {F77}          do ibin=1,nbin2_xi
// {F77} c theSkyNet
// {F77}             write(31,807) xi2_hist(ibin),pxi2_2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... xi_MIR^tot ...\n");
    for(ibin=0; ibin<nbin2_xi; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",xi2_hist[ibin],pxi2_2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_xi2(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_xi2[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pxi2_2, xi2_hist, nbin2_xi)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, xi2_hist(1), xi2_hist(nbin2_xi), xi2_hist(2) - xi2_hist(1)
    hpbv = get_hpbv(pxi2_2, xi2_hist, nbin2_xi);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,xi2_hist[0],xi2_hist[nbin2_xi-1]);
    fprintf(fitfp,"%10.4f\n",xi2_hist[1] - xi2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,818)
// {F77}  818     format('# ... xi_W^tot ...')
// {F77}          do ibin=1,nbin2_xi
// {F77} c theSkyNet
// {F77}             write(31,807) xi2_hist(ibin),pxi3_2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... xi_W^tot ...\n");
    for(ibin=0; ibin<nbin2_xi; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",xi2_hist[ibin],pxi3_2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_xi3(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_xi3[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pxi3_2, xi2_hist, nbin2_xi)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, xi2_hist(1), xi2_hist(nbin2_xi), xi2_hist(2) - xi2_hist(1)
    hpbv = get_hpbv(pxi3_2, xi2_hist, nbin2_xi);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,xi2_hist[0],xi2_hist[nbin2_xi-1]);
    fprintf(fitfp,"%10.4f\n",xi2_hist[1] - xi2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,81)
// {F77}  81      format('# ... tau_V^ISM...')
// {F77}          do ibin=1,nbin2_tvism
// {F77} c theSkyNet
// {F77}             write(31,807) tvism2_hist(ibin),ptvism2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... tau_V^ISM...\n");
    for(ibin=0; ibin<nbin2_tvism; ibin++){
        fprintf(fitfp,"%10.4f%12.3E\n",tvism2_hist[ibin],ptvism2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_tvism(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_tvism[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(ptvism2, tvism2_hist, nbin2_tvism)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, tvism2_hist(1), tvism2_hist(nbin2_tvism), tvism2_hist(2) - tvism2_hist(1)
    hpbv = get_hpbv(ptvism2, tvism2_hist, nbin2_tvism);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,tvism2_hist[0],tvism2_hist[nbin2_tvism-1]);
    fprintf(fitfp,"%10.4f\n",tvism2_hist[1] - tvism2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,888)
// {F77}  888     format('# ... M(dust)...')
// {F77}          do ibin=1,nbin2_md
// {F77} c theSkyNet
// {F77}             write(31,807) md2_hist(ibin),pmd_2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... M(dust)...\n");
    for(ibin=0; ibin<nbin2_md; ibin++){
       fprintf(fitfp,"%10.4f%12.3E\n",md2_hist[ibin],pmd_2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_md(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_md[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(pmd_2, md2_hist, nbin2_md)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, md2_hist(1), md2_hist(nbin2_md), md2_hist(2) - md2_hist(1)
    hpbv = get_hpbv(pmd_2, md2_hist, nbin2_md);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,md2_hist[0],md2_hist[nbin2_md-1]);
    fprintf(fitfp,"%10.4f\n",md2_hist[1] - md2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77}          write(31,889)
// {F77}  889     format('# ... SFR_0.1Gyr ...')
// {F77}          do ibin=1,nbin2_sfr
// {F77} c theSkyNet
// {F77}             write(31,812) sfr2_hist(ibin),psfr2(ibin)
// {F77}          enddo
    fprintf(fitfp,"# ... SFR_0.1Gyr ...\n");
    for(ibin=0; ibin<nbin2_sfr; ibin++){
        fprintf(fitfp,"%12.3E%12.3E\n",sfr2_hist[ibin],psfr2[ibin]);
    }    
// {F77}          write(31,60)
// {F77}          write(31,61) (pct_sfr(k),k=1,5)
    fprintf(fitfp,"#....percentiles of the PDF......\n");
    for(k=0;k<5;k++){
        fprintf(fitfp,"%8.3f",pct_sfr[k]);
    }
    fprintf(fitfp,"\n");
// {F77} c theSkyNet
// {F77}          hpbv = get_hpbv(psfr2, sfr2_hist, nbin2_sfr)
// {F77}          write(31, 900)
// {F77}          write(31, 901) hpbv, sfr2_hist(1), sfr2_hist(nbin2_sfr), sfr2_hist(2) - sfr2_hist(1)
    hpbv = get_hpbv(psfr2, sfr2_hist, nbin2_sfr);
    fprintf(fitfp,"# theSkyNet2\n");
    fprintf(fitfp,"%10.4f %10.4f %10.4f",hpbv,sfr2_hist[0],sfr2_hist[nbin2_sfr-1]);
    fprintf(fitfp,"%10.4f\n",sfr2_hist[1] - sfr2_hist[0]);
// {F77} c theSkyNet
// {F77} 
// {F77} c     ---------------------------------------------------------------------------
// {F77}          if (skynet .eqv. .TRUE.) then
// {F77}             write(31,*) '#...theSkyNet parameters of this model'
// {F77}             write(31,'(2I15,E20.6,E20.4,E10.2)') indx(sfh_sav),ir_sav,a_sav,fmu_sfh(sfh_sav),redshift(i_gal)
// {F77} 
// {F77}             close (31)
// {F77}          else
// {F77} c     ---------------------------------------------------------------------------
// {F77} 
// {F77}             write(*,*) 'Storing best-fit SED...'
// {F77}             write(*,*) outfile2
// {F77}             call get_bestfit_sed(indx(sfh_sav),ir_sav,a_sav,
// {F77}      +           fmu_sfh(sfh_sav),redshift(i_gal),outfile2)
    if(skynet){
        fprintf(fitfp," #...theSkyNet parameters of this model\n");
        fprintf(fitfp,"%15i%15i%20.5E%20.3E%10.1E\n",indx[sfh_sav],ir_sav+1,a_sav,fmu_sfh[sfh_sav],redshift[i_gal]);
    } else {
        // TODO : Imlement best fit.
    }
}
// {F77}          endif
// {F77}          STOP
// {F77}          END
// {F77} 
// {F77} c theSkyNet
// {F77} c     ===========================================================================
// {F77}       REAL*8 FUNCTION GET_HPBV(hist1, hist2, nbin)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Find the bin with the highest probability value
// {F77} c     ---------------------------------------------------------------------------
// {F77}       implicit none
// {F77}       integer nbin, ibin
// {F77}       real*8  hist1(nbin), hist2(nbin), max_pr
// {F77} 
// {F77}       do ibin=1,nbin
// {F77}          if (ibin .eq. 1) then
// {F77}             max_pr = hist1(ibin)
// {F77}             get_hpbv = hist2(ibin)
// {F77}          else if (hist1(ibin) .gt. max_pr) then
// {F77}             max_pr = hist1(ibin)
// {F77}             get_hpbv = hist2(ibin)
// {F77}          endif
// {F77}       enddo
// {F77}       RETURN
// {F77}       END
double get_hpbv(double hist1[],double hist2[],int nbin){
    int ibin;
    double max_pr;
    double hpbv;
    for(ibin=0;ibin<nbin;ibin++){
        if(ibin == 0){
            max_pr = hist1[ibin];
            hpbv = hist2[ibin];
        }else if(hist1[ibin] > max_pr){
            max_pr = hist1[ibin];
            hpbv = hist2[ibin];
        }
    }
    return hpbv;
}
            
// {F77} c theSkyNet
// {F77} 
// {F77} c     ===========================================================================
// {F77}       SUBROUTINE DEGRADE_HIST(delta,min,max,nbin1,nbin2,hist1,hist2,prob1,prob2)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Degrades the resolution of the histograms containing the likelihood
// {F77} c     distribution of the parameters: to facilitate storage & visualization
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     delta : bin width
// {F77} c     min   : minumum value
// {F77} c     max   : maximum value
// {F77} c     nbin1 : number of bins of high-res histogram
// {F77} c     nbin2 : number of bins of output low-res histogram
// {F77} c     hist1 : input high-res histogram x-axis
// {F77} c     hist2 : output low-res histogram x-axis
// {F77} c     prob1 : input histogram values
// {F77} c     prob2 : output histogram values
// {F77} c     ===========================================================================
// {F77}       implicit none
// {F77}       integer nbin1,nbin2,i,ibin,maxnbin2
// {F77}       parameter(maxnbin2=200)
// {F77}       real*8 delta,max,min,max2
// {F77}       real*8 hist1(nbin1),prob1(nbin1)
// {F77}       real*8 hist2(maxnbin2),prob2(maxnbin2)
// {F77}       real*8 aux
// {F77} 
// {F77}       max2=0.
// {F77}       max2=max+(delta/2.)
// {F77} 
// {F77}       call get_histgrid(delta,min,max2,nbin2,hist2)
// {F77} 
// {F77}       do i=1,nbin1
// {F77}          aux=((hist1(i)-min)/(max-min)) * nbin2
// {F77}          ibin=1+dint(aux)
// {F77}          prob2(ibin)=prob2(ibin)+prob1(i)
// {F77}       enddo
// {F77} 
// {F77}       RETURN
// {F77}       END
void degrade_hist(double delta,double min,double max,int nbin1,int * nbin2,double hist1[], double hist2[],double prob1[],double prob2[]){
    int i=0;
    int ibin=0;
    int maxnbin2=200;
    double max2=0;
    double aux;
    
    max2=max+(delta/2);
    
    get_histgrid(delta,min,max2,nbin2,hist2);
    for(i=0;i<nbin1;i++){
        aux=((hist1[i]-min)/(max-min))*(*nbin2);
        ibin=(int)(aux);
        prob2[ibin]=prob2[ibin]+prob1[i];
    }
}
   
// {F77} 
// {F77} c     ===========================================================================
// {F77}       SUBROUTINE GET_HISTGRID(dv,vmin,vmax,nbin,vout)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Build histogram grid (i.e. vector of bins)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c       dv : bin width
// {F77} c     vmin : minumum value
// {F77} c     vmax : maximum value
// {F77} c     nbin : number of bins
// {F77} c     vout : output vector of bins
// {F77} c     ===========================================================================
// {F77}       implicit none
// {F77}       integer nbin,ibin,maxnbin
// {F77}       parameter(maxnbin=5000)
// {F77}       real*8 vout(maxnbin)
// {F77}       real*8 vmin,vmax,x1,x2,dv
// {F77} 
// {F77}       ibin=1
// {F77}       x1=vmin
// {F77}       x2=vmin+dv
// {F77}       do while (x2.le.vmax)
// {F77}          vout(ibin)=0.5*(x1+x2)
// {F77}          ibin=ibin+1
// {F77}          x1=x1+dv
// {F77}          x2=x2+dv
// {F77}       enddo
// {F77}       nbin=ibin-1
// {F77}       return
// {F77}       END
void get_histgrid(double dv,double vmin,double vmax,int* nbin,double vout[]){
    double x1,x2;
    (*nbin) = 0;
    x1=vmin;
    x2=vmin+dv;
    while(x2 <= vmax){
        vout[(*nbin)]=0.5*(x1+x2);
        x1=x1+dv;
        x2=x2+dv;
        (*nbin)++;
    }
}   
// {F77} 
// {F77} c     ===========================================================================
// {F77}       SUBROUTINE GET_PERCENTILES(n,par,probability,percentile)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Calculates percentiles of the probability distibution
// {F77} c     for a given parameter: 2.5, 16, 50 (median), 84, 97.5
// {F77} c     1. Sort the parameter + the probability array
// {F77} c     2. Find the parameter value M for which:
// {F77} c        P (x < M) = P (x > M) = percentiles
// {F77} c     ---------------------------------------------------------------------------
// {F77} c               n : number of points (bins)
// {F77} c             par : parameter value (vector of bins)
// {F77} c     probability : vector with prob of each parameter value (or bin)
// {F77} c      percentile : vector containing 5 percentiles described above
// {F77} c     ===========================================================================
// {F77}       integer n,n_perc(5),i
// {F77}       real*8 par(n),probability(n),pless
// {F77}       real*8 percentile(5),limit(5)
// {F77} 
// {F77}       data limit/0.025,0.16,0.50,0.84,0.975/
// {F77} 
// {F77}       call sort2(n,par,probability)
// {F77} 
// {F77}       pless=0.
// {F77}       do i=1,5
// {F77}          n_perc(i)=1
// {F77}          pless=0.
// {F77}          do while (pless.le.limit(i))
// {F77}             pless=pless+probability(n_perc(i))
// {F77}             n_perc(i)=n_perc(i)+1
// {F77}          enddo
// {F77}          n_perc(i)=n_perc(i)-1
// {F77}          percentile(i)=par(n_perc(i))
// {F77}       enddo
// {F77} 
// {F77}       return
// {F77}       END
void get_percentiles(int n,double par[],double probability[],double percentile[]){
    int i=0;
    double pless=0;
    int n_perc[5];
    double limit[5]={0.025,0.16,0.50,0.84,0.975};
    sort2(par,probability,0,n-1);
    
   for(i=0; i<5; i++){
       n_perc[i]=0;
       pless=0;
       while(pless <= limit[i]){
           pless=pless+probability[n_perc[i]];
           n_perc[i]++;
       }
       n_perc[i]=n_perc[i]-1;
       percentile[i]=par[n_perc[i]];
   }
}
  
// {F77} 
// {F77} c     ===========================================================================
// {F77}       SUBROUTINE sort2(n,arr,brr)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Sorts an array arr(1:n) into ascending order using Quicksort
// {F77} c     while making the corresponding rearrangement of the array brr(1:n)
// {F77} c     ===========================================================================
// {F77}       INTEGER n,M,NSTACK
// {F77}       REAL*8 arr(n),brr(n)
// {F77}       PARAMETER (M=7,NSTACK=5000)
// {F77}       INTEGER i,ir,j,jstack,k,l,istack(NSTACK)
// {F77}       REAL*8 a,b,temp
// {F77}       jstack=0
// {F77}       l=1
// {F77}       ir=n
// {F77}  1    if (ir-l.lt.M) then
// {F77}          do j=l+1,ir
// {F77}             a=arr(j)
// {F77}             b=brr(j)
// {F77}             do i=j-1,l,-1
// {F77}                if (arr(i).le.a) goto 2
// {F77}                arr(i+1)=arr(i)
// {F77}                brr(i+1)=brr(i)
// {F77}             enddo
// {F77}             i=l-1
// {F77}  2          arr(i+1)=a
// {F77}             brr(i+1)=b
// {F77}          enddo
// {F77}          if (jstack.eq.0) return
// {F77}          ir=istack(jstack)
// {F77}          l=istack(jstack-1)
// {F77}          jstack=jstack-2
// {F77}       else
// {F77}          k=(l+ir)/2
// {F77}          temp=arr(k)
// {F77}          arr(k)=arr(l+1)
// {F77}          arr(l+1)=temp
// {F77}          temp=brr(k)
// {F77}          brr(k)=brr(l+1)
// {F77}          brr(l+1)=temp
// {F77}          if (arr(l).gt.arr(ir)) then
// {F77}             temp=arr(l)
// {F77}             arr(l)=arr(ir)
// {F77}             arr(ir)=temp
// {F77}             temp=brr(l)
// {F77}             brr(l)=brr(ir)
// {F77}             brr(ir)=temp
// {F77}          endif
// {F77}          if (arr(l+1).gt.arr(ir)) then
// {F77}             temp=arr(l+1)
// {F77}             arr(l+1)=arr(ir)
// {F77}             arr(ir)=temp
// {F77}             temp=brr(l+1)
// {F77}             brr(l+1)=brr(ir)
// {F77}             brr(ir)=temp
// {F77}          endif
// {F77}          if (arr(l).gt.arr(l+1)) then
// {F77}             temp=arr(l)
// {F77}             arr(l)=arr(l+1)
// {F77}             arr(l+1)=temp
// {F77}             temp=brr(l)
// {F77}             brr(l)=brr(l+1)
// {F77}             brr(l+1)=temp
// {F77}          endif
// {F77}          i=l+1
// {F77}          j=ir
// {F77}          a=arr(l+1)
// {F77}          b=brr(l+1)
// {F77}  3       continue
// {F77}          i=i+1
// {F77}          if (arr(i).lt.a) goto 3
// {F77}  4       continue
// {F77}          j=j-1
// {F77}          if (arr(j).gt.a) goto 4
// {F77}          if (j.lt.i) goto 5
// {F77}          temp=arr(i)
// {F77}          arr(i)=arr(j)
// {F77}          arr(j)=temp
// {F77}          temp=brr(i)
// {F77}          brr(i)=brr(j)
// {F77}          brr(j)=temp
// {F77}          goto 3
// {F77}  5       arr(l+1)=arr(j)
// {F77}          arr(j)=a
// {F77}          brr(l+1)=brr(j)
// {F77}          brr(j)=b
// {F77}          jstack=jstack+2
// {F77}          if (jstack.gt.NSTACK) write (*,*) 'NSTACK too small in sort2'
// {F77}          if (ir-i+1.ge.j-l) then
// {F77}             istack(jstack)=ir
// {F77}             istack(jstack-1)=i
// {F77}             ir=j-1
// {F77}          else
// {F77}             istack(jstack)=j-1
// {F77}             istack(jstack-1)=l
// {F77}             l=i
// {F77}          endif
// {F77}       endif
// {F77}       goto 1
// {F77}       END
void sort2(double arr1[], double arr2[], int left, int right) {
    int i = left;
    int j = right;
    double temp1,temp2;
    double pivot = arr1[(left + right) / 2];
  
    while (i <= j) {
        while (arr1[i] < pivot)
            i++;
            while (arr1[j] > pivot)
                j--;
            if (i <= j) {
               temp1 = arr1[i];
               temp2 = arr2[i];
               arr1[i] = arr1[j];
               arr2[i] = arr2[j];
               arr1[j] = temp1;
               arr2[j] = temp2;
               i++;
               j--;
        }
    };
  
    if (left < j)
        sort2(arr1,arr2,left,j);
    if (i < right)
        sort2(arr1,arr2,i,right);
}
// {F77} 
// {F77} 
// {F77} c     ===========================================================================
// {F77}       REAL*8 FUNCTION DL(h,q,z)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Computes luminosity distance corresponding to a redshift z.
// {F77} c     Uses Mattig formulae for qo both 0 and non 0
// {F77} c     Revised January 1991 to implement cosmolgical constant
// {F77} c     Ho in km/sec/Mpc, DL is in Mpc
// {F77} c     ===========================================================================
// {F77}       implicit none
// {F77}       real*8 h, q, z, d1, d2
// {F77}       real*8 aa, bb, epsr, s, s0, funl
// {F77}       real*8 dd1, dd2, omega0
// {F77}       logical success
// {F77}       integer npts
// {F77}       external funl
// {F77}       common /cosm/ omega0
// {F77} 
// {F77}       if (z.le.0.) then
// {F77}          dl=1.e-5               !10 pc
// {F77}          return
// {F77}       endif
// {F77} 
// {F77}       if (q .eq. 0) then
// {F77}          dl = ((3.e5 * z) * (1 + (z / 2.))) / h
// {F77}       else if (q .gt. 0.) then
// {F77}          d1 = (q * z) + ((q - 1.) * (sqrt(1. + ((2. * q) * z)) - 1.))
// {F77}          d2 = ((h * q) * q) / 3.e5
// {F77}          dl = d1 / d2
// {F77}       else if (q .lt. 0.) then
// {F77}          omega0 = (2. * (q + 1.)) / 3.
// {F77}          aa = 1.
// {F77}          bb = 1. + z
// {F77}          success=.false.
// {F77}          s0=1.e-10
// {F77}          npts=0
// {F77}          do while (.not.success)
// {F77}             npts=npts+1
// {F77}             call midpnt(funl,aa,bb,s,npts)
// {F77}             epsr=abs(s-s0)/s0
// {F77}             if (epsr.lt.1.e-4) then
// {F77}                success=.true.
// {F77}             else
// {F77}                s0=s
// {F77}             endif
// {F77}          enddo
// {F77}          dd1=s
// {F77} 	 dd2 = (3.e5 * (1. + z)) / (h * sqrt(omega0))
// {F77} 	 dl = dd1 * dd2
// {F77}       end if
// {F77} 
// {F77}       return
// {F77}       end
double get_dl(double h,double q,double z){
    double dl, d1, d2;
    double aa,bb,epsr,s,s0;
    double dd1,dd2;
    bool success;
    int npts;
    
    if(z <= 0){
        return (1.0e-5);
    }

    if(q == 0){
        dl = ((3.0e5 * z)*(1 + (z/2)))/h;
    } else if (q > 0){
        d1 = (q*z)+((q-1)*(sqrt(1+((2*q)*z))-1));
        d2 = ((h*q)*q)/3.0e5;
        dl = d1/d2; 
    } else if(q < 0){
        omega0 = (2*(q+1))/3;
        aa = 1;
        bb = 1+z;
        success=false;
        s0=1.0e-10;
        npts=0;
        do{
            npts++;
            get_midpnt(get_funl,aa,bb,&s,npts);
            epsr=fabs(s-s0)/s0;
            if(epsr < 1.0e-4){
                success=true;
            } else {
                s0=s;
            }
        }while(!success);
        dd1=s;
        dd2=(3.0e5 * (1+z))/(h*sqrt(omega0));
        dl=dd1*dd2;
    }
    return dl;
}
// {F77} 
// {F77} c     ===========================================================================
// {F77}       REAL*8 FUNCTION FUNL(x)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     For non-zero cosmological constant
// {F77} c     ===========================================================================
// {F77}       real*8 x, omega0, omegainv
// {F77}       common /cosm/ omega0
// {F77}       omegainv = 1. / omega0
// {F77}       funl = 1. / sqrt(((x ** 3.) + omegainv) - 1.)
// {F77}       return
// {F77}       end
double get_funl(double x){
    double omegainv;
    omegainv = 1/omega0;
    return (1/sqrt(((x*x*x) + omegainv)-1));
}
// {F77} 
// {F77} 
// {F77} c     ===========================================================================
// {F77}       SUBROUTINE MIDPNT(func,a,b,s,n)
// {F77} c     ===========================================================================
// {F77}       INTEGER n
// {F77}       REAL*8 a,b,s,func
// {F77}       EXTERNAL func
// {F77}       INTEGER it,j
// {F77}       REAL*8 ddel,del,sum,tnm,x
// {F77}       if (n.eq.1) then
// {F77}          s=(b-a)*func(0.5*(a+b))
// {F77}       else
// {F77}          it=3**(n-2)
// {F77}          tnm=it
// {F77}          del=(b-a)/(3.*tnm)
// {F77}          ddel=del+del
// {F77}          x=a+0.5*del
// {F77}          sum=0.
// {F77}          do 11 j=1,it
// {F77}             sum=sum+func(x)
// {F77}             x=x+ddel
// {F77}             sum=sum+func(x)
// {F77}             x=x+del
// {F77}  11      continue
// {F77}          s=(s+(b-a)*sum/tnm)/3.
// {F77}       endif
// {F77}       return
// {F77}       END
void get_midpnt(double (*func)(double),double a,double b,double* s,double n){
    int it,j;
    double ddel,del,sum,tnm,x;
    if(n == 1){
        (*s)=(b-a)*((*func)(0.5*(a+b)));
    } else{
        it=pow(3,(n-2));
        tnm=it;
        del=(b-a)/(3*tnm);
        ddel=del+del;
        x=a+0.5*del;
        sum=0;
        for(j=0; j < it;j++){
            sum=sum+((*func)(x));
            x=x+ddel;
            sum=sum+((*func)(x));
            x=x+del;
        }
        (*s)=((*s)+(b-a)*sum/tnm)/3;
    }
}
// {F77} 
// {F77} c     ===========================================================================
// {F77}       REAL*8 FUNCTION COSMOL_C(h,omega,omega_lambda,q)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Returns cosmological constant = cosmol_c and parameter q
// {F77} c
// {F77} c     Omega is entered by the user
// {F77} c     omega=1.-omega_lambda
// {F77} c     ===========================================================================
// {F77}       real*8 h,omega,omega_lambda,q
// {F77} 
// {F77} c     Cosmological constant
// {F77}       cosmol_c=omega_lambda/(3.*h**2)
// {F77} c     Compute q=q0
// {F77}       if (omega_lambda.eq.0.) then
// {F77}          q=omega/2.
// {F77}       else
// {F77}          q=(3.*omega/2.) - 1.
// {F77}       endif
// {F77}       return
// {F77}       end
double get_cosmol_c(double h,double omega,double omega_lambda,double* q){
    if(omega_lambda == 0){
        *q=omega/2;
    }else{
        *q=(3*omega/2)-1;
    }
    return (omega_lambda/(3*h*h));
}
// {F77} 
// {F77} c     ===========================================================================
// {F77}       REAL*8 FUNCTION T(h, q, z, lamb)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Returns age of universe at redshift z
// {F77} c     ===========================================================================
// {F77}       implicit none
// {F77}       real*8 h, q, z, a, b, c, hh0, cosh, x, lamb
// {F77}       real*8 aa, bb, epsr, s0, s, funq, omega0
// {F77}       integer npts
// {F77}       logical success
// {F77}       external funq
// {F77}       common /cosm/ omega0
// {F77} 
// {F77} c     H = Ho in km/sec/Mpc
// {F77} c     Q = qo  (if problems with qo = 0, try 0.0001)
// {F77} 
// {F77}       a(q,z) = (sqrt(1. + ((2. * q) * z)) / (1. - (2. * q))) / (1. + z)
// {F77}       b(q) = q / (abs((2. * q) - 1.) ** 1.5)
// {F77}       c(q,z) = ((1. - (q * (1. - z))) / q) / (1. + z)
// {F77} 
// {F77}       cosh(x) = dlog10(x + sqrt((x ** 2) - 1.))
// {F77}       hh0 = h * 0.001022
// {F77} c     in (billion years)**(-1)
// {F77} 
// {F77}       if (lamb .ne. 0.0) then
// {F77}          omega0 = (2. * (q + 1.)) / 3.
// {F77}          aa = 0.
// {F77}          bb = 1. / (1. + z)
// {F77}          success=.false.
// {F77}          s0=1.e-10
// {F77}          npts=0
// {F77}          do while (.not.success)
// {F77}             npts=npts+1
// {F77}             call midpnt(funq,aa,bb,s,npts)
// {F77}             epsr=abs(s-s0)/s0
// {F77}             if (epsr.lt.1.e-4) then
// {F77}                success=.true.
// {F77}             else
// {F77}                s0=s
// {F77}             endif
// {F77}          enddo
// {F77}          t=s
// {F77}       else if (q .eq. 0.0) then
// {F77}          t = 1. / (1. + z)
// {F77}       else if (q .lt. 0.5) then
// {F77}          t = a(q,z) - (b(q) * cosh(c(q,z)))
// {F77}       else if (q .eq. 0.5) then
// {F77}          t = (2. / 3.) / ((1. + z) ** 1.5)
// {F77}       else
// {F77}          t = a(q,z) + (b(q) * cos(c(q,z)))
// {F77}       end if
// {F77} 
// {F77}       t = t / hh0
// {F77} 
// {F77}       return
// {F77}       end
// {F77} 
// {F77} 
// {F77} c     ===========================================================================
// {F77}       REAL*8 FUNCTION FUNQ(x)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     For non-zero cosmological constant
// {F77} c     ===========================================================================
// {F77}       real*8 x, omega0, omegainv
// {F77}       common /cosm/ omega0
// {F77}       omegainv = 1. / omega0
// {F77}       funq = sqrt(omegainv) / (x*sqrt((omegainv-1.)+(1./(x**3.))))
// {F77}       return
// {F77}       end
// {F77} 
// {F77} c     ===========================================================================
// {F77}       FUNCTION LARGO(A)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Returns significant length of string a
// {F77} c     ===========================================================================
// {F77}       Character*(*) a
// {F77}       largo=0
// {F77}       do i=1,len(a)
// {F77}          if (a(i:i).ne.' ') largo=i
// {F77}       enddo
// {F77}       return
// {F77}       end
// {F77} 
// {F77} 
// {F77} c     ===========================================================================
// {F77}       SUBROUTINE GET_BESTFIT_SED(i_opt,i_ir,dmstar,dfmu_aux,dz,outfile)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     Gets the total (UV-to-infrared) best-fit SED
// {F77} c
// {F77} c     Gets stellar spectrum and dust emission spectra from .bin files
// {F77} c     and adds them to get total SED, and writes output in .sed file
// {F77} c
// {F77} c        i_opt : index in the Optical library
// {F77} c         i_ir : index in the Infrared library
// {F77} c       dmstar : stellar mass (scaling)
// {F77} c     dfmu_aux : fmu_optical (to check if we got the right model)
// {F77} c           dz : redshift
// {F77} c      outfile : .sed file (output)
// {F77} c     ===========================================================================
// {F77}       implicit none
// {F77}       character infile1*80,infile2*80
// {F77}       character*10 outfile
// {F77}       integer nage,niw_opt,niw_ir,niw_tot
// {F77}       integer i,imod,nburst,k
// {F77}       integer i_opt,i_ir,indx
// {F77}       parameter(niw_tot=12817)
// {F77}       real tform,gamma,zmet,tauv0,mu,mstr1,mstr0,mstry,tlastburst,age_wm,age_wr
// {F77}       real fmu,ldtot,fbc,aux,lha,lhb
// {F77}       real wl_opt(6918),opt_sed(6918),opt_sed0(6918)
// {F77}       real wl_ir(6450),ir_sed(6450),irprop(8)
// {F77}       real age(1000),sfr(1000)
// {F77}       real fburst(5),ftot(5),sfrav(5)
// {F77}       real*8 dfmu_aux,dmstar,dz
// {F77}       real fmu_aux,mstar,z
// {F77}       real fmuopt(50000),fmuir(50000)
// {F77}       real fopt(6918),fopt0(6918),ldust
// {F77}       real fir(6450),fopt_int(niw_tot),fopt_int0(niw_tot)
// {F77}       real sedtot(niw_tot),wl(niw_tot)
// {F77}       real fir_new(niw_tot),fopt_new(niw_tot),fopt_aux(niw_tot)
// {F77}       real fopt_new0(niw_tot),fopt_aux0(niw_tot)
// {F77} 
// {F77}       mstar=sngl(dmstar)
// {F77}       fmu_aux=sngl(dfmu_aux)
// {F77}       z=sngl(dz)
// {F77} 
// {F77}       call getenv('OPTILIB',infile1)
// {F77}       call getenv('IRLIB',infile2)
// {F77} 
// {F77}       close (29)
// {F77}       open (29,file=infile1,status='old',form='unformatted')
// {F77} 
// {F77}       close (30)
// {F77}       open (30,file=infile2,status='old',form='unformatted')
// {F77} 
// {F77}       close (31)
// {F77}       open (31,file=outfile,status='unknown')
// {F77} 
// {F77}       write(31,*) '#...Main parameters of this model:'
// {F77}       write(31,319)
// {F77} 
// {F77} c     Read Optical SEDs and properties (1st file = models 1 to 25000)
// {F77}  7    read (29) niw_opt,(wl_opt(i),i=1,niw_opt)
// {F77}       indx=0
// {F77}       do imod=1,25000
// {F77}          indx=indx+1
// {F77}          read (29,end=1) tform,gamma,zmet,tauv0,mu,nburst,
// {F77}      .        mstr1,mstr0,mstry,tlastburst,
// {F77}      .        (fburst(i),i=1,5),(ftot(i),i=1,5),
// {F77}      .        age_wm,age_wr,aux,aux,aux,aux,
// {F77}      .        lha,lhb,aux,aux,ldtot,fmu,fbc
// {F77}          read (29) nage,(age(i),sfr(i),i=1,nage),(sfrav(i),i=1,5)
// {F77}          sfrav(3)=sfrav(3)/mstr1
// {F77}          read (29) (opt_sed(i),opt_sed0(i),i=1,niw_opt)
// {F77} 
// {F77}          if (indx.eq.i_opt) then
// {F77}             fmuopt(imod)=fmu
// {F77} c     Normalise Optical SED by stellar mass of the model
// {F77}             do i=1,niw_opt
// {F77}                fopt(i)=opt_sed(i)/mstr1
// {F77}                fopt0(i)=opt_sed0(i)/mstr1
// {F77}             enddo
// {F77}             ldust=ldtot/mstr1
// {F77}             goto 2
// {F77}          endif
// {F77}       enddo
// {F77} 
// {F77}  2    if (int(fmu*1000).eq.int(fmu_aux*1000)
// {F77}      +     .or.int(fmu*1000).eq.(int(fmu_aux*1000)-1)
// {F77}      +     .or.int(fmu*1000).eq.(int(fmu_aux*1000)+1)) then
// {F77}          write(*,*) 'optical... done'
// {F77}       endif
// {F77}       if (int(fmu*1000).ne.int(fmu_aux*1000)
// {F77}      +     .and.int(fmu*1000).ne.(int(fmu_aux*1000)-1)
// {F77}      +     .and.int(fmu*1000).ne.(int(fmu_aux*1000)+1) ) then
// {F77}          call getenv('OPTILIBIS',infile1)
// {F77}          close(29)
// {F77}          open (29,file=infile1,status='old',form='unformatted')
// {F77}          goto 7
// {F77}       endif
// {F77} 
// {F77} c     Read Infrared SEDs and properties
// {F77}       read (30) niw_ir,(wl_ir(i),i=1,niw_ir)
// {F77}       do imod=1,50000
// {F77}          read (30) (irprop(i),i=1,8)
// {F77}          read (30) (ir_sed(i),i=1,niw_ir)
// {F77}          fmuir(imod)=irprop(1)
// {F77}          if (imod.eq.i_ir) then
// {F77}             do i=1,niw_ir
// {F77}                fir(i)=ir_sed(i)
// {F77}             enddo
// {F77}             goto 3
// {F77}          endif
// {F77}       enddo
// {F77}  3    write(*,*) 'infrared... done'
// {F77} 
// {F77}       write(*,*) 'Ldust/L_sun= ',mstar*ldust
// {F77} 
// {F77}       write(31,315)
// {F77}  315  format('#...fmu(Opt).....fmu(IR)....tform/yr.......gamma',
// {F77}      +     '........Z/Zo........tauV..........mu.....M*/Msun',
// {F77}      +     '....SFR(1e8).....Ld/Lsun')
// {F77}       write(31,316) fmu,irprop(1),tform,gamma,zmet,tauv0,mu,mstar,
// {F77}      +     sfrav(3),ldust*mstar
// {F77}  316  format(0p2f12.3,1pe12.3,0p4f12.3,1p3e12.3)
// {F77} 
// {F77}       write(31,319)
// {F77}       write(31,317)
// {F77}  317  format('#...xi_C^ISM....T_W^BC/K...T_C^ISM/K...xi_PAH^BC',
// {F77}      +     '...xi_MIR^BC.....xi_W^BC....Mdust/Mo')
// {F77}       write(31,318) (irprop(k),k=2,7),irprop(8)*ldust*mstar
// {F77}  318  format(0p6f12.3,1pe12.3)
// {F77} 
// {F77}       write(31,319)
// {F77}  319  format('#')
// {F77}       write(31,314)
// {F77}  314  format('#...Spectral Energy Distribution [lg(L_lambda/LoA^-1)]:')
// {F77}       write(31,312)
// {F77}  312  format('#...lg(lambda/A)...Attenuated...Unattenuated')
// {F77} 
// {F77} 
// {F77} c     Wavelength vectors are not the same for the Optical and IR spectra
// {F77} c     Make new wavelength vector by combining them
// {F77}       do i=1,6367
// {F77}          wl(i)=wl_opt(i)
// {F77}          fir_new(i)=0.
// {F77}       enddo
// {F77}       do i=6368,niw_tot
// {F77}          wl(i)=wl_ir(i-6367)
// {F77}          fir_new(i)=fir(i-6367)
// {F77}       enddo
// {F77} 
// {F77} c     Interpolate the optical SED in the new wavelength grid (do it in log)
// {F77}       do i=1,niw_opt
// {F77}          fopt_aux(i)=log10(fopt(i))
// {F77}          fopt_aux0(i)=log10(fopt0(i))
// {F77}       enddo
// {F77} 
// {F77}       do i=1,niw_tot
// {F77}          call interp(wl_opt,fopt_aux,niw_opt,4,wl(i),fopt_int(i))
// {F77}          fopt_new(i)=10**(fopt_int(i))
// {F77}          call interp(wl_opt,fopt_aux0,niw_opt,4,wl(i),fopt_int0(i))
// {F77}          fopt_new0(i)=10**(fopt_int0(i))
// {F77}       enddo
// {F77} 
// {F77} c     Final SEDs - write output file
// {F77}       do i=1,niw_tot-1
// {F77}          sedtot(i)=fopt_new(i)+ldust*fir_new(i)
// {F77}          sedtot(i)=mstar*sedtot(i)
// {F77}          fopt_new0(i)=fopt_new0(i)*mstar
// {F77}          write(31,311) log10(wl(i)*(1.+z)),log10(sedtot(i)/(1.+z)),
// {F77}      +        log10(fopt_new0(i)/(1.+z))
// {F77}       enddo
// {F77}  311  format(3f15.6)
// {F77} 
// {F77}  1    stop
// {F77}       end
// {F77} 
// {F77} c     ===========================================================================
// {F77}       SUBROUTINE INTERP(x,y,npts,nterms,xin,yout)
// {F77} c     ---------------------------------------------------------------------------
// {F77} c     INTERPOLATOR
// {F77} c     description of parameters
// {F77} c     x      - array of data points for independent variable
// {F77} c     y      - array of data points for dependent variable
// {F77} c     npts   - number of pairs of data points
// {F77} c     nterms - number of terms in fitting polynomial
// {F77} c     xin    - input value of x
// {F77} c     yout   - interplolated value of y
// {F77} c
// {F77} c     comments
// {F77} c     dimension statement valid for nterms up to 10
// {F77} c     value of nterms may be modified by the program
// {F77} c     ===========================================================================
// {F77}       implicit real (a-h,o-z)
// {F77}       integer npts
// {F77}       dimension x(npts),y(npts)
// {F77}       dimension delta(10),a(10)
// {F77} c     search for appropriate value of x(1)
// {F77}  11   do 19 i=1,npts
// {F77}          if (xin-x(i)) 13,17,19
// {F77}  13      i1 = i-nterms/2
// {F77}          if (i1) 15,15,21
// {F77}  15      i1 = 1
// {F77}          go to 21
// {F77}  17      yout = y(i)
// {F77}  18      go to 61
// {F77}  19   continue
// {F77}       i1 = npts - nterms + 1
// {F77}  21   i2 = i1 + nterms -1
// {F77}       if (npts-i2) 23,31,31
// {F77}  23   i2 = npts
// {F77}       i1 = i2 - nterms +1
// {F77}  25   if (i1) 26,26,31
// {F77}  26   i1 = 1
// {F77}  27   nterms = i2 - i1 + 1
// {F77} 
// {F77} c     evaluate deviations delta
// {F77}  31   denom = x(i1+1) - x(i1)
// {F77}       deltax = (xin-x(i1))/denom
// {F77}       do 35 i=1,nterms
// {F77}          ix = i1 + i - 1
// {F77}  35      delta(i) = (x(ix)-x(i1))/denom
// {F77} 
// {F77} c     accumulate coefficients a
// {F77}  40      a(1) = y(i1)
// {F77}  41      do 50 k=2,nterms
// {F77}             prod = 1.0
// {F77}             sum = 0.0
// {F77}             imax = k-1
// {F77}             ixmax = i1 + imax
// {F77}             do 49 i=1,imax
// {F77}                j = k-i
// {F77}                prod = prod*(delta(k)-delta(j))
// {F77}  49            sum = sum - a(j)/prod
// {F77}  50            a(k) = sum + y(ixmax)/prod
// {F77} 
// {F77} c     accumulate sum of expansion
// {F77}  51            sum = a(1)
// {F77}                do 57 j=2,nterms
// {F77}                   prod = 1.0
// {F77}                   imax = j-1
// {F77}                   do 56 i=1,imax
// {F77}  56                  prod = prod*(deltax-delta(i))
// {F77}  57                  sum = sum + a(j)*prod
// {F77}  60                  yout = sum
// {F77} 
// {F77}  61                  return
// {F77}                      end
// {F77} 
// {F77} 
