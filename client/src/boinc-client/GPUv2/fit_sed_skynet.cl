// Enable double precision.																													
#pragma OPENCL EXTENSION cl_khr_fp64 : enable																									

// Some constants copied from main host program.																								
#define NMAX 56
#define NMOD 50016
#define blockSize 256	//BlockSize for sumprob

// Struct containing var constants read by kernel																								
// threads.										 	 																						
typedef struct clconstants {
	int nbin_sfr;
	int nbin_a;
	int nbin_ld;
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
	double df;
	int n_sfh;
	int n_ir;
} clconstants_t;

// Struct to define arrays of indexes and models																								
// used by kernel threads.								 																						
typedef struct clmod_sfh {
	double lssfr;
	double logldust;
	double ldust;
	double flux_sfh[NMAX];
} clmod_sfh_t;

typedef struct clmod_ir {
	double mdust;
	double flux_ir[NMAX];
} clmod_ir_t;

__kernel void fit(const int ci_idsSize,
	__constant clconstants_t* ct_clconstants,
	__global const clmod_sfh_t* mods_sfh,
	__global const clmod_ir_t* mods_ir,
	__global const double* flux_obs,
	__global const double* w,
	__global const double* flux_obs_mask,
	__global const double* filt_sfh_mask,
	__global const double* filt_ir_mask,
	__global const ushort* cl_sfh,
	__global const ushort* cl_ir,
	__global double* cl_chi2,
	__global double* cl_prob,
	__global ushort* ibin_pa,
	__global ushort* ibin_psfr,
	__global ushort* ibin_pldust,
	__global ushort* ibin_pmdust
	)
{
	// Get kernel thread id for matching with array indexes.																					
	int global_index = get_global_id(0);
	int local_index = get_local_id(0);

	// Only continue if our id is less than batch max. The id can sometimes		 															
	// be greater if the global work size is greater than values we're working with. 															
	if (global_index < ci_idsSize){

		// Set some variables in private memory space.																							
		ushort k = 0;
		double num = 0;
		double den = 0;
		ushort i_sfh = cl_sfh[global_index];
		ushort i_ir = cl_ir[global_index];
		ushort nfilt = ct_clconstants->nfilt;
		ushort nfilt_sfh = ct_clconstants->nfilt_sfh;
		ushort nfilt_mix = ct_clconstants->nfilt_mix;
		__global clmod_sfh_t *msfh = &mods_sfh[i_sfh];
		__global clmod_ir_t *mir = &mods_ir[i_ir];

		double flux_mod[NMAX];
		// Build the model flux array. ldust is already part of flux_ir																											
		for (k = 0; k < nfilt_sfh - nfilt_mix; k++){
			flux_mod[k] = msfh->flux_sfh[k];
		}
		for (k = nfilt_sfh - nfilt_mix; k < nfilt_sfh; k++){
			flux_mod[k] = msfh->flux_sfh[k] + mir->flux_ir[k];
		}
		for (k = nfilt_sfh; k < nfilt; k++){
			flux_mod[k] = mir->flux_ir[k];
		}

		// Compute the scaling factor a.						 																				
		for (k = 0; k<nfilt; k++){
			if (flux_obs[k]>0) {
				num = num + (flux_mod[k] * flux_obs[k] * w[k]);
				den = den + ((flux_mod[k] * flux_mod[k]) * w[k]);
			}
		}

		double a = num / den;

		// Compute chi^2 goodness of fit.						 																				
		double chi2 = 0;
		for (k = 0; k < nfilt_sfh; k++){
			if (flux_obs[k]>0) {
				chi2 = chi2 + ( (  (flux_obs[k] - (a * flux_mod[k]))*(flux_obs[k] - (a * flux_mod[k])) ) * w[k]);
			}
		}
		if (chi2 < 600){
			for (k = nfilt_sfh; k < nfilt; k++){
				if (flux_obs[k]>0) {
					chi2 = chi2 + ((pow(flux_obs[k] - (a * flux_mod[k]), 2)) * w[k]);
				}
			}
		}

		// Calculate probability.							 																					
		double prob = exp(-0.5 * chi2);

		cl_chi2[global_index] = chi2;
		cl_prob[global_index] = prob;

		// Calculate marginal probability density functions. Instead			 																
		// of writing prob values, we instead write the index of bin			 																
		// for non-parallelized processing.						 																			
		int ibin;
		ushort usbin;
		double aux;

		a = log10(a);

		// Mstar									 																							
		aux = ((a - ct_clconstants->a_min) / (ct_clconstants->a_max - ct_clconstants->a_min)) * ct_clconstants->nbin_a;
		ibin = (int)(aux);
		usbin = max(0, min(ibin, ct_clconstants->nbin_a - 1));
		ibin_pa[global_index] = usbin;

		// SFR_0.1Gyr									 																						
		aux = ((msfh->lssfr + a - ct_clconstants->sfr_min) / (ct_clconstants->sfr_max - ct_clconstants->sfr_min))* ct_clconstants->nbin_sfr;
		ibin = (int)(aux);
		usbin = max(0, min(ibin, ct_clconstants->nbin_sfr - 1));
		ibin_psfr[global_index] = usbin;

		// Ldust									 																							
		aux = ((msfh->logldust + a - ct_clconstants->ld_min) / (ct_clconstants->ld_max - ct_clconstants->ld_min))* ct_clconstants->nbin_ld;
		ibin = (int)(aux);
		usbin = max(0, min(ibin, ct_clconstants->nbin_ld - 1));
		ibin_pldust[global_index] = usbin;

		// Mdust									 																							
		aux = log10(mir->mdust * msfh->ldust * exp10(a));
		aux = ((aux - ct_clconstants->md_min) / (ct_clconstants->md_max - ct_clconstants->md_min)) * ct_clconstants->nbin_md;
		ibin = (int)(aux);
		usbin = max(0, min(ibin, ct_clconstants->nbin_md - 1));
		ibin_pmdust[global_index] = usbin;

	} //if global_index < ci_idsSize											 																
}

__kernel void sumprob(int ci_idsSize, __global double *g_idata, __global double *g_odata, __local volatile double* sdata)
{
	// perform first level of reduction,
	// reading from global memory, writing to shared memory
	unsigned int tid = get_local_id(0);
	unsigned int i = get_group_id(0)*(get_local_size(0) * 2) + get_local_id(0);
	unsigned int gridSize = blockSize * 2 * get_num_groups(0);
	sdata[tid] = 0;

	// we reduce multiple elements per thread.  The number is determined by the 
	// number of active thread blocks. More blocks will result
	// in a larger gridSize and therefore fewer elements per thread
	while (i < ci_idsSize)
	{
		sdata[tid] += g_idata[i];
		// this is optimized away for powerOf2 sized arrays
		sdata[tid] += g_idata[i + blockSize];
		i += gridSize;
	}

	barrier(CLK_LOCAL_MEM_FENCE);

	// do reduction in shared mem
	if (blockSize >= 512) { if (tid < 256) { sdata[tid] += sdata[tid + 256]; } barrier(CLK_LOCAL_MEM_FENCE); }
	if (blockSize >= 256) { if (tid < 128) { sdata[tid] += sdata[tid + 128]; } barrier(CLK_LOCAL_MEM_FENCE); }
	if (blockSize >= 128) { if (tid <  64) { sdata[tid] += sdata[tid + 64]; } barrier(CLK_LOCAL_MEM_FENCE); }

	if (tid < 32)
	{
		if (blockSize >= 64) { sdata[tid] += sdata[tid + 32]; }
		if (blockSize >= 32) { sdata[tid] += sdata[tid + 16]; }
		if (blockSize >= 16) { sdata[tid] += sdata[tid + 8]; }
		if (blockSize >= 8) { sdata[tid] += sdata[tid + 4]; }
		if (blockSize >= 4) { sdata[tid] += sdata[tid + 2]; }
		if (blockSize >= 2) { sdata[tid] += sdata[tid + 1]; }
	}

	// write result for this block to global mem 
	if (tid == 0) g_odata[get_group_id(0)] = sdata[0];
}

__kernel void minchi(int ci_idsSize, __global const ushort* cl_sfh,
	__global const ushort* cl_ir, __global double *g_idata,
	__global double *g_odata, __global ushort *g_o_sfh, __global ushort *g_o_ir,
	__local volatile double* sdata, __local volatile ushort* s_sfh, __local volatile ushort* s_ir)
{
	//Need to added checks if chi2 is equal then use lowest sfh and ir

	// perform first level of reduction,
	// reading from global memory, writing to shared memory
	unsigned int tid = get_local_id(0);
	unsigned int i = get_group_id(0)*(get_local_size(0) * 2) + get_local_id(0);
	unsigned int gridSize = blockSize * 2 * get_num_groups(0);
	sdata[tid] = INFINITY;

	// we reduce multiple elements per thread.  The number is determined by the 
	// number of active thread blocks. More blocks will result
	// in a larger gridSize and therefore fewer elements per thread
	while (i < ci_idsSize)
	{
		//this is optimized away for powerOf2 sized arrays
		if (g_idata[i] < sdata[tid]) {
			sdata[tid] = g_idata[i]; s_sfh[tid] = cl_sfh[i]; s_ir[tid] = cl_ir[i];
		}
		if (g_idata[i] == sdata[tid] && (cl_sfh[i] * NMOD) + cl_ir[i] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
			s_sfh[tid] = cl_sfh[i]; s_ir[tid] = cl_ir[i];
		}
		if (g_idata[i + blockSize] < sdata[tid]) {
			sdata[tid] = g_idata[i + blockSize]; s_sfh[tid] = cl_sfh[i + blockSize]; s_ir[tid] = cl_ir[i + blockSize];
		}
		if (g_idata[i + blockSize] == sdata[tid] && (cl_sfh[i + blockSize] * NMOD) + cl_ir[i + blockSize] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
			s_sfh[tid] = cl_sfh[i + blockSize]; s_ir[tid] = cl_ir[i + blockSize];
		}
		i += gridSize;
	}

	barrier(CLK_LOCAL_MEM_FENCE);

	//do reduction in shared mem
	if (blockSize >= 512) {
		if (tid < 256) {
			if (sdata[tid + 256] < sdata[tid]) {
				sdata[tid] = sdata[tid + 256]; s_sfh[tid] = s_sfh[tid + 256]; s_ir[tid] = s_ir[tid + 256];
			}
			if (sdata[tid + 256] == sdata[tid] && (s_sfh[tid + 256] * NMOD) + s_ir[tid + 256] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 256]; s_ir[tid] = s_ir[tid + 256];
			}
		}
		barrier(CLK_LOCAL_MEM_FENCE);
	}
	if (blockSize >= 256) {
		if (tid < 128) {
			if (sdata[tid + 128] < sdata[tid]) {
				sdata[tid] = sdata[tid + 128]; s_sfh[tid] = s_sfh[tid + 128]; s_ir[tid] = s_ir[tid + 128];
			}
			else if (sdata[tid + 128] == sdata[tid] && (s_sfh[tid + 128] * NMOD) + s_ir[tid + 128] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 128]; s_ir[tid] = s_ir[tid + 128];
			}
		}
		barrier(CLK_LOCAL_MEM_FENCE);
	}
	if (blockSize >= 128) {
		if (tid < 64) {
			if (sdata[tid + 64] < sdata[tid]) {
				sdata[tid] = sdata[tid + 64]; s_sfh[tid] = s_sfh[tid + 64]; s_ir[tid] = s_ir[tid + 64];
			}
			else if (sdata[tid + 64] == sdata[tid] && (s_sfh[tid + 64] * NMOD) + s_ir[tid + 64] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 64]; s_ir[tid] = s_ir[tid + 64];
			}
		}
		barrier(CLK_LOCAL_MEM_FENCE);
	}

	if (tid < 32)
	{
		if (blockSize >= 64) {
			if (sdata[tid + 32] < sdata[tid]) {
				sdata[tid] = sdata[tid + 32]; s_sfh[tid] = s_sfh[tid + 32]; s_ir[tid] = s_ir[tid + 32];
			}
			else if (sdata[tid + 32] == sdata[tid] && (s_sfh[tid + 32] * NMOD) + s_ir[tid + 32] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 32]; s_ir[tid] = s_ir[tid + 32];
			}
		}
		if (blockSize >= 32) {
			if (sdata[tid + 16] < sdata[tid]) {
				sdata[tid] = sdata[tid + 16]; s_sfh[tid] = s_sfh[tid + 16]; s_ir[tid] = s_ir[tid + 16];
			}
			else if (sdata[tid + 16] == sdata[tid] && (s_sfh[tid + 16] * NMOD) + s_ir[tid + 16] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 16]; s_ir[tid] = s_ir[tid + 16];
			}
		}
		if (blockSize >= 16) {
			if (sdata[tid + 8] < sdata[tid]) {
				sdata[tid] = sdata[tid + 8]; s_sfh[tid] = s_sfh[tid + 8]; s_ir[tid] = s_ir[tid + 8];
			}
			else if (sdata[tid + 8] == sdata[tid] && (s_sfh[tid + 8] * NMOD) + s_ir[tid + 8] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 8]; s_ir[tid] = s_ir[tid + 8];
			}
		}
		if (blockSize >= 8) {
			if (sdata[tid + 4] < sdata[tid]) {
				sdata[tid] = sdata[tid + 4]; s_sfh[tid] = s_sfh[tid + 4]; s_ir[tid] = s_ir[tid + 4];
			}
			else if (sdata[tid + 4] == sdata[tid] && (s_sfh[tid + 4] * NMOD) + s_ir[tid + 4] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 4]; s_ir[tid] = s_ir[tid + 4];
			}
		}
		if (blockSize >= 4) {
			if (sdata[tid + 2] < sdata[tid]) {
				sdata[tid] = sdata[tid + 2]; s_sfh[tid] = s_sfh[tid + 2]; s_ir[tid] = s_ir[tid + 2];
			}
			else if (sdata[tid + 2] == sdata[tid] && (s_sfh[tid + 2] * NMOD) + s_ir[tid + 2] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 2]; s_ir[tid] = s_ir[tid + 2];
			}
		}
		if (blockSize >= 2) {
			if (sdata[tid + 1] < sdata[tid]) {
				sdata[tid] = sdata[tid + 1]; s_sfh[tid] = s_sfh[tid + 1]; s_ir[tid] = s_ir[tid + 1];
			}
			else if (sdata[tid + 1] == sdata[tid] && (s_sfh[tid + 1] * NMOD) + s_ir[tid + 1] < (s_sfh[tid] * NMOD) + s_ir[tid]) {
				s_sfh[tid] = s_sfh[tid + 1]; s_ir[tid] = s_ir[tid + 1];
			}
		}
	}

	// write result for this block to global mem 
	if (tid == 0) {
		g_odata[get_group_id(0)] = sdata[0];
		g_o_sfh[get_group_id(0)] = s_sfh[0];
		g_o_ir[get_group_id(0)] = s_ir[0];
	}
}

__kernel void check_df(const int start_sfh,
	__constant clconstants_t* ct_clconstants,
	__global const double* fmu_sfh,
	__global const double* fmu_ir,
	__global unsigned int* withindf
	)
{
	// Get kernel thread id for matching with array indexes.
	int i_idx = get_global_id(0) * 32;
	int i_sfhdiff = i_idx / NMOD;
	int i_ir = i_idx - (i_sfhdiff * NMOD);
	int i_sfh = start_sfh + i_sfhdiff;
	int k;

	unsigned int ui_df = 0; //All False
	unsigned int ui_pow = 1;

	if (i_sfh < ct_clconstants->n_sfh && i_ir < ct_clconstants->n_ir){
		for (k = 0; k < 32 && i_ir < ct_clconstants->n_ir; k++) {
			if (fabs(fmu_sfh[i_sfh] - fmu_ir[i_ir]) <= ct_clconstants->df) {
				ui_df = ui_df | ui_pow;
			}
			i_ir++;
			ui_pow = ui_pow << 1;
		}
	}

	withindf[get_global_id(0)] = ui_df;

}

__kernel void sumidtorange(
	const int ci_idsSize,
	const int ci_groupSize,
	const int ci_theadSize,
	const int range_start,
	const int range_width,
	__global ushort* ibin_id,
	__global double* cl_prob,
	__global double *g_odata,
	__local ushort* sdataid,
	__local double* sdataprob)
{
	//scratch is (clmax/get_num_groups)*double  262144 *2b 524288/49152=11  /14 37450  multiple of gpu_compute<48K
	//g_odata is range*get_num_groups*double    3008*14 42K 200K total 50008*14 700K vs balanced square 14k+14k vs cpu reduce 262k f-op 1.4M f-op total
	// perform first level of reduction,        //cl_model 262144*24*8=6M //42k*4 + bal = 250K GPU/1024, vs 1.4M CPU/4  244 vs 393K *1611
	// reading from global memory, writing to shared memory //withindf 312M //42k*16 672K no sfh/ir

	//ci_groupSize ceil(256144 clmax/14 groups)=18296
	//ci_theadSize ceil(18296/256localthreads)=72
	unsigned int i_global_groupoffset = get_group_id(0)*ci_groupSize;
	unsigned int i_local_threadoffset = ci_theadSize*get_local_id(0);
	unsigned int i_global_threadoffset = i_global_groupoffset + i_local_threadoffset;

	//loop ci_groupSize of Id's with each thread handling ci_theadSize
	for (int iload = 0; iload < ci_theadSize; iload++)
	{
		int i_local_id = i_local_threadoffset + iload;
		int i_global_id = i_global_threadoffset + iload;

		if (i_local_id < ci_groupSize && i_global_id < ci_idsSize) {
			sdataid[i_local_id] = ibin_id[i_global_id];
			sdataprob[i_local_id] = cl_prob[i_global_id];
		} else {
			sdataid[i_local_id] = 65535;
			sdataprob[i_local_id] = 0;
		}
	}
	barrier(CLK_LOCAL_MEM_FENCE);

	//ii_findid. 2304/256=9 or 50008/256=195 (unbalanced block, balanced=4)
	double sum_search[9];
	for (int ii_findid = 0; ii_findid < 10; ii_findid++) {
		sum_search[ii_findid] = 0;
	}
	ushort i_local_searchoffset = 9 * get_local_id(0);
	ushort i_local_searchoffsetend = min(i_local_searchoffset + 9, range_width);
	//const ushort us_searchmax = 9;
	//const ushort us_searchmin = 0;
	//ushort i_local_searchoffsetminus1 = i_local_searchoffset - 1;

	//ii_chklocal = 4574/8=571
	//ushort8 chkid = vload8(0, sdataid);
	//double8 prob = vload8(0, sdataprob);
	//ushort8 chkidoffset = chkid - i_local_searchoffset;

	for (int ii_chklocal = 0; ii_chklocal < ci_groupSize / 8; ii_chklocal++) {
		ushort8 chkid = vload8(ii_chklocal, sdataid);
		double8 prob = vload8(ii_chklocal, sdataprob);
		//ushort8 chkidoffset = min(us_searchmin, max(chkid - i_local_searchoffsetminus1, us_searchmax)); //Zeroth and 10th item is summed but not saved to avoid if's
		//sum_search[chkidoffset.s0] += prob.s0;
		//sum_search[chkidoffset.s1] += prob.s1;

		ushort8 chkidoffset = chkid - i_local_searchoffset;
		if (chkidoffset.s0 >= 0 && chkidoffset.s0 < 9) sum_search[chkidoffset.s0] += prob.s0;
		if (chkidoffset.s1 >= 0 && chkidoffset.s1 < 9) sum_search[chkidoffset.s1] += prob.s1;
		if (chkidoffset.s2 >= 0 && chkidoffset.s2 < 9) sum_search[chkidoffset.s2] += prob.s2;
		if (chkidoffset.s3 >= 0 && chkidoffset.s3 < 9) sum_search[chkidoffset.s3] += prob.s3;
		if (chkidoffset.s4 >= 0 && chkidoffset.s4 < 9) sum_search[chkidoffset.s4] += prob.s4;
		if (chkidoffset.s5 >= 0 && chkidoffset.s5 < 9) sum_search[chkidoffset.s5] += prob.s5;
		if (chkidoffset.s6 >= 0 && chkidoffset.s6 < 9) sum_search[chkidoffset.s6] += prob.s6;
		if (chkidoffset.s7 >= 0 && chkidoffset.s7 < 9) sum_search[chkidoffset.s7] += prob.s7;
	} //ii_searchhistogram

	for (int ii_findid = 0; ii_findid < (i_local_searchoffsetend - i_local_searchoffset); ii_findid++) {
		g_odata[get_group_id(0)*range_width + i_local_searchoffset + ii_findid] = sum_search[ii_findid];
	}
}

__kernel void sumrangetoarray(
	const int range_start,
	const int range_width,
	const int num_groups,
	__global double *g_idata,
	__global double *g_odata)
{
	unsigned int tid = get_global_id(0); //example histo start 0, width 3008
										 //example sfh start 1024, width 1024  IR start 2048 width 1024
	if (tid < range_width) {			// if we can balance blocks otherwise sfh 19 w 21, IR 0 w 50008
		double sum_search = 0;
		for (int i = 0; i < num_groups; i++) {
			sum_search += g_idata[i*range_width + tid];
		}
		if (sum_search != 0) { //Save to Global Array
			g_odata[range_start+tid] += sum_search;
		}
		//tid += get_num_groups(0)*get_local_size(0);
	}
}