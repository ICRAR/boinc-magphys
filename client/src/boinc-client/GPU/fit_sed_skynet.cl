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

typedef struct clmodel {
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
}clmodel_t;

typedef struct clprob {
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
} clprob_t;

typedef struct clmod {
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

    double lssfr;
    double logldust;
    double mdust;
    double ldust;
    double lmdust;
} clmod_t;

typedef struct clvar {
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

    int a_max;
    int a_min;
    int sfr_max;
    int sfr_min;
    int ld_max;
    int ld_min;
    int md_max;
    int md_min;

} clvar_t;

__kernel void compute( __global clmodel_t* models,
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
                       __global clprob_t* probs,
                       __global clmod_t* mods,
                       __global clvar_t* var,
                       __global double* lmdust
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
        double a = num/den;
        models[id].a= a;
        for(k=0;k<nfilt_sfh;k++){
            if(flux_obs(k,i_gal) > 0){
                models[id].chi2=models[id].chi2+((pow(flux_obs(k,i_gal)-(a*flux_mod[k]),2))*w(k,i_gal));
                models[id].chi2_opt=models[id].chi2;
            }
        }
        if(models[id].chi2 < 600){
            for(k=nfilt_sfh;k<nfilt;k++){
                if (flux_obs(k,i_gal) > 0){
                    models[id].chi2=models[id].chi2+((pow(flux_obs(k,i_gal)-(a*flux_mod[k]),2))*w(k,i_gal));
                    models[id].chi2_ir=models[id].chi2_ir+((pow(flux_obs(k,i_gal)-(a*flux_mod[k]),2))*w(k,i_gal));
                }
            }
        }

        // Calculate probability.
        double prob = exp(-0.5*models[id].chi2);
        models[id].prob = prob;

        // Marginal probability density functions

        int ibin;
        double aux;
        
        // f_mu (SFH)
        ibin=mods[i_sfh].i_fmu_sfh;
        ibin=max(0,min(ibin,var->nbin_fmu-1));
        probs[ibin].psfh=probs[ibin].psfh+models[id].prob;

        // f_mu (IR)
        ibin=mods[i_ir].i_fmu_ir;
        ibin = max(0,min(ibin,var->nbin_fmu-1));
        probs[ibin].pir=probs[ibin].pir+prob;

        // mu
        ibin=mods[i_sfh].i_mu;
        ibin=max(0,min(ibin,var->nbin_mu-1));
        probs[ibin].pmu=probs[ibin].pmu+prob;

        // tauV
        ibin=mods[i_sfh].i_tauv;
        ibin=max(0,min(ibin,var->nbin_tv-1));
        probs[ibin].ptv=probs[ibin].ptv+prob;

        // tvism
        ibin=mods[i_sfh].i_tvism;
        ibin=max(0,min(ibin,var->nbin_tv-1));
        probs[ibin].ptvism=probs[ibin].ptvism+prob;

        // sSFR_0.1Gyr
        ibin=mods[i_sfh].i_lssfr;
        ibin=max(0,min(ibin,var->nbin_sfr-1));
        probs[ibin].pssfr=probs[ibin].pssfr+prob;

        // Mstar
        a=log10(a);
        aux=((a-var->a_min)/(var->a_max-var->a_min)) * var->nbin_a;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_a-1));
        probs[ibin].pa=probs[ibin].pa+prob;

        // SFR_0.1Gyr
        aux=((mods[i_sfh].lssfr+a-var->sfr_min)/(var->sfr_max-var->sfr_min))* var->nbin_sfr;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_sfr-1));
        probs[ibin].psfr=probs[ibin].psfr+prob;

        // Ldust
        aux=((mods[i_sfh].logldust+a-var->ld_min)/(var->ld_max-var->ld_min))* var->nbin_ld;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_ld-1));
        probs[ibin].pldust=probs[ibin].pldust+prob;
                        
        // xi_C^tot
        ibin=mods[i_ir].i_fmu_ism;
        ibin=max(0,min(ibin,var->nbin_fmu_ism-1));
        probs[ibin].pism=probs[ibin].pism+prob;

        // T_C^ISM
        ibin=mods[i_ir].i_tbg1;
        ibin=max(0,min(ibin,var->nbin_tbg1-1));
        probs[ibin].ptbg1=probs[ibin].ptbg1+prob;

        // T_W^BC
        ibin=mods[i_ir].i_tbg2;
        ibin=max(0,min(ibin,var->nbin_tbg2-1));
        probs[ibin].ptbg2=probs[ibin].ptbg2+prob;

        // xi_PAH^tot
        ibin=mods[i_ir].i_xi1;
        ibin=max(0,min(ibin,var->nbin_xi-1));
        probs[ibin].pxi1=probs[ibin].pxi1+prob;

        // xi_MIR^tot
        ibin=mods[i_ir].i_xi2;
        ibin=max(0,min(ibin,var->nbin_xi-1));
        probs[ibin].pxi2=probs[ibin].pxi2+prob;

        // xi_W^tot
        ibin=mods[i_ir].i_xi3;
        ibin=max(0,min(ibin,var->nbin_xi-1));
        probs[ibin].pxi3=probs[ibin].pxi3+prob;

        // Mdust
        lmdust[i_ir]=log10(mods[i_ir].mdust*mods[i_sfh].ldust*pow(10.0,a));
        aux=((lmdust[i_ir]-var->md_min)/(var->md_max-var->md_min))*var->nbin_md;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_md-1));
        probs[ibin].pmd=probs[ibin].pmd+prob;
    }
}                                                              
