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
                       __global double* w 
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

    }
}                                                              
