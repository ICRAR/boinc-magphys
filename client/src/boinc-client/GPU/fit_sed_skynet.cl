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

typedef struct clid {
    // sfh and ir index combo this model identified.
    int i_sfh; 
    int i_ir;
} clid_t;

typedef struct clmodel {
    // Scaling factor.
    double a;
    // chi^2 values.
    double chi2;
    double chi2_opt;
    double chi2_ir;
    // Probability
    double prob;
    // MPDF ibins
    int ibin_psfh;
    int ibin_pir; 
    int ibin_pmu; 
    int ibin_ptv; 
    int ibin_ptvism;
    int ibin_pssfr;
    int ibin_psfr;
    int ibin_pa;
    int ibin_pldust;
    int ibin_ptbg1;
    int ibin_ptbg2;
    int ibin_pism;
    int ibin_pxi1;
    int ibin_pxi2;
    int ibin_pxi3;
    int ibin_pmd; 
}clmodel_t;

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
    double a_max;
    double a_min;
    double sfr_max;
    double sfr_min;
    double ld_max;
    double ld_min;
    double md_max;
    double md_min;
    int nfilt;
    int nfilt_sfh;
    int nfilt_mix;
    int i_gal;

} clvar_t;

__kernel void fit( const int clm,
                       __global clid_t* ids,
                       __global clmodel_t* models,
                       __global clmod_t* mods,
                       __constant clvar_t* var,
                       __global double* flux_obs,
                       __global double* flux_sfh,
                       __global double* flux_ir,
                       __global double* w
                      )
{                                                              


    int id = get_global_id(0);                                 

    if (id < clm){                                                

        int k = 0;
        double num = 0;
        double den = 0;
        int i_sfh = ids[id].i_sfh;
        int i_ir = ids[id].i_ir;
        int nfilt = var->nfilt;
        int nfilt_sfh = var->nfilt_sfh;
        int nfilt_mix = var->nfilt_mix;
        int i_gal = var->i_gal;

        __global clmodel_t *m = &models[id];
        __global clmod_t *msfh = &mods[i_sfh];
        __global clmod_t *mir = &mods[i_ir];

        double flux_mod[NMAX];
        // Build the model flux array.
        for(k=0; k < nfilt_sfh-nfilt_mix; k++){
            flux_mod[k]=flux_sfh(k,i_sfh);
        }    
        for(k=nfilt_sfh-nfilt_mix; k<nfilt_sfh; k++){
            flux_mod[k]=flux_sfh(k,i_sfh)+msfh->ldust*flux_ir(k-nfilt_sfh+nfilt_mix,i_ir);
        }    
        for(k=nfilt_sfh; k<nfilt; k++){
            flux_mod[k]=msfh->ldust*flux_ir(k-nfilt_sfh+nfilt_mix,i_ir);
        }    

        // Compute the scaling factor "a".
        for(k=0; k<nfilt; k++){
            if(flux_obs(k,i_gal) > 0) { 
                num=num+(flux_mod[k]*flux_obs(k,i_gal)*w(k,i_gal));
                den=den+(pow(flux_mod[k],2)*w(k,i_gal));
            }    
        }    
    
        double a = num/den;
        m->a= a;

        // Compute chi^2 goodness of fit.
        double chi2 = 0;
        double chi2_opt = 0;
        double chi2_ir = 0;
        for(k=0;k<nfilt_sfh;k++){
            if(flux_obs(k,i_gal) > 0){
                chi2=chi2+((pow(flux_obs(k,i_gal)-(a*flux_mod[k]),2))*w(k,i_gal));
                chi2_opt=chi2;
            }
        }
        if(chi2 < 600){
            for(k=nfilt_sfh;k<nfilt;k++){
                if (flux_obs(k,i_gal) > 0){
                    chi2=chi2+((pow(flux_obs(k,i_gal)-(a*flux_mod[k]),2))*w(k,i_gal));
                    chi2_ir=chi2_ir+((pow(flux_obs(k,i_gal)-(a*flux_mod[k]),2))*w(k,i_gal));
                }
            }
        }
        m->chi2=chi2;
        m->chi2_opt=chi2_opt;
        m->chi2_ir=chi2_ir;

        // Calculate probability.
        double prob = exp(-0.5*m->chi2);
        m->prob = prob;

        // Marginal probability density functions

        int ibin;
        double aux;
        
        // f_mu (SFH)
        ibin=msfh->i_fmu_sfh;
        ibin=max(0,min(ibin,var->nbin_fmu-1));
        m->ibin_psfh = ibin;

        // f_mu (IR)
        ibin=mir->i_fmu_ir;
        ibin = max(0,min(ibin,var->nbin_fmu-1));
        m->ibin_pir = ibin;

        // mu
        ibin=msfh->i_mu;
        ibin=max(0,min(ibin,var->nbin_mu-1));
        m->ibin_pmu = ibin;

        // tauV
        ibin=msfh->i_tauv;
        ibin=max(0,min(ibin,var->nbin_tv-1));
        m->ibin_ptv=ibin;

        // tvism
        ibin=msfh->i_tvism;
        ibin=max(0,min(ibin,var->nbin_tv-1));
        m->ibin_ptvism=ibin;

        // sSFR_0.1Gyr
        ibin=msfh->i_lssfr;
        ibin=max(0,min(ibin,var->nbin_sfr-1));
        m->ibin_pssfr=ibin;

        // Mstar
        a=log10(a);
        aux=((a-var->a_min)/(var->a_max-var->a_min)) * var->nbin_a;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_a-1));
        m->ibin_pa=ibin;

        // SFR_0.1Gyr
        aux=((msfh->lssfr+a-var->sfr_min)/(var->sfr_max-var->sfr_min))* var->nbin_sfr;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_sfr-1));
        m->ibin_psfr=ibin;

        // Ldust
        aux=((msfh->logldust+a-var->ld_min)/(var->ld_max-var->ld_min))* var->nbin_ld;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_ld-1));
        m->ibin_pldust=ibin;
                        
        // xi_C^tot
        ibin=mir->i_fmu_ism;
        ibin=max(0,min(ibin,var->nbin_fmu_ism-1));
        m->ibin_pism=ibin;

        // T_C^ISM
        ibin=mir->i_tbg1;
        ibin=max(0,min(ibin,var->nbin_tbg1-1));
        m->ibin_ptbg1=ibin;

        // T_W^BC
        ibin=mir->i_tbg2;
        ibin=max(0,min(ibin,var->nbin_tbg2-1));
        m->ibin_ptbg2=ibin;

        // xi_PAH^tot
        ibin=mir->i_xi1;
        ibin=max(0,min(ibin,var->nbin_xi-1));
        m->ibin_pxi1=ibin;

        // xi_MIR^tot
        ibin=mir->i_xi2;
        ibin=max(0,min(ibin,var->nbin_xi-1));
        m->ibin_pxi2=ibin;

        // xi_W^tot
        ibin=mir->i_xi3;
        ibin=max(0,min(ibin,var->nbin_xi-1));
        m->ibin_pxi3=ibin;

        // Mdust
        aux=log10(mir->mdust*msfh->ldust*pow(10.0,a));
        aux=((aux-var->md_min)/(var->md_max-var->md_min))*var->nbin_md;
        ibin=(int)(aux);
        ibin=max(0,min(ibin,var->nbin_md-1));
        m->ibin_pmd=ibin;
    }
}                                                              
