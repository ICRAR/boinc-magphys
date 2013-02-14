#pragma OPENCL EXTENSION cl_khr_fp64 : enable

#define NMAX 50
#define GALMAX 5000
#define NMOD 50001
#define NPROP_SFH 24
#define NPROP_IR 8
#define NZMAX 5000
#define NBINMAX1 3000
#define NBINMAX2 300
#define MIN_HPBV 0.00001

#define flux_obs(x,y) *(flux_obs+(x*GALMAX)+y)
#define flux_sfh(x,y) *(flux_sfh+(x*NMOD)+y)
#define flux_ir(x,y) *(flux_ir+(x*NMOD)+y)
#define w(x,y) *(w+(x*GALMAX)+y)

typedef struct model {
    // sfh and ir index combo this model identified.
    int sfh; 
    int ir;
    // Scaling factor.
    double a;
    // chi^2 values.
    double chi2;
    double chi2_opt;
    double chi2_ir;
    // Probability
    double prob;
}model_t;

typedef struct prob {
   double psfh;
   double pir; 
   double pmu; 
   double ptv; 
   double ptvism;
   double pssfr;
   double psfr;
   double pa;
   double pldust;
   double ptbg1;
   double ptbg2;
   double pism;
   double pxi1;
   double pxi2;
   double pxi3;
   double pmd; 
} prob_t;

typedef struct index {
    // SFH
    double i_fmu_sfh;
    double i_mu;
    double i_tauv;
    double i_tvism;
    double i_lssfr;
    // IR
    double i_fmu_ir;
    double i_fmu_ism;
    double i_tbg1;
    double i_tbg2;
    double i_xi1;
    double i_xi2;
    double i_xi3;
} index_t;

typedef struct nbin {
    int nbin_fmu;
    int nbin_mu;
    int nbin_tv;
    int nbin_sfr;
    int nbin_a;
    int nbin_ld;
    int nbin_fmu_ism;
    int nbin_tbg1;
    int nbin_tbg2;
    int nbin_xi;
    int nbin_md;
} nbin_t;

__kernel void compute( __global model_t* models,
                       const unsigned int n,
                       const int i_gal,
                       const int nfilt,
                       const int nfilt_sfh,
                       const int nfilt_mix, 
                       __global double* ldust,
                       __global double* flux_obs,
                       __global double* flux_sfh,
                       __global double* flux_ir,
                       __global double* w, 
                       __global prob_t* probs,
                       __global index_t* indexes,
                       __global nbin_t* nbin
                      )
{                                                              

    int id = get_global_id(0);                                 

    int k = 0;
    double num;
    double den;

    int i_sfh = models[id].sfh;
    int i_ir = models[id].ir;

    double flux_mod[NMAX];

    if (id < n){                                                
        // Build the model flux array.
        for(k=0; k < nfilt_sfh-nfilt_mix; k++){
            flux_mod[k]=flux_sfh(k,i_sfh);
        }    
        for(k=nfilt_sfh-nfilt_mix; k<nfilt_sfh; k++){
            flux_mod[k]=flux_sfh(k,i_sfh)+ldust[i_sfh]*flux_ir(k-nfilt_sfh+nfilt_mix,i_ir);
        }    
        for(k=nfilt_sfh; k<nfilt; k++){
            flux_mod[k]=ldust[i_sfh]*flux_ir(k-nfilt_sfh+nfilt_mix,i_ir);
        }    

        // Compute the scaling factor "a".
        for(k=0; k<nfilt; k++){
            if(flux_obs(k,i_gal) > 0) { 
                num=num+(flux_mod[k]*flux_obs(k,i_gal)*w(k,i_gal));
                den=den+(pow(flux_mod[k],2)*w(k,i_gal));
            }    
        }    
    
        // Compute chi^2 goodness of fit.
        models[id].a=num/den;
        for(k=0;k<nfilt_sfh;k++){
            if(flux_obs(k,i_gal) > 0){
                models[id].chi2=models[id].chi2+((pow(flux_obs(k,i_gal)-(models[id].a*flux_mod[k]),2))*w(k,i_gal));
                models[id].chi2_opt=models[id].chi2;
            }
        }
        if(models[id].chi2 < 600){
            for(k=nfilt_sfh;k<nfilt;k++){
                if (flux_obs(k,i_gal) > 0){
                    models[id].chi2=models[id].chi2+((pow(flux_obs(k,i_gal)-(models[id].a*flux_mod[k]),2))*w(k,i_gal));
                    models[id].chi2_ir=models[id].chi2_ir+((pow(flux_obs(k,i_gal)-(models[id].a*flux_mod[k]),2))*w(k,i_gal));
                }
            }
        }

        // Calculate probability.
        models[id].prob=exp(-0.5*models[id].chi2);

        // Marginal probability density functions
        
/********************************************************************** 
    TODO - IMPLEMENT

        // f_mu (SFH)
        ibin=i_fmu_sfh[i_sfh];
        ibin=max(0,min(ibin,nbin_fmu-1));
        psfh[ibin]=psfh[ibin]+prob;

        // f_mu (IR)
        ibin=i_fmu_ir[i_ir];
        ibin = max(0,min(ibin,nbin_fmu-1));
        pir[ibin]=pir[ibin]+prob;

        // mu
        ibin=i_mu[i_sfh];
        ibin=max(0,min(ibin,nbin_mu-1));
        pmu[ibin]=pmu[ibin]+prob;

        // tauV
        ibin=i_tauv[i_sfh];
        ibin=max(0,min(ibin,nbin_tv-1));
        ptv[ibin]=ptv[ibin]+prob;

        // tvism
        ibin=i_tvism[i_sfh];
        ibin=max(0,min(ibin,nbin_tv-1));
        ptvism[ibin]=ptvism[ibin]+prob;

        // sSFR_0.1Gyr
        ibin=i_lssfr[i_sfh];
        ibin=max(0,min(ibin,nbin_sfr-1));
        pssfr[ibin]=pssfr[ibin]+prob;

        // Mstar
        a=log10(a);
        aux=((a-a_min)/(a_max-a_min)) * nbin_a;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,nbin_a-1));
        pa[ibin]=pa[ibin]+prob;

        // SFR_0.1Gyr
        aux=((lssfr[i_sfh]+a-sfr_min)/(sfr_max-sfr_min))* nbin_sfr;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,nbin_sfr-1));
        psfr[ibin]=psfr[ibin]+prob;

        // Ldust
        aux=((logldust[i_sfh]+a-ld_min)/(ld_max-ld_min))* nbin_ld;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,nbin_ld-1));
        pldust[ibin]=pldust[ibin]+prob;
                        
        // xi_C^tot
        ibin=i_fmu_ism[i_ir];
        ibin=max(0,min(ibin,nbin_fmu_ism-1));
        pism[ibin]=pism[ibin]+prob;

        // T_C^ISM
        ibin=i_tbg1[i_ir];
        ibin=max(0,min(ibin,nbin_tbg1-1));
        ptbg1[ibin]=ptbg1[ibin]+prob;

        // T_W^BC
        ibin=i_tbg2[i_ir];
        ibin=max(0,min(ibin,nbin_tbg2-1));
        ptbg2[ibin]=ptbg2[ibin]+prob;

        // xi_PAH^tot
        ibin=i_xi1[i_ir];
        ibin=max(0,min(ibin,nbin_xi-1));
        pxi1[ibin]=pxi1[ibin]+prob;

        // xi_MIR^tot
        ibin=i_xi2[i_ir];
        ibin=max(0,min(ibin,nbin_xi-1));
        pxi2[ibin]=pxi2[ibin]+prob;

        // xi_W^tot
        ibin=i_xi3[i_ir];
        ibin=max(0,min(ibin,nbin_xi-1));
        pxi3[ibin]=pxi3[ibin]+prob;

        // Mdust
        lmdust[i_ir]=log10(mdust[i_ir]*ldust[i_sfh]*pow(10.0,a));
        aux=((lmdust[i_ir]-md_min)/(md_max-md_min))*nbin_md;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,nbin_md-1));
        pmd[ibin]=pmd[ibin]+prob;
*******************************************************************/
    }
}                                                              
