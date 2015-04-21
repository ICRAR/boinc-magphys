// ===========================================================================
// PROGRAM FIT_SED
// ---------------------------------------------------------------------------
// Authors :   E. da Cunha & S. Charlot
// Latest revision :   Sep. 16th, 2010
// ---------------------------------------------------------------------------
// Model & Method descibed in detail in:
// da Cunha, Charlot & Elbaz, 2008, MNRAS 388, 1595
// ---------------------------------------------------------------------------
// Compares model fluxes with observed fluxes from the ultraviolet to the
// far-infrared by computing the chi^2 goodness-of-fit of each model.
// The probability of each model is exp(-1/2 chi^2)
// The code also builds the likelihood distribution of each parameter
// 
// INPUTS:
// - filter file - define USER_FILTERS in .galsbit_tcshrc
// - file with redshifts & observed fluxes of the
// galaxies - define USER_OBS in .magphys_tcshrc
// - file with redshifts at which libraries
// were computed "zlibs.dat"
// - .lbr files generated with get_optic_colors.f
// & get_infrared_colors.f
// - number of the galaxy to fit: i_gal
//
// OUTPUTS: - "name".fit file containing:
// -- observed fluxes
// -- mininum chi2
// -- best-fit model parameters & fluxes
// -- likelihood distribution of each parameter
// -- 2.5th, 16th, 50th, 84th, 97.5th percentile
// of each parameter
// - "name".sed file containing the best-fit SED
// ===========================================================================
//
//
// ===========================================================================
// Author : Kevin Vinsen
//Date : 29th May 2012
// ---------------------------------------------------------------------------
// Added minor changes to allow the code to run from the command line and not
// to perform the normalisation against the models. Instead it writes the
// parameters required to normalise it later.
// The skyNet project is a citizen science project and we cannot expect the
// general public to download the 3 large .bin files
// ===========================================================================

// C++ binding header.
#include "stdafx.h";
#include <algorithm>
#include <ctime>
#include <chrono>
#include <CL/cl.hpp>
// We only use the vector class for OpenCL implementation
// at present.
#include <vector>
#include <sstream>
#include <fstream>
#include <iostream>
#include <sstream>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cstring>
#include <cfenv>
//#pragma fenv_access (on)

#if defined(_WIN32)
class Parser
{
public:
	Parser();
	Parser(std::string file);

	virtual void Ignore(const std::string& start, const std::string& end);
	virtual void Rewind(void);
	virtual void Next(void);
	virtual void GetLine(std::string& line);
	virtual void GetTokens(std::vector<std::string>& tokens);
	virtual bool Good(void);
	virtual void GetNextToken(std::string& container, size_t& from);

	std::stringstream		 stream;

protected:
	void                     TrimLine(std::string& line);

	int                      ignoring;
	std::vector<std::string> excludeDelims;
	std::vector<std::string> includeDelims;
	std::ifstream            input;
	std::string				 line;
};
#endif

//#define READCL //Read CL From File Or Constant *KernelSource

// OpenCL kernel.
#ifndef READCL
const char *kernelSource = "\n" \
"// Enable double precision.																															\n" \
"#pragma OPENCL EXTENSION cl_khr_fp64 : enable																											\n" \
"																																						\n" \
"// Some constants copied from main host program.																										\n" \
"#define NMAX 56																																		\n" \
"#define NMOD 50016																																		\n" \
"#define blockSize 256	//BlockSize for sumprob																											\n" \
"																																						\n" \
"// Struct containing var constants read by kernel																										\n" \
"// threads.										 	 																								\n" \
"typedef struct clconstants {																															\n" \
"	int nbin_sfr;																																		\n" \
"	int nbin_a;																																			\n" \
"	int nbin_ld;																																		\n" \
"	int nbin_md;																																		\n" \
"	double a_max;																																		\n" \
"	double a_min;																																		\n" \
"	double sfr_max;																																		\n" \
"	double sfr_min;																																		\n" \
"	double ld_max;																																		\n" \
"	double ld_min;																																		\n" \
"	double md_max;																																		\n" \
"	double md_min;																																		\n" \
"	int nfilt;																																			\n" \
"	int nfilt_sfh;																																		\n" \
"	int nfilt_mix;																																		\n" \
"	int i_gal;																																			\n" \
"	double df;																																			\n" \
"	int n_sfh;																																			\n" \
"	int n_ir;																																			\n" \
"} clconstants_t;																																		\n" \
"																																						\n" \
"// Struct to define arrays of indexes and models																										\n" \
"// used by kernel threads.								 																								\n" \
"typedef struct clmod_sfh {																																\n" \
"	double lssfr;																																		\n" \
"	double logldust;																																	\n" \
"	double ldust;																																		\n" \
"	double flux_sfh[NMAX];																																\n" \
"} clmod_sfh_t;																																			\n" \
"																																						\n" \
"typedef struct clmod_ir {																																\n" \
"	double mdust;																																		\n" \
"	double flux_ir[NMAX];																																\n" \
"} clmod_ir_t;																																			\n" \
"																																						\n" \
"__kernel void fit(const int ci_idsSize,																												\n" \
"	__constant clconstants_t* ct_clconstants,																											\n" \
"	__global const clmod_sfh_t* mods_sfh,																												\n" \
"	__global const clmod_ir_t* mods_ir,																													\n" \
"	__global const double* flux_obs,																													\n" \
"	__global const double* w,																															\n" \
"	__global const double* flux_obs_mask,																												\n" \
"	__global const double* filt_sfh_mask,																												\n" \
"	__global const double* filt_ir_mask,																												\n" \
"	__global const ushort* cl_sfh,																														\n" \
"	__global const ushort* cl_ir,																														\n" \
"	__global double* cl_chi2,																															\n" \
"	__global double* cl_prob,																															\n" \
"	__global ushort* ibin_pa,																															\n" \
"	__global ushort* ibin_psfr,																															\n" \
"	__global ushort* ibin_pldust,																														\n" \
"	__global ushort* ibin_pmdust																														\n" \
"	)																																					\n" \
"{																																						\n" \
"	// Get kernel thread id for matching with array indexes.																							\n" \
"	int global_index = get_global_id(0);																												\n" \
"	int local_index = get_local_id(0);																													\n" \
"																																						\n" \
"	// Only continue if our id is less than batch max. The id can sometimes		 																		\n" \
"	// be greater if the global work size is greater than values we're working with. 																	\n" \
"	if (global_index < ci_idsSize){																														\n" \
"																																						\n" \
"		// Set some variables in private memory space.																									\n" \
"		ushort k = 0;																																	\n" \
"		double num = 0;																																	\n" \
"		double den = 0;																																	\n" \
"		ushort i_sfh = cl_sfh[global_index];																											\n" \
"		ushort i_ir = cl_ir[global_index];																												\n" \
"		ushort nfilt = ct_clconstants->nfilt;																											\n" \
"		ushort nfilt_sfh = ct_clconstants->nfilt_sfh;																									\n" \
"		ushort nfilt_mix = ct_clconstants->nfilt_mix;																									\n" \
"		__global clmod_sfh_t *msfh = &mods_sfh[i_sfh];																									\n" \
"		__global clmod_ir_t *mir = &mods_ir[i_ir];																										\n" \
"																																						\n" \
"		double flux_mod[NMAX];																															\n" \
"		for (k = 0; k < nfilt_sfh - nfilt_mix; k++){																									\n" \
"			flux_mod[k] = msfh->flux_sfh[k];																											\n" \
"		}																																				\n" \
"		for (k = nfilt_sfh - nfilt_mix; k < nfilt_sfh; k++){																							\n" \
"			flux_mod[k] = msfh->flux_sfh[k] + mir->flux_ir[k];																							\n" \
"		}																																				\n" \
"		for (k = nfilt_sfh; k < nfilt; k++){																											\n" \
"			flux_mod[k] = mir->flux_ir[k];																												\n" \
"		}																																				\n" \
"																																						\n" \
"		// Compute the scaling factor a.						 																						\n" \
"		for (k = 0; k<nfilt; k++){																														\n" \
"			if (flux_obs[k]>0) {																														\n" \
"				num = num + (flux_mod[k] * flux_obs[k] * w[k]);																							\n" \
"				den = den + ((flux_mod[k] * flux_mod[k]) * w[k]);																						\n" \
"			}																																			\n" \
"		}																																				\n" \
"																																						\n" \
"		double a = num / den;																															\n" \
"																																						\n" \
"		// Compute chi^2 goodness of fit.						 																						\n" \
"		double chi2 = 0;																																\n" \
"		for (k = 0; k < nfilt_sfh; k++){																												\n" \
"			if (flux_obs[k]>0) {																														\n" \
"				chi2 = chi2 + ( (  (flux_obs[k] - (a * flux_mod[k]))*(flux_obs[k] - (a * flux_mod[k])) ) * w[k]);										\n" \
"			}																																			\n" \
"		}																																				\n" \
"		if (chi2 < 600){																																\n" \
"			for (k = nfilt_sfh; k < nfilt; k++){																										\n" \
"				if (flux_obs[k]>0) {																													\n" \
"					chi2 = chi2 + ((pow(flux_obs[k] - (a * flux_mod[k]), 2)) * w[k]);																	\n" \
"				}																																		\n" \
"			}																																			\n" \
"		}																																				\n" \
"																																						\n" \
"		// Calculate probability.							 																							\n" \
"		double prob = exp(-0.5 * chi2);																													\n" \
"																																						\n" \
"		cl_chi2[global_index] = chi2;																													\n" \
"		cl_prob[global_index] = prob;																													\n" \
"																																						\n" \
"		// Calculate marginal probability density functions. Instead			 																		\n" \
"		// of writing prob values, we instead write the index of bin			 																		\n" \
"		// for non-parallelized processing.						 																						\n" \
"		int ibin;																																		\n" \
"		ushort usbin;																																	\n" \
"		double aux;																																		\n" \
"																																						\n" \
"		a = log10(a);																																	\n" \
"																																						\n" \
"		// Mstar									 																									\n" \
"		aux = ((a - ct_clconstants->a_min) / (ct_clconstants->a_max - ct_clconstants->a_min)) * ct_clconstants->nbin_a;									\n" \
"		ibin = (int)(aux);																																\n" \
"		usbin = max(0, min(ibin, ct_clconstants->nbin_a - 1));																							\n" \
"		ibin_pa[global_index] = usbin;																													\n" \
"																																						\n" \
"		// SFR_0.1Gyr									 																								\n" \
"		aux = ((msfh->lssfr + a - ct_clconstants->sfr_min) / (ct_clconstants->sfr_max - ct_clconstants->sfr_min))* ct_clconstants->nbin_sfr;			\n" \
"		ibin = (int)(aux);																																\n" \
"		usbin = max(0, min(ibin, ct_clconstants->nbin_sfr - 1));																						\n" \
"		ibin_psfr[global_index] = usbin;																												\n" \
"																																						\n" \
"		// Ldust									 																									\n" \
"		aux = ((msfh->logldust + a - ct_clconstants->ld_min) / (ct_clconstants->ld_max - ct_clconstants->ld_min))* ct_clconstants->nbin_ld;				\n" \
"		ibin = (int)(aux);																																\n" \
"		usbin = max(0, min(ibin, ct_clconstants->nbin_ld - 1));																							\n" \
"		ibin_pldust[global_index] = usbin;																												\n" \
"																																						\n" \
"		// Mdust									 																									\n" \
"		aux = log10(mir->mdust * msfh->ldust * exp10(a));																								\n" \
"		aux = ((aux - ct_clconstants->md_min) / (ct_clconstants->md_max - ct_clconstants->md_min)) * ct_clconstants->nbin_md;							\n" \
"		ibin = (int)(aux);																																\n" \
"		usbin = max(0, min(ibin, ct_clconstants->nbin_md - 1));																							\n" \
"		ibin_pmdust[global_index] = usbin;																												\n" \
"																																						\n" \
"	} //if global_index < ci_idsSize											 																		\n" \
"}																																						\n" \
"																																						\n" \
"__kernel void sumprob(int ci_idsSize, __global double *g_idata, __global double *g_odata, __local volatile double* sdata)								\n" \
"{																																						\n" \
"	// perform first level of reduction,																												\n" \
"	// reading from global memory, writing to shared memory																								\n" \
"	unsigned int tid = get_local_id(0);																													\n" \
"	unsigned int i = get_group_id(0)*(get_local_size(0) * 2) + get_local_id(0);																			\n" \
"	unsigned int gridSize = blockSize * 2 * get_num_groups(0);																							\n" \
"	sdata[tid] = 0;																																		\n" \
"																																						\n" \
"	// we reduce multiple elements per thread.  The number is determined by the 																		\n" \
"	// number of active thread blocks. More blocks will result																							\n" \
"	// in a larger gridSize and therefore fewer elements per thread																						\n" \
"	while (i < ci_idsSize)																																\n" \
"	{																																					\n" \
"		sdata[tid] += g_idata[i];																														\n" \
"		// this is optimized away for powerOf2 sized arrays																								\n" \
"		sdata[tid] += g_idata[i + blockSize];																											\n" \
"		i += gridSize;																																	\n" \
"	}																																					\n" \
"																																						\n" \
"	barrier(CLK_LOCAL_MEM_FENCE);																														\n" \
"																																						\n" \
"	// do reduction in shared mem																														\n" \
"	if (blockSize >= 512) { if (tid < 256) { sdata[tid] += sdata[tid + 256]; } barrier(CLK_LOCAL_MEM_FENCE); }											\n" \
"	if (blockSize >= 256) { if (tid < 128) { sdata[tid] += sdata[tid + 128]; } barrier(CLK_LOCAL_MEM_FENCE); }											\n" \
"	if (blockSize >= 128) { if (tid <  64) { sdata[tid] += sdata[tid + 64]; } barrier(CLK_LOCAL_MEM_FENCE); }											\n" \
"																																						\n" \
"	if (tid < 32)																																		\n" \
"	{																																					\n" \
"		if (blockSize >= 64) { sdata[tid] += sdata[tid + 32]; }																							\n" \
"		if (blockSize >= 32) { sdata[tid] += sdata[tid + 16]; }																							\n" \
"		if (blockSize >= 16) { sdata[tid] += sdata[tid + 8]; }																							\n" \
"		if (blockSize >= 8) { sdata[tid] += sdata[tid + 4]; }																							\n" \
"		if (blockSize >= 4) { sdata[tid] += sdata[tid + 2]; }																							\n" \
"		if (blockSize >= 2) { sdata[tid] += sdata[tid + 1]; }																							\n" \
"	}																																					\n" \
"																																						\n" \
"	// write result for this block to global mem 																										\n" \
"	if (tid == 0) g_odata[get_group_id(0)] = sdata[0];																									\n" \
"}																																						\n" \
"																																						\n" \
"__kernel void minchi(int ci_idsSize, __global const ushort* cl_sfh,																					\n" \
"	__global const ushort* cl_ir, __global double *g_idata,																								\n" \
"	__global double *g_odata, __global ushort *g_o_sfh, __global ushort *g_o_ir,																		\n" \
"	__local volatile double* sdata, __local volatile ushort* s_sfh, __local volatile ushort* s_ir)														\n" \
"{																																						\n" \
"	//Need to added checks if chi2 is equal then use lowest sfh and ir																					\n" \
"																																						\n" \
"	// perform first level of reduction,																												\n" \
"	// reading from global memory, writing to shared memory																								\n" \
"	unsigned int tid = get_local_id(0);																													\n" \
"	unsigned int i = get_group_id(0)*(get_local_size(0) * 2) + get_local_id(0);																			\n" \
"	unsigned int gridSize = blockSize * 2 * get_num_groups(0);																							\n" \
"	sdata[tid] = INFINITY;																																\n" \
"																																						\n" \
"	// we reduce multiple elements per thread.  The number is determined by the 																		\n" \
"	// number of active thread blocks. More blocks will result																							\n" \
"	// in a larger gridSize and therefore fewer elements per thread																						\n" \
"	while (i < ci_idsSize)																																\n" \
"	{																																					\n" \
"		//this is optimized away for powerOf2 sized arrays																								\n" \
"		if (g_idata[i] < sdata[tid]) {																													\n" \
"			sdata[tid] = g_idata[i]; s_sfh[tid] = cl_sfh[i]; s_ir[tid] = cl_ir[i];																		\n" \
"		}																																				\n" \
"		if (g_idata[i] == sdata[tid] && (cl_sfh[i] * NMOD) + cl_ir[i] < (s_sfh[tid] * NMOD) + s_ir[tid]) {												\n" \
"			s_sfh[tid] = cl_sfh[i]; s_ir[tid] = cl_ir[i];																								\n" \
"		}																																				\n" \
"		if (g_idata[i + blockSize] < sdata[tid]) {																										\n" \
"			sdata[tid] = g_idata[i + blockSize]; s_sfh[tid] = cl_sfh[i + blockSize]; s_ir[tid] = cl_ir[i + blockSize];									\n" \
"		}																																				\n" \
"		if (g_idata[i + blockSize] == sdata[tid] && (cl_sfh[i + blockSize] * NMOD) + cl_ir[i + blockSize] < (s_sfh[tid] * NMOD) + s_ir[tid]) {			\n" \
"			s_sfh[tid] = cl_sfh[i + blockSize]; s_ir[tid] = cl_ir[i + blockSize];																		\n" \
"		}																																				\n" \
"		i += gridSize;																																	\n" \
"	}																																					\n" \
"																																						\n" \
"	barrier(CLK_LOCAL_MEM_FENCE);																														\n" \
"																																						\n" \
"	//do reduction in shared mem																														\n" \
"	if (blockSize >= 512) {																																\n" \
"		if (tid < 256) {																																\n" \
"			if (sdata[tid + 256] < sdata[tid]) {																										\n" \
"				sdata[tid] = sdata[tid + 256]; s_sfh[tid] = s_sfh[tid + 256]; s_ir[tid] = s_ir[tid + 256];												\n" \
"			}																																			\n" \
"			if (sdata[tid + 256] == sdata[tid] && (s_sfh[tid + 256] * NMOD) + s_ir[tid + 256] < (s_sfh[tid] * NMOD) + s_ir[tid]) {						\n" \
"				s_sfh[tid] = s_sfh[tid + 256]; s_ir[tid] = s_ir[tid + 256];																				\n" \
"			}																																			\n" \
"		}																																				\n" \
"		barrier(CLK_LOCAL_MEM_FENCE);																													\n" \
"	}																																					\n" \
"	if (blockSize >= 256) {																																\n" \
"		if (tid < 128) {																																\n" \
"			if (sdata[tid + 128] < sdata[tid]) {																										\n" \
"				sdata[tid] = sdata[tid + 128]; s_sfh[tid] = s_sfh[tid + 128]; s_ir[tid] = s_ir[tid + 128];												\n" \
"			}																																			\n" \
"			else if (sdata[tid + 128] == sdata[tid] && (s_sfh[tid + 128] * NMOD) + s_ir[tid + 128] < (s_sfh[tid] * NMOD) + s_ir[tid]) {					\n" \
"				s_sfh[tid] = s_sfh[tid + 128]; s_ir[tid] = s_ir[tid + 128];																				\n" \
"			}																																			\n" \
"		}																																				\n" \
"		barrier(CLK_LOCAL_MEM_FENCE);																													\n" \
"	}																																					\n" \
"	if (blockSize >= 128) {																																\n" \
"		if (tid < 64) {																																	\n" \
"			if (sdata[tid + 64] < sdata[tid]) {																											\n" \
"				sdata[tid] = sdata[tid + 64]; s_sfh[tid] = s_sfh[tid + 64]; s_ir[tid] = s_ir[tid + 64];													\n" \
"			}																																			\n" \
"			else if (sdata[tid + 64] == sdata[tid] && (s_sfh[tid + 64] * NMOD) + s_ir[tid + 64] < (s_sfh[tid] * NMOD) + s_ir[tid]) {					\n" \
"				s_sfh[tid] = s_sfh[tid + 64]; s_ir[tid] = s_ir[tid + 64];																				\n" \
"			}																																			\n" \
"		}																																				\n" \
"		barrier(CLK_LOCAL_MEM_FENCE);																													\n" \
"	}																																					\n" \
"																																						\n" \
"	if (tid < 32)																																		\n" \
"	{																																					\n" \
"		if (blockSize >= 64) {																															\n" \
"			if (sdata[tid + 32] < sdata[tid]) {																											\n" \
"				sdata[tid] = sdata[tid + 32]; s_sfh[tid] = s_sfh[tid + 32]; s_ir[tid] = s_ir[tid + 32];													\n" \
"			}																																			\n" \
"			else if (sdata[tid + 32] == sdata[tid] && (s_sfh[tid + 32] * NMOD) + s_ir[tid + 32] < (s_sfh[tid] * NMOD) + s_ir[tid]) {					\n" \
"				s_sfh[tid] = s_sfh[tid + 32]; s_ir[tid] = s_ir[tid + 32];																				\n" \
"			}																																			\n" \
"		}																																				\n" \
"		if (blockSize >= 32) {																															\n" \
"			if (sdata[tid + 16] < sdata[tid]) {																											\n" \
"				sdata[tid] = sdata[tid + 16]; s_sfh[tid] = s_sfh[tid + 16]; s_ir[tid] = s_ir[tid + 16];													\n" \
"			}																																			\n" \
"			else if (sdata[tid + 16] == sdata[tid] && (s_sfh[tid + 16] * NMOD) + s_ir[tid + 16] < (s_sfh[tid] * NMOD) + s_ir[tid]) {					\n" \
"				s_sfh[tid] = s_sfh[tid + 16]; s_ir[tid] = s_ir[tid + 16];																				\n" \
"			}																																			\n" \
"		}																																				\n" \
"		if (blockSize >= 16) {																															\n" \
"			if (sdata[tid + 8] < sdata[tid]) {																											\n" \
"				sdata[tid] = sdata[tid + 8]; s_sfh[tid] = s_sfh[tid + 8]; s_ir[tid] = s_ir[tid + 8];													\n" \
"			}																																			\n" \
"			else if (sdata[tid + 8] == sdata[tid] && (s_sfh[tid + 8] * NMOD) + s_ir[tid + 8] < (s_sfh[tid] * NMOD) + s_ir[tid]) {						\n" \
"				s_sfh[tid] = s_sfh[tid + 8]; s_ir[tid] = s_ir[tid + 8];																					\n" \
"			}																																			\n" \
"		}																																				\n" \
"		if (blockSize >= 8) {																															\n" \
"			if (sdata[tid + 4] < sdata[tid]) {																											\n" \
"				sdata[tid] = sdata[tid + 4]; s_sfh[tid] = s_sfh[tid + 4]; s_ir[tid] = s_ir[tid + 4];													\n" \
"			}																																			\n" \
"			else if (sdata[tid + 4] == sdata[tid] && (s_sfh[tid + 4] * NMOD) + s_ir[tid + 4] < (s_sfh[tid] * NMOD) + s_ir[tid]) {						\n" \
"				s_sfh[tid] = s_sfh[tid + 4]; s_ir[tid] = s_ir[tid + 4];																					\n" \
"			}																																			\n" \
"		}																																				\n" \
"		if (blockSize >= 4) {																															\n" \
"			if (sdata[tid + 2] < sdata[tid]) {																											\n" \
"				sdata[tid] = sdata[tid + 2]; s_sfh[tid] = s_sfh[tid + 2]; s_ir[tid] = s_ir[tid + 2];													\n" \
"			}																																			\n" \
"			else if (sdata[tid + 2] == sdata[tid] && (s_sfh[tid + 2] * NMOD) + s_ir[tid + 2] < (s_sfh[tid] * NMOD) + s_ir[tid]) {						\n" \
"				s_sfh[tid] = s_sfh[tid + 2]; s_ir[tid] = s_ir[tid + 2];																					\n" \
"			}																																			\n" \
"		}																																				\n" \
"		if (blockSize >= 2) {																															\n" \
"			if (sdata[tid + 1] < sdata[tid]) {																											\n" \
"				sdata[tid] = sdata[tid + 1]; s_sfh[tid] = s_sfh[tid + 1]; s_ir[tid] = s_ir[tid + 1];													\n" \
"			}																																			\n" \
"			else if (sdata[tid + 1] == sdata[tid] && (s_sfh[tid + 1] * NMOD) + s_ir[tid + 1] < (s_sfh[tid] * NMOD) + s_ir[tid]) {						\n" \
"				s_sfh[tid] = s_sfh[tid + 1]; s_ir[tid] = s_ir[tid + 1];																					\n" \
"			}																																			\n" \
"		}																																				\n" \
"	}																																					\n" \
"																																						\n" \
"	// write result for this block to global mem 																										\n" \
"	if (tid == 0) {																																		\n" \
"		g_odata[get_group_id(0)] = sdata[0];																											\n" \
"		g_o_sfh[get_group_id(0)] = s_sfh[0];																											\n" \
"		g_o_ir[get_group_id(0)] = s_ir[0];																												\n" \
"	}																																					\n" \
"}																																						\n" \
"																																						\n" \
"__kernel void check_df(const int start_sfh,																											\n" \
"	__constant clconstants_t* ct_clconstants,																											\n" \
"	__global const double* fmu_sfh,																														\n" \
"	__global const double* fmu_ir,																														\n" \
"	__global unsigned int* withindf																														\n" \
"	)																																					\n" \
"{																																						\n" \
"	// Get kernel thread id for matching with array indexes.																							\n" \
"	int i_idx = get_global_id(0) * 32;																													\n" \
"	int i_sfhdiff = i_idx / NMOD;																														\n" \
"	int i_ir = i_idx - (i_sfhdiff * NMOD);																												\n" \
"	int i_sfh = start_sfh + i_sfhdiff;																													\n" \
"	int k;																																				\n" \
"																																						\n" \
"	unsigned int ui_df = 0; //All False																													\n" \
"	unsigned int ui_pow = 1;																															\n" \
"																																						\n" \
"	if (i_sfh < ct_clconstants->n_sfh && i_ir < ct_clconstants->n_ir){																					\n" \
"		for (k = 0; k < 32 && i_ir < ct_clconstants->n_ir; k++) {																						\n" \
"			if (fabs(fmu_sfh[i_sfh] - fmu_ir[i_ir]) <= ct_clconstants->df) {																			\n" \
"				ui_df = ui_df | ui_pow;																													\n" \
"			}																																			\n" \
"			i_ir++;																																		\n" \
"			ui_pow = ui_pow << 1;																														\n" \
"		}																																				\n" \
"	}																																					\n" \
"																																						\n" \
"	withindf[get_global_id(0)] = ui_df;																													\n" \
"																																						\n" \
"}																																						\n" \
"																																						\n" \
"__kernel void sumidtorange(																															\n" \
"	const int ci_idsSize,																																\n" \
"	const int ci_groupSize,																																\n" \
"	const int ci_theadSize,																																\n" \
"	const int range_start,																																\n" \
"	const int range_width,																																\n" \
"	__global ushort* ibin_id,																															\n" \
"	__global double* cl_prob,																															\n" \
"	__global double *g_odata,																															\n" \
"	__local ushort* sdataid,																															\n" \
"	__local double* sdataprob)																															\n" \
"{																																						\n" \
"	//scratch is (clmax/get_num_groups)*double  262144 *2b 524288/49152=11  /14 37450  multiple of gpu_compute<48K										\n" \
"	//g_odata is range*get_num_groups*double    3008*14 42K 200K total 50008*14 700K vs balanced square 14k+14k vs cpu reduce 262k f-op 1.4M f-op total	\n" \
"	// perform first level of reduction,        //cl_model 262144*24*8=6M //42k*4 + bal = 250K GPU/1024, vs 1.4M CPU/4  244 vs 393K *1611				\n" \
"	// reading from global memory, writing to shared memory //withindf 312M //42k*16 672K no sfh/ir														\n" \
"																																						\n" \
"	//ci_groupSize ceil(256144 clmax/14 groups)=18296																									\n" \
"	//ci_theadSize ceil(18296/256localthreads)=72																										\n" \
"	unsigned int i_global_groupoffset = get_group_id(0)*ci_groupSize;																					\n" \
"	unsigned int i_local_threadoffset = ci_theadSize*get_local_id(0);																					\n" \
"	unsigned int i_global_threadoffset = i_global_groupoffset + i_local_threadoffset;																	\n" \
"																																						\n" \
"	//loop ci_groupSize of Id's with each thread handling ci_theadSize																					\n" \
"	for (int iload = 0; iload < ci_theadSize; iload++)																									\n" \
"	{																																					\n" \
"		int i_local_id = i_local_threadoffset + iload;																									\n" \
"		int i_global_id = i_global_threadoffset + iload;																								\n" \
"																																						\n" \
"		if (i_local_id < ci_groupSize && i_global_id < ci_idsSize) {																					\n" \
"			sdataid[i_local_id] = ibin_id[i_global_id];																									\n" \
"			sdataprob[i_local_id] = cl_prob[i_global_id];																								\n" \
"		} else {																																		\n" \
"			sdataid[i_local_id] = 65535;																												\n" \
"			sdataprob[i_local_id] = 0;																													\n" \
"		}																																				\n" \
"	}																																					\n" \
"	barrier(CLK_LOCAL_MEM_FENCE);																														\n" \
"																																						\n" \
"	//ii_findid. 2304/256=9 or 50008/256=195 (unbalanced block, balanced=4)																				\n" \
"	double sum_search[9];																																\n" \
"	for (int ii_findid = 0; ii_findid < 10; ii_findid++) {																								\n" \
"		sum_search[ii_findid] = 0;																														\n" \
"	}																																					\n" \
"	ushort i_local_searchoffset = 9 * get_local_id(0);																									\n" \
"	ushort i_local_searchoffsetend = min(i_local_searchoffset + 9, range_width);																		\n" \
"	//const ushort us_searchmax = 9;																													\n" \
"	//const ushort us_searchmin = 0;																													\n" \
"	//ushort i_local_searchoffsetminus1 = i_local_searchoffset - 1;																						\n" \
"																																						\n" \
"	//ii_chklocal = 4574/8=571																															\n" \
"	//ushort8 chkid = vload8(0, sdataid);																												\n" \
"	//double8 prob = vload8(0, sdataprob);																												\n" \
"	//ushort8 chkidoffset = chkid - i_local_searchoffset;																								\n" \
"																																						\n" \
"	for (int ii_chklocal = 0; ii_chklocal < ci_groupSize / 8; ii_chklocal++) {																			\n" \
"		ushort8 chkid = vload8(ii_chklocal, sdataid);																									\n" \
"		double8 prob = vload8(ii_chklocal, sdataprob);																									\n" \
"		//ushort8 chkidoffset = min(us_searchmin, max(chkid - i_local_searchoffsetminus1, us_searchmax)); 												\n" \
"		//sum_search[chkidoffset.s0] += prob.s0;																										\n" \
"		//sum_search[chkidoffset.s1] += prob.s1;																										\n" \
"																																						\n" \
"		ushort8 chkidoffset = chkid - i_local_searchoffset;																								\n" \
"		if (chkidoffset.s0 >= 0 && chkidoffset.s0 < 9) sum_search[chkidoffset.s0] += prob.s0;															\n" \
"		if (chkidoffset.s1 >= 0 && chkidoffset.s1 < 9) sum_search[chkidoffset.s1] += prob.s1;															\n" \
"		if (chkidoffset.s2 >= 0 && chkidoffset.s2 < 9) sum_search[chkidoffset.s2] += prob.s2;															\n" \
"		if (chkidoffset.s3 >= 0 && chkidoffset.s3 < 9) sum_search[chkidoffset.s3] += prob.s3;															\n" \
"		if (chkidoffset.s4 >= 0 && chkidoffset.s4 < 9) sum_search[chkidoffset.s4] += prob.s4;															\n" \
"		if (chkidoffset.s5 >= 0 && chkidoffset.s5 < 9) sum_search[chkidoffset.s5] += prob.s5;															\n" \
"		if (chkidoffset.s6 >= 0 && chkidoffset.s6 < 9) sum_search[chkidoffset.s6] += prob.s6;															\n" \
"		if (chkidoffset.s7 >= 0 && chkidoffset.s7 < 9) sum_search[chkidoffset.s7] += prob.s7;															\n" \
"	} //ii_searchhistogram																																\n" \
"																																						\n" \
"	for (int ii_findid = 0; ii_findid < (i_local_searchoffsetend - i_local_searchoffset); ii_findid++) {												\n" \
"		g_odata[get_group_id(0)*range_width + i_local_searchoffset + ii_findid] = sum_search[ii_findid];												\n" \
"	}																																					\n" \
"}																																						\n" \
"																																						\n" \
"__kernel void sumrangetoarray(																															\n" \
"	const int range_start,																																\n" \
"	const int range_width,																																\n" \
"	const int num_groups,																																\n" \
"	__global double *g_idata,																															\n" \
"	__global double *g_odata)																															\n" \
"{																																						\n" \
"	unsigned int tid = get_global_id(0); //example histo start 0, width 3008																			\n" \
"										 //example sfh start 1024, width 1024  IR start 2048 width 1024													\n" \
"	if (tid < range_width) {			// if we can balance blocks otherwise sfh 19 w 21, IR 0 w 50008													\n" \
"		double sum_search = 0;																															\n" \
"		for (int i = 0; i < num_groups; i++) {																											\n" \
"			sum_search += g_idata[i*range_width + tid];																									\n" \
"		}																																				\n" \
"		if (sum_search != 0) { //Save to Global Array																									\n" \
"			g_odata[range_start+tid] += sum_search;																										\n" \
"		}																																				\n" \
"		//tid += get_num_groups(0)*get_local_size(0);																									\n" \
"	}																																					\n" \
"}																																						\n" \
"\n";
#endif
// OpenCL implementation specific.
//#define __CL_ENABLE_EXCEPTIONS
// Number of models to batch for kernel thread work.
#define CLMAX 262144   //262144=512*512=2^18 (Best if Power of 2)
#define CLLOCAL_FIT 64
#define CLLOCAL_RED 256
#define CLLOCAL_RANGE 256
#define CLBLOCKSIZE_RED 256

#define NMAX 56
//#define GALMAX 5008//5000	//galmax: maximum number of galaxies in one input file
#define NMOD 50016 //50001
#define NZMAX 5008 //5000	//nmax: maxium number of photometric points/filters
#define NBINMAX1 2304 //3000 //144*16doubles(128bytes) 18K
#define NBINMAX2 128 //300   //8SIMD 1K

#define CLDF_SFH 320
#define CLDFCHECK NMOD*CLDF_SFH
#define CLDFSIZE NMOD*CLDF_SFH/32 // 50008 / 320 / bits in int

#define NPROP_SFH 24
#define NPROP_IR 8
#define MIN_HPBV 0.00001f

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

//Function prototypes for old FORTRAN functions.
double get_cosmol_c(double h, double omega, double omega_lambda, double* q);
double get_funl(double x);
void get_midpnt(double(*func)(double), double a, double b, double* s, double n);
double get_dl(double h, double q, double z);
void sort2(double arr1[], double arr2[], int left, int right);
void get_histgrid(double dv, double vmin, double vmax, int* nbin, double vout[]);
void get_percentiles(int n, double par[], double probability[], double percentile[]);
void degrade_hist(double delta, double min, double max, int nbin1, int * nbin2, double hist1[], double hist2[], double prob1[], double prob2[]);

void get_percentilesp(int n, double par[], double probability[], double percentile[]);
void degrade_histp(double delta, double min, double max, int nbin1, int * nbin2, double hist1[], double hist2[], double prob1[], double prob2[]);

double get_hpbv(double hist1[], double hist2[], int nbin);

void get_fexp3(char dstr[]);
void print_fexp3(FILE * fitfp, double histvalue);
void get_fsci(char dstr[]);

double round_nup(double n, int p);

// TODO : Bad! Get rid of this eventually.
static double omega0;

using namespace std;


int main(int argc, char *argv[]){
	// Windows specific instruction
#if defined(_WIN32)
	//Required as windows default is 3 digit exponent.
	_set_output_format(_TWO_DIGIT_EXPONENT);
#endif
	//fesetround(FE_TONEAREST);
	static unsigned int withindf[CLDFSIZE];

	static unsigned short cl_sfh[CLMAX];
	static unsigned short cl_ir[CLMAX];

	static double cl_chi2[CLMAX];
	static double cl_prob[CLMAX];
	static unsigned short ibin_pa[CLMAX];
	static unsigned short ibin_psfr[CLMAX];
	static unsigned short ibin_pldust[CLMAX];
	static unsigned short ibin_pmdust[CLMAX];

	static double cl_sum[CLBLOCKSIZE_RED];
	static double cl_minchi[CLBLOCKSIZE_RED];
	static unsigned short cl_minsfh[CLBLOCKSIZE_RED];
	static unsigned short cl_minir[CLBLOCKSIZE_RED];

	int i, j, k, i_gal;
	static int n_obs, n_models, ibin;
	static int nfilt_sfh, nfilt_ir, nfilt_mix;
	static int n_sfh, n_ir, i_ir, i_sfh, ir_sav, sfh_sav;
	static int nfilt, filt_id[NMAX], fit[NMAX], ifilt;
	static char filt_name[NMAX][12];
	static char outfile1[100];
	static char gal_name[30], aux_name[30];
	static char optlib[35], irlib[27];
	static char filters[81], obs[81];
	//redshift libs
	static int nz;
	static double zlib[NZMAX], diffz[NZMAX];

	//observations, filters, etc.
	static double w[NMAX], redshift, dist;
	static double flux_obs[NMAX], sigma[NMAX], aux;
	static double flux_obs_mask[NMAX];
	static double filt_sfh_mask[NMAX];
	static double filt_ir_mask[NMAX];
	static double flux_sfh[NMAX][NMOD], ssfr[NMOD];
	static double lambda_eff[NMAX], lambda_rest[NMAX];

	//model libraries, parameters, etc.
	static int n_flux, indx[NMOD];
	static double fprop_sfh[NPROP_SFH][NMOD], fmu_sfh[NMOD];
	static double fprop_ir[NPROP_IR][NMOD], fmu_ir[NMOD];
	static double ldust[NMOD], mstr1[NMOD], logldust[NMOD], lssfr[NMOD];
	static double flux_ir[NMAX][NMOD], tvism[NMOD], tauv[NMOD], mu[NMOD];
	static double tbg1[NMOD], tbg2[NMOD], xi1[NMOD], xi2[NMOD], xi3[NMOD];
	static double fmu_ism[NMOD], mdust[NMOD], lmdust[NMOD];

	//chi2, scaling factors, etc.
	static double flux_mod[NMAX];
	static double chi2, chi2_sav, chi2_new, df;
	static double a, num, den, a_sav;
	static double ptot, prob, chi2_new_opt, chi2_new_ir;
	static double chi2_opt, chi2_ir, chi2_sav_opt, chi2_sav_ir;

	//histograms
	static double fmu_min, fmu_max, dfmu;
	static double ssfr_min, ssfr_max, dssfr;
	static double fmuism_min, fmuism_max, dfmu_ism;
	static double mu_min, mu_max, dmu;
	static double tv_min, tv_max, dtv, dtvism;
	static double sfr_min, sfr_max, dsfr;
	static double a_min, a_max, da;
	static double md_min, md_max, dmd;
	static double ld_min, ld_max, dldust;
	static double tbg1_min, tbg1_max, dtbg, tbg2_min, tbg2_max;
	static double xi_min, xi_max, dxi;
	static double pct_sfr[5], pct_fmu_sfh[5], pct_fmu_ir[5];
	static double pct_mu[5], pct_tv[5], pct_mstr[5];
	static double pct_ssfr[5], pct_ld[5], pct_tbg2[5];
	static double pct_tbg1[5], pct_xi1[5], pct_xi2[5];
	static double pct_xi3[5], pct_tvism[5], pct_ism[5], pct_md[5];

	static double psfh2[NBINMAX2], pir2[NBINMAX2], pmu2[NBINMAX2];
	static double ptv2[NBINMAX2], pxi2_2[NBINMAX2], pssfr2[NBINMAX2];
	static double pa2[NBINMAX2], pldust2[NBINMAX2];
	static double ptbg1_2[NBINMAX2], ptbg2_2[NBINMAX2], pxi1_2[NBINMAX2];
	static double ptvism2[NBINMAX2], pism2[NBINMAX2], pxi3_2[NBINMAX2];
	static double fmuism2_hist[NBINMAX2], md2_hist[NBINMAX2];
	static double ssfr2_hist[NBINMAX2], psfr2[NBINMAX2], pmd_2[NBINMAX2];
	static double fmu2_hist[NBINMAX2], mu2_hist[NBINMAX2], tv2_hist[NBINMAX2];

	static double sfr2_hist[NBINMAX2], a2_hist[NBINMAX2], ld2_hist[NBINMAX2];
	static double tbg1_2_hist[NBINMAX2], tbg2_2_hist[NBINMAX2], xi2_hist[NBINMAX2];
	static double tvism2_hist[NBINMAX2];

	//The highest probability bin values
	static double hpbv;
	static int nbin_fmu, nbin_mu, nbin_tv, nbin_a, nbin2_tvism;
	static int nbin_tbg1, nbin_tbg2, nbin_xi, nbin_sfr, nbin_ld;
	static int nbin2_fmu, nbin2_mu, nbin2_tv, nbin2_a, nbin_fmu_ism;
	static int nbin2_fmu_ism, nbin_md, nbin2_md, nbin_ssfr, nbin2_ssfr;
	static int nbin2_tbg1, nbin2_tbg2, nbin2_xi, nbin2_sfr, nbin2_ld;

	static double sfh_hist[NMOD], ir_hist[NMOD];

	static double fmu_hist[NBINMAX1], psfh[NBINMAX1], pism[NBINMAX1];
	static double pir[NBINMAX1], ptbg1[NBINMAX1];
	static double mu_hist[NBINMAX1], pmu[NBINMAX1], ptbg2[NBINMAX1];
	static double tv_hist[NBINMAX1], ptv[NBINMAX1], ptvism[NBINMAX1];
	static double sfr_hist[NBINMAX1], psfr[NBINMAX1], fmuism_hist[NBINMAX1];
	static double pssfr[NBINMAX1], a_hist[NBINMAX1], pa[NBINMAX1];
	static double pachk[NBINMAX1];
	static double ld_hist[NBINMAX1], pldust[NBINMAX1];
	static double tbg1_hist[NBINMAX1], tbg2_hist[NBINMAX1];
	static double ssfr_hist[NBINMAX1], xi_hist[NBINMAX1], pxi1[NBINMAX1];
	static double pxi2[NBINMAX1], pxi3[NBINMAX1];
	static double md_hist[NBINMAX1], pmd[NBINMAX1];

	static int i_fmu_sfh[NMOD], i_fmu_ir[NMOD];
	static int i_mu[NMOD], i_tauv[NMOD], i_tvism[NMOD];
	static int i_lssfr[NMOD], i_fmu_ism[NMOD];
	static int i_tbg1[NMOD], i_xi1[NMOD], i_xi2[NMOD], i_xi3[NMOD];
	static int i_tbg2[NMOD];

	// {F77} c     cosmological parameters
	static double h, omega, omega_lambda, q;

	//histogram parameters: min,max,bin width
	fmu_min = 0, fmu_max = 1.0005f, dfmu = 0.001f;
	fmuism_min = 0, fmuism_max = 1.0005f, dfmu_ism = 0.001f;
	mu_min = 0, mu_max = 1.0005f, dmu = 0.001f;
	tv_min = 0, tv_max = 6.0025f, dtv = 0.005f;
	ssfr_min = -13, ssfr_max = -5.9975f, dssfr = 0.05f;
	sfr_min = -8, sfr_max = 3.5005f, dsfr = 0.005f;
	a_min = 2, a_max = 13.0025f, da = 0.005f;
	ld_min = 2, ld_max = 13.0025f, dldust = 0.005f;
	tbg1_min = 30, tbg1_max = 60.0125f, dtbg = 0.025f;
	tbg2_min = 15, tbg2_max = 25.0125f;
	xi_min = 0, xi_max = 1.0001f, dxi = 0.001f;
	md_min = -2, md_max = 9, dmd = 0.005f;

	//cosmology
	h = 70, omega = 0.30f, omega_lambda = 0.70f;

	i_gal = 0;
	if (argc == 4){
		i_gal = atoi(argv[1]) - 1;
		std::strcpy(filters, argv[2]);
		std::strcpy(obs, argv[3]);
	}
	else{
		std::cout << "Requires arguments: pixel to fit, filters file, observations file" << endl;
		exit(-1);
	}

	//---------------------------------------------------------------------------
	// Set things up: what filters to use, observations and models:
	//---------------------------------------------------------------------------

	//READ FILTER FILE: "filters.dat"
	ifstream infs;
	stringstream ss;
	string line;

	string filtername(filters, 0, 81);
	Parser filterParser(filtername);
	filterParser.Ignore("#", "\n");

	nfilt = 0;
	vector<string> filtertokens;
	while (filterParser.Good())
	{
		filterParser.Next();

		filterParser.GetTokens(filtertokens);
		if (filtertokens.size() > 0) {
			std::strncpy(filt_name[nfilt], filtertokens[0].c_str(), 16);
			lambda_eff[nfilt] = atof(filtertokens[1].c_str());
			filt_id[nfilt] = atoi(filtertokens[2].c_str());
			fit[nfilt] = atoi(filtertokens[3].c_str());

			nfilt++;
		}
	}

	//READ FILE WITH OBSERVATIONS:
	string obsname(obs, 0, 81);
	Parser obsParser(obsname);
	obsParser.Ignore("#", "\n");

	n_obs = 0;
	vector<string> obstokens;
	while (obsParser.Good())
	{
		obsParser.Next();

		obsParser.GetTokens(obstokens);
		if (obstokens.size() > 0) {
			if (n_obs == i_gal) {
				std::strncpy(gal_name, obstokens[0].c_str(), 30);
				redshift = atof(obstokens[1].c_str());
				j = 2;
				for (k = 0; k < nfilt; k++){
					flux_obs[k] = atof(obstokens[j++].c_str());
					sigma[k] = atof(obstokens[j++].c_str());
				}
			}
			n_obs++;
		}

	}

	//READ FILE WITH REDSHIFTS OF THE MODEL LIBRARIES
	infs.open("zlibs.dat");
	if (!infs.is_open()){
		cerr << "Error opening zlibs.dat" << endl;
		exit(-1);
	}
	nz = 0;
	while (getline(infs, line)){
		if (line[0] != '#'){
			ss.str("");
			ss.clear();
			ss << line;
			ss >> i >> zlib[nz];
			nz++;
		}
	}
	infs.close();

	//CHOOSE GALAXY TO FIT (enter corresponding i)
	std::cout << i_gal + 1 << "\t" << n_obs << endl;

	//Do we have the observation
	if (i_gal + 1 > n_obs){
		cerr << "Observation does not exist" << endl;
		exit(-1);
	}

	//WHAT OBSERVATIONS DO YOU WANT TO FIT?
	//  fit(ifilt)=1: fit flux from filter ifilt
	//  fit(ifilt)=0: do not fit flux from filter ifilt (set flux=-99)
	for (ifilt = 0; ifilt < nfilt; ifilt++){
		if (fit[ifilt] == 0){
			flux_obs[ifilt] = -99;
			sigma[ifilt] = -99;
		}
	}

	//Count number of non-zero fluxes (i.e. detections) to fit
	n_flux = 0;
	for (k = 0; k < nfilt; k++){
		if (flux_obs[k] > 0){
			n_flux++;
		}
	}

	std::cout << "n_flux = " << n_flux << endl;
	if (n_flux < 4){
		exit(-1);
	}

	//COMPUTE LUMINOSITY DISTANCE from z given cosmology
	// Obtain cosmological constant and q

	get_cosmol_c(h, omega, omega_lambda, &q);

	//Compute distance in Mpc from the redshifts z
	dist = get_dl(h, q, redshift);
	dist = dist * (3.086e+24f) / sqrt(1 + redshift);

	//OUTPUT FILES
	// name.fit: fit results, PDFs etc
	std::strcpy(aux_name, gal_name);
	FILE * fitfp;
	fitfp = NULL;
	std::sprintf(outfile1, "%d.fit", i_gal + 1);
	fitfp = fopen(outfile1, "w");
	if (!fitfp){
		cerr << "Could not open fit file: " << outfile1 << endl;
	}
	std::fprintf(fitfp, " ####### %s", gal_name);
	//We need to iterate the length of the char array like fortran seems to be doing.
	for (i = strlen(gal_name); i<30; i++){
		std::fprintf(fitfp, " ");
	}
	std::fprintf(fitfp, "\n");

	// Choose libraries according to the redshift of the source
	// Find zlib(i) closest of the galaxie's redshift
	for (i = 0; i<nz; i++){
		diffz[i] = fabs(zlib[i] - redshift);
	}

	sort2(diffz, zlib, 0, nz - 1);

	// diff(1): minimum difference
	// zlib(1): library z we use for this galaxy
	//   (if diffz(1) not gt 0.005)

	if (diffz[0] > 0.005f && fmod(redshift * 1000, 10) != 5){
		cerr << "No model library at this galaxy redshift..." << endl;
		exit(-1);
	}

	//  snprintf(numz, 6, "%f.4",zlib[0]);
	_snprintf(optlib, 35, "starformhist_cb07_z%6.4f.lbr", zlib[0]);
	_snprintf(irlib, 27, "infrared_dce08_z%6.4f.lbr", zlib[0]);

	std::cout << "z = " << redshift << endl;
	std::cout << "optlib = " << optlib << endl;
	std::cout << "irlib = " << irlib << endl;

	// ---------------------------------------------------------------------------
	// What part of the SED are the filters sampling at the redshift of the galaxy?
	//  - lambda(rest-frame) < 2.5 mic : emission purely stellar (attenuated by dust)
	//  - 2.5 mic < lambda(rest-frame) < 10 mic : stellar + dust emission
	//  - lambda(rest-frame) > 10 mic : emission purely from dust
	// ---------------------------------------------------------------------------

	nfilt_sfh = nfilt_ir = nfilt_mix = 0;
	for (i = 0; i<nfilt; i++){
		lambda_rest[i] = lambda_eff[i] / (1 + redshift);
		if (lambda_rest[i] < 10){
			nfilt_sfh++;
		}
		if (lambda_rest[i] > 2.5f){
			nfilt_ir++;
		}
		if (lambda_rest[i] > 2.5f && lambda_rest[i] <= 10){
			nfilt_mix++;
		}
	}
	std::cout << "   " << endl;
	std::cout << "At this redshift: " << endl;

	for (k = 0; k < (nfilt_sfh - nfilt_mix); k++){
		std::cout << "purely stellar... " << filt_name[k] << endl;
	}

	for (k = nfilt_sfh - nfilt_mix; k < nfilt_sfh; k++){
		std::cout << "mix stars+dust... " << filt_name[k] << endl;
	}
	for (k = nfilt_sfh; k < nfilt; k++){
		std::cout << "purely dust... " << filt_name[k] << endl;
	}

	// ---------------------------------------------------------------------------
	// MODELS: read libraries of models with parameters + AB mags at z
	// attenuated stellar emission - optlib: starformhist_cb07_z###.lbr
	// --> nfilt_sfh model absolute AB mags
	// dust emission - irlib: infrared_dce08_z###.lbr
	// --> nfilt_ir model absolute AB mags
	// ---------------------------------------------------------------------------
	std::cout << "Reading SFH library..." << endl;

	string sfhname(optlib, 0, 35);
	Parser sfhParser(sfhname);
	sfhParser.Ignore("#", "\n");

	n_sfh = 0;
	int i_line = 0;
	vector<string> sfhtokens;
	while (sfhParser.Good())
	{
		sfhParser.Next();
		i_line++;

		if (i_line > 1){
			sfhParser.GetTokens(sfhtokens);
			if (sfhtokens.size() > 0) {
				indx[n_sfh] = atoi(sfhtokens[0].c_str());
				for (j = 0; j < NPROP_SFH; j++){
					fprop_sfh[j][n_sfh] = atof(sfhtokens[1 + j].c_str());
				}
				for (j = 0; j < nfilt_sfh; j++){
					flux_sfh[j][n_sfh] = atof(sfhtokens[1 + NPROP_SFH + j].c_str());
				}

				fmu_sfh[n_sfh] = fprop_sfh[21][n_sfh];
				mstr1[n_sfh] = fprop_sfh[5][n_sfh];
				ldust[n_sfh] = fprop_sfh[20][n_sfh] / mstr1[n_sfh];
				logldust[n_sfh] = log10(ldust[n_sfh]);
				mu[n_sfh] = fprop_sfh[4][n_sfh];
				tauv[n_sfh] = fprop_sfh[3][n_sfh];
				ssfr[n_sfh] = fprop_sfh[9][n_sfh] / mstr1[n_sfh];
				lssfr[n_sfh] = log10(ssfr[n_sfh]);
				tvism[n_sfh] = mu[n_sfh] * tauv[n_sfh];

				for (k = 0; k < nfilt_sfh; k++){
					flux_sfh[k][n_sfh] = 3.117336e+6f*pow(10, -0.4f*(flux_sfh[k][n_sfh] + 48.6f));
					flux_sfh[k][n_sfh] = flux_sfh[k][n_sfh] / mstr1[n_sfh];
					flux_sfh[k][n_sfh] = flux_sfh[k][n_sfh] / (1 + redshift);
				}
				n_sfh++;
			}
		}
	}
	std::cout << "  Loaded " << n_sfh << endl;

	// READ IRLIB
	// IR model parameters
	// .lbr contains absolute AB magnitudes -> convert to fluxes Fnu in Lo/Hz
	//  Re-define IR parameters: xi^tot
	std::cout << "Reading IR dust emission library..." << endl;
	string irname(irlib, 0, 35);
	Parser irParser(irname);
	irParser.Ignore("#", "\n");
	vector<string> irtokens;
	n_ir = 0;
	while (irParser.Good())
	{
		irParser.Next();
		irParser.GetTokens(irtokens);
		if (irtokens.size() > 0) {
			for (j = 0; j < NPROP_IR; j++){
				//if (fabs(fprop_ir[j][n_ir] - atof(irtokens[j].c_str()) ) > std::numeric_limits<double>::epsilon()) {
				fprop_ir[j][n_ir] = atof(irtokens[j].c_str());

			}
			for (j = 0; j < nfilt_ir; j++){
				flux_ir[j][n_ir] = atof(irtokens[NPROP_IR + j].c_str());
			}

			// We need to subtract array index by 1 due to fortran difference.
			fmu_ir[n_ir] = fprop_ir[0][n_ir];
			fmu_ism[n_ir] = fprop_ir[1][n_ir];
			tbg1[n_ir] = fprop_ir[2][n_ir];
			tbg2[n_ir] = fprop_ir[3][n_ir];
			xi1[n_ir] = fprop_ir[4][n_ir];
			xi2[n_ir] = fprop_ir[5][n_ir];
			xi3[n_ir] = fprop_ir[6][n_ir];
			mdust[n_ir] = fprop_ir[7][n_ir];

			for (k = 0; k < nfilt_ir; k++){
				flux_ir[k][n_ir] = 3.117336e+6f*pow(10, -0.4f*(flux_ir[k][n_ir] + 48.6f));
				flux_ir[k][n_ir] = flux_ir[k][n_ir] / (1 + redshift);
			}

			xi1[n_ir] = xi1[n_ir] * (1 - fmu_ir[n_ir]) + 0.550f*(1 - fmu_ism[n_ir])*fmu_ir[n_ir];
			xi2[n_ir] = xi2[n_ir] * (1 - fmu_ir[n_ir]) + 0.275f*(1 - fmu_ism[n_ir])*fmu_ir[n_ir];
			xi3[n_ir] = xi3[n_ir] * (1 - fmu_ir[n_ir]) + 0.175f*(1 - fmu_ism[n_ir])*fmu_ir[n_ir];
			fmu_ism[n_ir] = fmu_ism[n_ir] * fmu_ir[n_ir];

			n_ir++;
		}
	}
	std::cout << "  Loaded " << n_ir << endl;

	// ---------------------------------------------------------------------------
	// COMPARISON BETWEEN MODELS AND OBSERVATIONS:
	// 
	// Compare everything in the sample units:
	// Lnu (i.e. luminosity per unit frequency) in Lsun/Hz
	// 
	// Model fluxes: already converted from AB mags to Lnu in Lsun/Hz
	// Fluxes and physical parameters from optical library per unit Mstar=1 Msun
	// Fluxes and physical parameters from infrared library per unit Ldust=1 Lsun
	// 
	// Observed fluxes & uncertainties
	// Convert from Fnu in Jy to Lnu in Lo/Hz [using luminosity distance dist(i_gal)]
	// ---------------------------------------------------------------------------
	for (k = 0; k<nfilt; k++){
		if (flux_obs[k] > 0){
			flux_obs[k] = flux_obs[k] * 1.0e-23f*3.283608731e-33f*pow(dist, 2);
			sigma[k] = sigma[k] * 1.0e-23f*3.283608731e-33f*pow(dist, 2);
		}
		if (sigma[k] < 0.05f*flux_obs[k]){
			sigma[k] = 0.05f*flux_obs[k];
		}
	}
	for (k = 0; k<nfilt; k++){
		if (sigma[k] > 0.0){
			w[k] = 1.0 / (pow(sigma[k], 2));
		}
	}

	//Initialize variables:
	n_models = 0;
	chi2_sav = 1.0e30f;
	ptot = 0;
	prob = 0;
	for (k = 0; k<nfilt; k++){
		flux_mod[k] = 0;
	}
	for (i = 0; i < NMOD; i++){
		sfh_hist[i] = 0;
		ir_hist[i] = 0;
	}
	for (i = 0; i<NBINMAX1; i++){
		psfh[i] = 0;
		pir[i] = 0;
		pmu[i] = 0;
		ptv[i] = 0;
		ptvism[i] = 0;
		pssfr[i] = 0;
		psfr[i] = 0;
		pa[i] = 0;
		pldust[i] = 0;
		ptbg1[i] = 0;
		ptbg2[i] = 0;
		pism[i] = 0;
		pxi1[i] = 0;
		pxi2[i] = 0;
		pxi3[i] = 0;
		pmd[i] = 0;
	}

	// ---------------------------------------------------------------------------
	// Compute histogram grids of the parameter likelihood distributions before
	// starting the big loop in which we compute chi^2 for each allowed combination
	// of stellar+dust emission model (to save time).
	//
	// The high-resolution marginalized likelihood distributions will be
	// computed on-the-run
	// ---------------------------------------------------------------------------

	// f_mu (SFH) & f_mu (IR)
	get_histgrid(dfmu, fmu_min, fmu_max, &nbin_fmu, fmu_hist);
	// mu parameter
	get_histgrid(dmu, mu_min, mu_max, &nbin_mu, mu_hist);
	// tauv (dust optical depth)
	get_histgrid(dtv, tv_min, tv_max, &nbin_tv, tv_hist);
	// sSFR
	get_histgrid(dssfr, ssfr_min, ssfr_max, &nbin_ssfr, ssfr_hist);
	// SFR
	get_histgrid(dsfr, sfr_min, sfr_max, &nbin_sfr, sfr_hist);
	// Mstars
	get_histgrid(da, a_min, a_max, &nbin_a, a_hist);
	// Ldust
	get_histgrid(dldust, ld_min, ld_max, &nbin_ld, ld_hist);
	// fmu_ism
	get_histgrid(dfmu_ism, fmuism_min, fmuism_max, &nbin_fmu_ism, fmuism_hist);
	// T_BGs (ISM)
	get_histgrid(dtbg, tbg1_min, tbg1_max, &nbin_tbg1, tbg1_hist);
	// T_BGs (BC)
	get_histgrid(dtbg, tbg2_min, tbg2_max, &nbin_tbg2, tbg2_hist);
	// xi's (PAHs, VSGs, BGs)
	get_histgrid(dxi, xi_min, xi_max, &nbin_xi, xi_hist);
	// Mdust
	get_histgrid(dmd, md_min, md_max, &nbin_md, md_hist);

	// Compute histogram indexes for each parameter value
	// [makes code faster -- implemented by the Nottingham people]
	//Moved Min Max Check From Fit Loop to Here.
	//sfh models histogram indexes
	for (i_sfh = 0; i_sfh<n_sfh; i_sfh++){
		aux = ((fmu_sfh[i_sfh] - fmu_min) / (fmu_max - fmu_min)) * nbin_fmu;
		i_fmu_sfh[i_sfh] = max(0, min((int)(aux), nbin_fmu - 1));

		aux = ((mu[i_sfh] - mu_min) / (mu_max - mu_min)) * nbin_mu;
		i_mu[i_sfh] = max(0, min((int)(aux), nbin_mu - 1));

		aux = ((tauv[i_sfh] - tv_min) / (tv_max - tv_min)) * nbin_tv;
		i_tauv[i_sfh] = max(0, min((int)(aux), nbin_tv - 1));

		aux = ((tvism[i_sfh] - tv_min) / (tv_max - tv_min)) * nbin_tv;
		i_tvism[i_sfh] = max(0, min((int)(aux), nbin_tv - 1));

		if (lssfr[i_sfh] < ssfr_min){
			lssfr[i_sfh] = ssfr_min;
		}

		aux = ((lssfr[i_sfh] - ssfr_min) / (ssfr_max - ssfr_min)) * nbin_ssfr;
		i_lssfr[i_sfh] = max(0, min((int)(aux), nbin_sfr - 1));
	}

	//ir models histogram indexes
	for (i_ir = 0; i_ir<n_ir; i_ir++){
		aux = ((fmu_ir[i_ir] - fmu_min) / (fmu_max - fmu_min)) * nbin_fmu;
		i_fmu_ir[i_ir] = max(0, min((int)(aux), nbin_fmu - 1));

		aux = ((fmu_ism[i_ir] - fmuism_min) / (fmuism_max - fmuism_min))*nbin_fmu_ism;
		i_fmu_ism[i_ir] = max(0, min((int)(aux), nbin_fmu_ism - 1));

		aux = ((tbg1[i_ir] - tbg1_min) / (tbg1_max - tbg1_min))* nbin_tbg1;
		i_tbg1[i_ir] = max(0, min((int)(aux), nbin_tbg1 - 1));

		aux = ((tbg2[i_ir] - tbg2_min) / (tbg2_max - tbg2_min))* nbin_tbg2;
		i_tbg2[i_ir] = max(0, min((int)(aux), nbin_tbg2 - 1));

		aux = ((xi1[i_ir] - xi_min) / (xi_max - xi_min)) * nbin_xi;
		i_xi1[i_ir] = max(0, min((int)(aux), nbin_xi - 1));

		aux = ((xi2[i_ir] - xi_min) / (xi_max - xi_min)) * nbin_xi;
		i_xi2[i_ir] = max(0, min((int)(aux), nbin_xi - 1));

		aux = ((xi3[i_ir] - xi_min) / (xi_max - xi_min)) * nbin_xi;
		i_xi3[i_ir] = max(0, min((int)(aux), nbin_xi - 1));
	}


	// ---------------------------------------------------------------------------
	// HERE STARTS THE ACTUAL FIT
	// 
	// For each model in the stellar library, find all the models in the infrared
	// dust emission library for which the proportion of dust luminosity from stellar
	// birth clouds and diffuse ISM is the same, i.e. same "fmu" parameter (+/- df)
	// Scale each infrared model satisfying this condition to the total dust
	// luminosity Ldust predicted by the stellar+attenuation model
	// [this satisfies the energy balance]
	// 
	// 
	// For each combination of model, compute the chi^2 goodness-of-fit
	// by comparing the observed UV-to-IR fluxes with the model predictions
	// 
	// The scaling factor "a" is in practice the stellar mass of the model
	// since all the fluxes are normalised to Mstar
	// 
	// The probability of each model is p=exp(-chi^2/2)
	// Compute marginal likelihood distributions of each parameter
	// and build high-resolution histogram of each PDF
	// ---------------------------------------------------------------------------
	std::cout << "Starting fit......." << endl;
	df = 0.15f;

	// OpenCL implementation of fitting process.

	// Build struct array of models and indexes of length NMOD that will be used
	// in the kernel threads. Cleaner than passing individual arrays.
	std::vector<clmod_sfh_t> h_clmods_sfh;
	for (i = 0; i<NMOD; i++){
		clmod_sfh_t clmod;
		clmod.lssfr = lssfr[i];
		clmod.logldust = logldust[i];
		clmod.ldust = ldust[i];
		for (j = 0; j < nfilt_sfh; j++){
			clmod.flux_sfh[j] = flux_sfh[j][i];
		}

		h_clmods_sfh.push_back(clmod);
	}

	std::vector<clmod_ir_t> h_clmods_ir;
	for (i = 0; i<NMOD; i++){
		clmod_ir_t clmod;
		clmod.mdust = mdust[i];
		for (j = nfilt_sfh - nfilt_mix; j < nfilt_sfh; j++){ //Set for Vector addition.
			clmod.flux_ir[j] = mdust[i] * flux_ir[j - nfilt_sfh + nfilt_mix][i];
		}
		for (j = nfilt_sfh; j < nfilt; j++){
			clmod.flux_ir[j] = flux_ir[j - nfilt_sfh + nfilt_mix][i];
		}
		h_clmods_ir.push_back(clmod);
	}

	for (i = 0; i < CLBLOCKSIZE_RED; i++){
		cl_sum[i] = 0;
		cl_minchi[i] = INFINITY;
	}
	for (i = 0; i < NMAX; i++){
		if (i<nfilt && flux_obs[i]>0) {
			flux_obs_mask[i] = 1;
		}
		else {
			flux_obs_mask[i] = 0;
		}
	}
	for (i = 0; i < NMAX; i++){
		if (i<nfilt_sfh) {
			filt_sfh_mask[i] = 1;
		}
		else {
			filt_sfh_mask[i] = 0;
		}
		if (i >= nfilt_sfh && i<nfilt) {
			filt_ir_mask[i] = 1;
		}
		else {
			filt_ir_mask[i] = 0;
		}
	}

	// Push constants into struct that kernel threads will use.
	clconstants_t h_clconstants;
	h_clconstants.nbin_sfr = nbin_sfr;
	h_clconstants.nbin_a = nbin_a;
	h_clconstants.nbin_ld = nbin_ld;
	h_clconstants.nbin_md = nbin_md;
	h_clconstants.a_max = a_max;
	h_clconstants.a_min = a_min;
	h_clconstants.sfr_max = sfr_max;
	h_clconstants.sfr_min = sfr_min;
	h_clconstants.ld_max = ld_max;
	h_clconstants.ld_min = ld_min;
	h_clconstants.md_max = md_max;
	h_clconstants.md_min = md_min;
	h_clconstants.nfilt = nfilt;
	h_clconstants.nfilt_sfh = nfilt_sfh;
	h_clconstants.nfilt_mix = nfilt_mix;
	h_clconstants.i_gal = i_gal;
	h_clconstants.df = df;
	h_clconstants.n_sfh = n_sfh;
	h_clconstants.n_ir = n_ir;

	// Catch all OpenCL errors and exit if one is thrown.
	try{
		// Read platforms and select first OpenCL device
		std::vector<cl::Platform> platforms;
		cl::Platform::get(&platforms);
		if (platforms.size() == 0){
			return EXIT_FAILURE;
		}
		cl::Platform platform = platforms[0];
		cl_context_properties cps[3] = { CL_CONTEXT_PLATFORM, (cl_context_properties)(platform)(), 0 };
		cl::Context context(CL_DEVICE_TYPE_GPU, cps);
		std::vector<cl::Device> devices;
		platform.getDevices(CL_DEVICE_TYPE_GPU, &devices);
		if (devices.size() == 0){
			return EXIT_FAILURE;
		}
		std::cout << "DeviceName " << j << " " << devices[0].getInfo<CL_DEVICE_NAME>() << endl;
		std::cout << "  Compute Units " << devices[0].getInfo<CL_DEVICE_MAX_COMPUTE_UNITS>() << endl;
		std::cout << "  Clock Freq    " << devices[0].getInfo<CL_DEVICE_MAX_CLOCK_FREQUENCY>() << endl;
		std::cout << "  Local Mem     " << devices[0].getInfo<CL_DEVICE_LOCAL_MEM_SIZE>() << endl;
		std::cout << "  Global Mem    " << devices[0].getInfo<CL_DEVICE_GLOBAL_MEM_SIZE>() << endl;
		int gpu_compute = devices[0].getInfo<CL_DEVICE_MAX_COMPUTE_UNITS>();
		long gpu_localmem = devices[0].getInfo<CL_DEVICE_LOCAL_MEM_SIZE>();
		cl::Device device = devices[0];

		// Create a command queue for first device.
		cl::CommandQueue queue(cl::CommandQueue(context, device, CL_QUEUE_PROFILING_ENABLE));

		// Read in kernel program from file.
#ifdef READCL
		std::ifstream sourceFile("fit_sed_skynet.cl");
		std::string sourceCode(
			std::istreambuf_iterator<char>(sourceFile),
			(std::istreambuf_iterator<char>()));
		cl::Program::Sources source(1, std::make_pair(sourceCode.c_str(), sourceCode.length() + 1));
#else
		cl::Program::Sources source(1, std::make_pair(kernelSource, strlen(kernelSource)));
#endif
		cl::Program fit_program = cl::Program(context, source);

		// Attempt to build kernel program. Echo build error if unsuccesful.
		try{
			fit_program.build(devices);
		}
		catch (cl::Error error){
			cerr << fit_program.getBuildInfo<CL_PROGRAM_BUILD_LOG>(devices[0]) << endl;
		}

		// Buffer necessary object space onto device memory.
		cl::Buffer d_fmu_sfh = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, NMOD*sizeof(double), fmu_sfh, NULL);
		cl::Buffer d_fmu_ir = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, NMOD*sizeof(double), fmu_ir, NULL);
		cl::Buffer d_withindf = cl::Buffer(context, CL_MEM_WRITE_ONLY | CL_MEM_USE_HOST_PTR, CLDFSIZE*sizeof(unsigned int), withindf, NULL);

		cl::Buffer d_clclconstants = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, sizeof(clconstants_t), &h_clconstants, NULL);
		cl::Buffer d_clmods_sfh = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, h_clmods_sfh.size()*sizeof(clmod_sfh_t), &h_clmods_sfh[0], NULL);
		cl::Buffer d_clmods_ir = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, h_clmods_ir.size()*sizeof(clmod_ir_t), &h_clmods_ir[0], NULL);
		cl::Buffer d_flux_obs = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, NMAX*sizeof(double), flux_obs, NULL);
		cl::Buffer d_flux_obs_mask = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, NMAX*sizeof(double), flux_obs_mask, NULL);
		cl::Buffer d_filt_sfh_mask = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, NMAX*sizeof(double), filt_sfh_mask, NULL);
		cl::Buffer d_filt_ir_mask = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, NMAX*sizeof(double), filt_ir_mask, NULL);
		cl::Buffer d_w = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, NMAX*sizeof(double), w, NULL);

		cl::Buffer d_cl_sfh = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(unsigned short), cl_sfh , NULL);
		cl::Buffer d_cl_ir = cl::Buffer(context, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(unsigned short), cl_ir, NULL);
		cl::Buffer d_cl_chi2 = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(double), cl_chi2, NULL);
		cl::Buffer d_cl_prob = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(double), cl_prob, NULL);
		cl::Buffer d_ibin_pa = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(unsigned short), ibin_pa, NULL);
		cl::Buffer d_ibin_psfr = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(unsigned short), ibin_psfr, NULL);
		cl::Buffer d_ibin_pldust = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(unsigned short), ibin_pldust, NULL);
		cl::Buffer d_ibin_pmdust = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLMAX*sizeof(unsigned short), ibin_pmdust, NULL);

		cl::Buffer d_cl_sum = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLBLOCKSIZE_RED*sizeof(double), cl_sum, NULL);
		cl::Buffer d_cl_minchi = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLBLOCKSIZE_RED*sizeof(double), cl_minchi, NULL);
		cl::Buffer d_cl_minsfh = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLBLOCKSIZE_RED*sizeof(unsigned short), cl_minsfh, NULL);
		cl::Buffer d_cl_minir = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, CLBLOCKSIZE_RED*sizeof(unsigned short), cl_minir, NULL);

		cl::Buffer d_sfh_hist = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, NMOD*sizeof(double), sfh_hist, NULL);
		cl::Buffer d_ir_hist = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, NMOD*sizeof(double), ir_hist, NULL);
		cl::Buffer d_pa = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, NBINMAX1*sizeof(double), pa, NULL);
		cl::Buffer d_psfr = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, NBINMAX1*sizeof(double), psfr, NULL);
		cl::Buffer d_pldust = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, NBINMAX1*sizeof(double), pldust, NULL);
		cl::Buffer d_pmdust = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, NBINMAX1*sizeof(double), pmd, NULL);

		// Write static objects into reserved device memory.
		queue.enqueueWriteBuffer(d_clclconstants, CL_TRUE, 0, sizeof(clconstants_t), &h_clconstants);
		queue.enqueueWriteBuffer(d_clmods_sfh, CL_TRUE, 0, h_clmods_sfh.size()*sizeof(clmod_sfh_t), &h_clmods_sfh[0]);
		queue.enqueueWriteBuffer(d_clmods_ir, CL_TRUE, 0, h_clmods_ir.size()*sizeof(clmod_ir_t), &h_clmods_ir[0]);
		queue.enqueueWriteBuffer(d_flux_obs, CL_TRUE, 0, NMAX*sizeof(double), flux_obs);
		queue.enqueueWriteBuffer(d_flux_obs_mask, CL_TRUE, 0, NMAX*sizeof(double), flux_obs_mask);
		queue.enqueueWriteBuffer(d_filt_sfh_mask, CL_TRUE, 0, NMAX*sizeof(double), filt_sfh_mask);
		queue.enqueueWriteBuffer(d_filt_ir_mask, CL_TRUE, 0, NMAX*sizeof(double), filt_ir_mask);
		queue.enqueueWriteBuffer(d_w, CL_TRUE, 0, NMAX*sizeof(double), w);

		queue.enqueueWriteBuffer(d_cl_sum, CL_FALSE, 0, CLBLOCKSIZE_RED*sizeof(double), cl_sum);
		queue.enqueueWriteBuffer(d_cl_minchi, CL_FALSE, 0, CLBLOCKSIZE_RED*sizeof(double), cl_minchi);

		queue.enqueueWriteBuffer(d_fmu_sfh, CL_TRUE, 0, NMOD*sizeof(double), fmu_sfh);
		queue.enqueueWriteBuffer(d_fmu_ir, CL_TRUE, 0, NMOD*sizeof(double), fmu_ir);

		//queue.enqueueWriteBuffer(d_pa, CL_TRUE, 0, NBINMAX1*sizeof(double), pa);

		// Prepare kernel program.
		cl::Kernel kernel_checkdf(fit_program, "check_df");
		//Argument 0 is i_sfh to process.
		kernel_checkdf.setArg(1, d_clclconstants);
		kernel_checkdf.setArg(2, d_fmu_sfh);
		kernel_checkdf.setArg(3, d_fmu_ir);
		kernel_checkdf.setArg(4, d_withindf);

		cl::NDRange localSize_checkdf(256);
		cl::NDRange globalSize_checkdf((int)(ceil(CLDFSIZE / (double)256) * 256));

		// Prepare kernel program.
		cl::Kernel kernel_fit(fit_program, "fit");

		// Parse kernel program arguments that will not change.
		//argument 0 will be i_m - number of models to process
		kernel_fit.setArg(1, d_clclconstants);
		kernel_fit.setArg(2, d_clmods_sfh);
		kernel_fit.setArg(3, d_clmods_ir);
		kernel_fit.setArg(4, d_flux_obs);
		kernel_fit.setArg(5, d_w);
		kernel_fit.setArg(6, d_flux_obs_mask);
		kernel_fit.setArg(7, d_filt_sfh_mask);
		kernel_fit.setArg(8, d_filt_ir_mask);
		kernel_fit.setArg(9, d_cl_sfh);
		kernel_fit.setArg(10, d_cl_ir);
		kernel_fit.setArg(11, d_cl_chi2);
		kernel_fit.setArg(12, d_cl_prob);
		kernel_fit.setArg(13, d_ibin_pa);
		kernel_fit.setArg(14, d_ibin_psfr);
		kernel_fit.setArg(15, d_ibin_pldust);
		kernel_fit.setArg(16, d_ibin_pmdust);

		// Set local workload size. Recommend divides NBINMAX1 and 64 evenly and is less/equal to NBIN_SPARSEHISTOGRAM.
		cl::NDRange localSize_fit(CLLOCAL_FIT);
		std::cout << " Fit LocalSize " << CLLOCAL_FIT << " Global Size " << CLMAX << endl;

		// Prepare kernel program.
		cl::Kernel kernel_sumprob(fit_program, "sumprob");
		//argument 0 will be i_m - number of models to process
		kernel_sumprob.setArg(1, d_cl_prob);
		kernel_sumprob.setArg(2, d_cl_sum);
		kernel_sumprob.setArg(3, (CLBLOCKSIZE_RED)*sizeof(double), NULL); //Local Scratch

		// Prepare kernel program.
		cl::Kernel kernel_minchi(fit_program, "minchi");
		//argument 0 will be i_m - number of models to process
		kernel_minchi.setArg(1, d_cl_sfh);
		kernel_minchi.setArg(2, d_cl_ir);
		kernel_minchi.setArg(3, d_cl_chi2);
		kernel_minchi.setArg(4, d_cl_minchi);
		kernel_minchi.setArg(5, d_cl_minsfh);
		kernel_minchi.setArg(6, d_cl_minir);
		kernel_minchi.setArg(7, (CLBLOCKSIZE_RED)*sizeof(double), NULL); //Local Scratch
		kernel_minchi.setArg(8, (CLBLOCKSIZE_RED)*sizeof(unsigned short), NULL); //Local Scratch
		kernel_minchi.setArg(9, (CLBLOCKSIZE_RED)*sizeof(unsigned short), NULL); //Local Scratch

		cl::NDRange localSize_reduce(CLLOCAL_RED);
		std::cout << " Reduce LocalSize " << CLLOCAL_RED << " Global Size " << CLBLOCKSIZE_RED*gpu_compute << endl;

		// Set global workload size.
		cl::NDRange globalSize_reduce(CLBLOCKSIZE_RED*gpu_compute);
		
		// Prepare kernel program.
		//static double cl_range[7 * 8 * NBINMAX1];
		//cl::Buffer d_cl_range = cl::Buffer(context, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR, gpu_compute * 8 * NBINMAX1*sizeof(double), cl_range, NULL);

		//cl::Kernel kernel_sumidtorange(fit_program, "sumidtorange");
		////argument 0 will be i_m - number of models to process
		////argument 1 const int ci_groupSize,
		//// argument 2	const int ci_theadSize,
		////argument 3 will be  - range start
		////argument 4 will be  - range width
		////argument 5 will be unsigned short array of ids.
		//kernel_sumidtorange.setArg(6, d_cl_prob);
		//kernel_sumidtorange.setArg(7, d_cl_range); //Temporary Global to send to sumRangetoarray
		////argument 8 is local scratch
		////argument 9 is local scratch

		//// Prepare kernel program.
		//cl::Kernel kernel_sumrangetoarray(fit_program, "sumrangetoarray");
		////argument 0 will be  - range start
		////argument 1 will be  - range width
		////argument 2 will be - num groups /
		//kernel_sumrangetoarray.setArg(2, gpu_compute * 8);
		//kernel_sumrangetoarray.setArg(3, d_cl_range); //Temporary Global to send to sumRangetoarray
		////argument 4 will be - Array to update. d_sfh_hist d_ir_hist d_pa d_psfr d_pldust d_pmdust
		////kernel_sumrangetoarray.setArg(4, d_sfh_hist);

		//// Set global workload size.
		//cl::NDRange localSize_range(CLLOCAL_RANGE);
		//cl::NDRange globalSize_range(CLLOCAL_RANGE*gpu_compute * 8);

		//std::cout << " Range LocalSize " << CLLOCAL_RANGE << " Global Size " << CLLOCAL_RANGE*gpu_compute * 8 << endl;

		//cl::NDRange localSize_range2(CLBLOCKSIZE_RED);
		//cl::NDRange globalSize_range2(CLBLOCKSIZE_RED*gpu_compute*2);

		//std::cout << " Range2 LocalSize " << CLBLOCKSIZE_RED << " Global Size " << CLBLOCKSIZE_RED*gpu_compute*2 << endl;

		// Event that will be used for getting response.
		cl::Event event;

		int writePercentage = 25;
		std::clock_t clckstart;
		std::clock_t memtime = 0;
		std::clock_t arrtime = 0;
		std::clock_t arrtime1 = 0;
		std::clock_t arrtimedf = 0;
		cl_ulong start, end;
		double cltime = 0;
		double cltimehisto1 = 0;
		double cltimehisto2 = 0;
		int i_kernel = 0;

		//Load withindf for first sfh.
		clckstart = std::clock();
		int i_df = 0;
		kernel_checkdf.setArg(0, 0);
		queue.enqueueNDRangeKernel(kernel_checkdf, cl::NullRange, globalSize_checkdf, localSize_checkdf, NULL, &event);
		event.wait();
		// Read processed model data back from device memory.
		queue.enqueueReadBuffer(d_withindf, CL_TRUE, 0, CLDFSIZE*sizeof(unsigned int), withindf);
		arrtimedf = arrtimedf + (std::clock() - clckstart);

		int i_sfhoffset = 0;
		int i_iroffset = 0;
		int i_dfshift = 0;
		unsigned int ui_df = withindf[i_df];
		i_sfh = 0;
		i_ir = 0;

		while (i_sfh + i_sfhoffset< n_sfh){
			int i_m = 0;

			clckstart = std::clock();
			while (i_sfh + i_sfhoffset<n_sfh && i_m<CLMAX) {

				while (i_df < CLDFSIZE && i_m<CLMAX) {
					while (i_dfshift < 32 && i_m < CLMAX) {
						if ((ui_df & 1) == 1) {
							cl_sfh[i_m] = i_sfh + i_sfhoffset;
							cl_ir[i_m] = i_iroffset + i_dfshift;
							i_m++;
						}
						ui_df = ui_df >> 1;
						i_dfshift++;
					}
					if (i_dfshift == 32) {
						i_dfshift = 0;
						i_df++;
						ui_df = withindf[i_df];
						i_iroffset = i_iroffset + 32;
						if (i_iroffset == NMOD) {
							i_sfhoffset++;
							i_iroffset = 0;
						}
					}
				}
				if (i_df == CLDFSIZE) {
					arrtime = arrtime + (std::clock() - clckstart);
					clckstart = std::clock();
					i_sfh = i_sfh + i_sfhoffset;
					i_sfhoffset = 0;
					i_df = 0;
					kernel_checkdf.setArg(0, i_sfh);
					queue.enqueueNDRangeKernel(kernel_checkdf, cl::NullRange, globalSize_checkdf, localSize_checkdf, NULL, &event);
					event.wait();
					// Read processed model data back from device memory.
					queue.enqueueReadBuffer(d_withindf, CL_TRUE, 0, CLDFSIZE*sizeof(unsigned int), withindf);
					ui_df = withindf[i_df];
					arrtimedf = arrtimedf + (std::clock() - clckstart);
					clckstart = std::clock();
				}

			}
			arrtime = arrtime + (std::clock() - clckstart);

			// Batch up models to process (up to CLMAX).
			n_models += i_m;
			i_kernel++;

			//Calculate Fit
			clckstart = std::clock();
			// Write identifier struct array to device. This will change on a per batch basis.
			queue.enqueueWriteBuffer(d_cl_sfh, CL_TRUE, 0, i_m*sizeof(unsigned short), cl_sfh);
			queue.enqueueWriteBuffer(d_cl_ir, CL_TRUE, 0, i_m*sizeof(unsigned short), cl_ir);
			//void* p_map_clmodels = queue.enqueueMapBuffer(d_clmodels, CL_TRUE, CL_MAP_WRITE, 0, i_m*sizeof(clmodel_t), 0);
			memtime = memtime + (std::clock() - clckstart);

			// Parse kernel program arguments that will change.
			kernel_fit.setArg(0, i_m);

			// Set global workload size. This depends on number models.
			cl::NDRange globalSize_fit((int)(ceil(i_m / (double)CLLOCAL_FIT) * CLLOCAL_FIT));

			// Start the work and wait for response.
			queue.enqueueNDRangeKernel(kernel_fit, cl::NullRange, globalSize_fit, localSize_fit,
				NULL, &event);

			event.wait();

			start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
			end = event.getProfilingInfo<CL_PROFILING_COMMAND_END>();
			cltime = cltime + (end - start);

			//Reduce Prob

			int i_mpow2 = pow(2, floor(log(i_m) / log(2)));
			// Parse kernel program arguments that will change.
			kernel_sumprob.setArg(0, i_mpow2);

			// Start the work and wait for response.
			queue.enqueueNDRangeKernel(kernel_sumprob, cl::NullRange, globalSize_reduce, localSize_reduce,
				NULL, &event);

			event.wait();

			start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
			end = event.getProfilingInfo<CL_PROFILING_COMMAND_END>();
			cltime = cltime + (end - start);

			clckstart = std::clock();
			queue.enqueueReadBuffer(d_cl_sum, CL_TRUE, 0, CLBLOCKSIZE_RED*sizeof(double), cl_sum);
			memtime = memtime + (std::clock() - clckstart);

			clckstart = std::clock();
			for (i = 0; i < CLBLOCKSIZE_RED*gpu_compute / CLLOCAL_RED; i++){
				ptot += cl_sum[i];
				cl_sum[i] = 0;
			}
			arrtime1 = arrtime1 + (std::clock() - clckstart);

			//Write Initialized array back, non-blocking since it's small and we have time...
			queue.enqueueWriteBuffer(d_cl_sum, CL_FALSE, 0, CLBLOCKSIZE_RED*sizeof(double), cl_sum);

			if (i_m != i_mpow2) { //Loop Remaining that doesn't fit nicely into the reducer by pow2. //Last Step
				clckstart = std::clock();
				queue.enqueueReadBuffer(d_cl_prob, CL_TRUE, 0, i_m*sizeof(double), cl_prob);
				memtime = memtime + (std::clock() - clckstart);

				clckstart = std::clock();
				for (i = i_mpow2; i < i_m; i++){
					ptot += cl_prob[i];
				}
				arrtime1 = arrtime1 + (std::clock() - clckstart);
			}

			//Reduce Min Chi - Save i_sfh/i_ir

			// Parse kernel program arguments that will change.
			kernel_minchi.setArg(0, i_mpow2);

			// Start the work and wait for response.
			queue.enqueueNDRangeKernel(kernel_minchi, cl::NullRange, globalSize_reduce, localSize_reduce,
				NULL, &event);

			event.wait();

			start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
			end = event.getProfilingInfo<CL_PROFILING_COMMAND_END>();
			cltime = cltime + (end - start);

			clckstart = std::clock();
			queue.enqueueReadBuffer(d_cl_minchi, CL_TRUE, 0, CLBLOCKSIZE_RED*sizeof(double), cl_minchi);
			queue.enqueueReadBuffer(d_cl_minsfh, CL_TRUE, 0, CLBLOCKSIZE_RED*sizeof(unsigned short), cl_minsfh);
			queue.enqueueReadBuffer(d_cl_minir, CL_TRUE, 0, CLBLOCKSIZE_RED*sizeof(unsigned short), cl_minir);
			memtime = memtime + (std::clock() - clckstart);

			clckstart = std::clock();
			for (i = 0; i < CLBLOCKSIZE_RED*gpu_compute / CLLOCAL_RED; i++){
				if (cl_minchi[i] < chi2_sav){
					chi2_sav = cl_minchi[i];
					sfh_sav = cl_minsfh[i];
					ir_sav = cl_minir[i];
				}
				else if (cl_minchi[i] == chi2_sav && (cl_minsfh[i] * NMOD) + cl_minir[i] < (sfh_sav*NMOD) + ir_sav){
					chi2_sav = cl_minchi[i];
					sfh_sav = cl_minsfh[i];
					ir_sav = cl_minir[i];
				}
				cl_minchi[i] = INFINITY;
			}
			arrtime1 = arrtime1 + (std::clock() - clckstart);

			//Write Initialized array back, non-blocking since it's small and we have time...
			queue.enqueueWriteBuffer(d_cl_minchi, CL_FALSE, 0, CLBLOCKSIZE_RED*sizeof(double), cl_minchi);

			if (i_m != i_mpow2) { //Loop Remaining that doesn't fit nicely into the reducer by pow2. //Last Step
				clckstart = std::clock();
				queue.enqueueReadBuffer(d_cl_chi2, CL_TRUE, 0, i_m*sizeof(double), cl_chi2);
				memtime = memtime + (std::clock() - clckstart);

				clckstart = std::clock();
				for (i = i_mpow2; i < i_m; i++){
					if (cl_chi2[i] < chi2_sav){
						chi2_sav = cl_chi2[i];
						sfh_sav = cl_sfh[i];
						ir_sav = cl_ir[i];
					}
					else if (cl_chi2[i] == chi2_sav && (cl_sfh[i] * NMOD) + cl_ir[i] < (sfh_sav*NMOD) + ir_sav){
						chi2_sav = cl_chi2[i];
						sfh_sav = cl_sfh[i];
						ir_sav = cl_ir[i];
					}
				}
				arrtime1 = arrtime1 + (std::clock() - clckstart);
			}

//Reduce Histogram
			////Part1 Reduce pa histogram
			//kernel_sumidtorange.setArg(0, i_m);
			//int cl_groupsize = ceil(i_m / (double)(gpu_compute * 8)); //4574
			//int cl_threadsize = ceil(cl_groupsize / (double)CLLOCAL_RANGE);	  //4574/256=18 *256=4608 *10b<=48k Localsize
			//kernel_sumidtorange.setArg(1, cl_groupsize);
			//kernel_sumidtorange.setArg(2, cl_threadsize);
			//kernel_sumidtorange.setArg(3, 0);
			//kernel_sumidtorange.setArg(4, NBINMAX1);
			//kernel_sumidtorange.setArg(5, d_ibin_pa);
			//kernel_sumidtorange.setArg(8, cl_threadsize*CLLOCAL_RANGE * sizeof(unsigned short), NULL); //Local Scratch ushort
			//kernel_sumidtorange.setArg(9, cl_threadsize*CLLOCAL_RANGE * sizeof(double), NULL); //Local Scratch double

			//queue.enqueueNDRangeKernel(kernel_sumidtorange, cl::NullRange, globalSize_range, localSize_range,
			//	NULL, &event);

			//event.wait();

			//start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
			//end = event.getProfilingInfo<CL_PROFILING_COMMAND_END>();
			//cltimehisto1 = cltimehisto1 + (end - start);

			////Part2 Reduce pa histogram
			//kernel_sumrangetoarray.setArg(0, 0);
			//kernel_sumrangetoarray.setArg(1, NBINMAX1);
			//kernel_sumrangetoarray.setArg(4, d_pa);

			//queue.enqueueNDRangeKernel(kernel_sumrangetoarray, cl::NullRange, globalSize_range2, localSize_range2,
			//	NULL, &event);

			//event.wait();

			//start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
			//end = event.getProfilingInfo<CL_PROFILING_COMMAND_END>();
			//cltimehisto2 = cltimehisto2 + (end - start);

			//Manual Reduce HistoGram
			// Read processed model data back from device memory.
			clckstart = std::clock();
			queue.enqueueReadBuffer(d_cl_prob, CL_TRUE, 0, i_m*sizeof(double), cl_prob);
			queue.enqueueReadBuffer(d_ibin_pa, CL_TRUE, 0, i_m*sizeof(unsigned short), ibin_pa);
			queue.enqueueReadBuffer(d_ibin_psfr, CL_TRUE, 0, i_m*sizeof(unsigned short), ibin_psfr);
			queue.enqueueReadBuffer(d_ibin_pldust, CL_TRUE, 0, i_m*sizeof(unsigned short), ibin_pldust);
			queue.enqueueReadBuffer(d_ibin_pmdust, CL_TRUE, 0, i_m*sizeof(unsigned short), ibin_pmdust);
			memtime = memtime + (std::clock() - clckstart);

			clckstart = std::clock();
			// Sequential loop for cumulative shared values.
			for (i = 0; i<i_m; i++){
				sfh_hist[cl_sfh[i]] += cl_prob[i];
				ir_hist[cl_ir[i]] += cl_prob[i];
				pa[ibin_pa[i]] += cl_prob[i];
				psfr[ibin_psfr[i]] += cl_prob[i];
				pldust[ibin_pldust[i]] += cl_prob[i];
				pmd[ibin_pmdust[i]] += cl_prob[i];
			}
			arrtime1 = arrtime1 + (std::clock() - clckstart);

			if (i_sfh + i_sfhoffset >= n_sfh) {
				std::cout << "\r100% done... " << n_sfh << " opt. models - fit finished" << endl;
			}
			else if ((i_sfh + i_sfhoffset) * 100 / n_sfh > writePercentage){
				std::cout << "\r " << writePercentage << "% done... " << (n_sfh * writePercentage) / 100 << "/" << n_sfh << " opt. models" << endl;
				writePercentage += 25;
			}

		} //while (i_sfh<n_sfh)

		std::cout << "Time for kernel to execute             " << cltime / i_kernel * 1.e-9 << " * " << i_kernel << " = " << cltime * 1.e-9 << endl;
		std::cout << "Time for memory transfers              " << (memtime / (double)CLOCKS_PER_SEC) / i_kernel << " * " << i_kernel << " = " << (memtime / (double)CLOCKS_PER_SEC) << endl;
		std::cout << "Time for id array processing           " << (arrtime / (double)CLOCKS_PER_SEC) / i_kernel << " * " << i_kernel << " = " << (arrtime / (double)CLOCKS_PER_SEC) << endl;
		std::cout << "Time for df kernel processing          " << (arrtimedf / (double)CLOCKS_PER_SEC) / i_kernel << " * " << i_kernel << " = " << (arrtimedf / (double)CLOCKS_PER_SEC) << endl;
		std::cout << "Time for model array processing        " << (arrtime1 / (double)CLOCKS_PER_SEC) / i_kernel << " * " << i_kernel << " = " << (arrtime1 / (double)CLOCKS_PER_SEC) << endl;
		std::cout << "Time for pa rangeid to execute         " << cltimehisto1 / i_kernel * 1.e-9 << " * " << i_kernel << " = " << cltimehisto1 * 1.e-9 << endl;
		std::cout << "Time for pa rangesum kernel to execute " << cltimehisto2 / i_kernel * 1.e-9 << " * " << i_kernel << " = " << cltimehisto2 * 1.e-9 << endl;
		//queue.enqueueReadBuffer(d_pa, CL_TRUE, 0, NBINMAX1*sizeof(double), pa);
	}
	catch (cl::Error error){
		//CL_INVALID_ARG_INDEX
		cerr << "OpenCL error: " << error.what() << "(" << error.err() << ")" << endl;
		return EXIT_FAILURE;
	}

	//Expand SFH_HIST and IR_HIST
	for (i = 0; i < n_sfh; i++){
		psfh[i_fmu_sfh[i]] += sfh_hist[i];
		pmu[i_mu[i]] += sfh_hist[i];
		ptv[i_tauv[i]] += sfh_hist[i];
		ptvism[i_tvism[i]] += sfh_hist[i];
		pssfr[i_lssfr[i]] += sfh_hist[i];
	}
	for (i = 0; i < n_ir; i++){
		pir[i_fmu_ir[i]] += ir_hist[i];
		pism[i_fmu_ism[i]] += ir_hist[i];
		ptbg1[i_tbg1[i]] += ir_hist[i];
		ptbg2[i_tbg2[i]] += ir_hist[i];
		pxi1[i_xi1[i]] += ir_hist[i];
		pxi2[i_xi2[i]] += ir_hist[i];
		pxi3[i_xi3[i]] += ir_hist[i];
	}

	//Recompute chi2_opt, chi2_ir and a_sav for Best Fit (sfh_sav,ir_sav)
	for (k = 0; k < nfilt_sfh - nfilt_mix; k++){
		flux_mod[k] = flux_sfh[k][sfh_sav];
	}
	for (k = nfilt_sfh - nfilt_mix; k<nfilt_sfh; k++){
		flux_mod[k] = flux_sfh[k][sfh_sav] + ldust[sfh_sav] * flux_ir[k - nfilt_sfh + nfilt_mix][ir_sav];
	}
	for (k = nfilt_sfh; k<nfilt; k++){
		flux_mod[k] = ldust[sfh_sav] * flux_ir[k - nfilt_sfh + nfilt_mix][ir_sav];
	}
	for (k = 0; k<nfilt; k++){
		if (flux_obs[k] > 0) {
			num = num + (flux_mod[k] * flux_obs[k] * w[k]);
			den = den + (pow(flux_mod[k], 2)*w[k]);
		}
	}
	a_sav = num / den;
	for (k = 0; k<nfilt_sfh; k++){
		if (flux_obs[k] > 0){
			chi2_sav_opt = chi2_sav_opt + ((pow(flux_obs[k] - (a_sav * flux_mod[k]), 2)) * w[k]);
		}
	}
	if (chi2_sav_opt < 600){
		for (k = nfilt_sfh; k<nfilt; k++){
			if (flux_obs[k] > 0){
				chi2_sav_ir = chi2_sav_ir + ((pow(flux_obs[k] - (a_sav * flux_mod[k]), 2)) * w[k]);
			}
		}
	}

	std::cout << "      Number of random SFH models: " << n_sfh << endl;
	std::cout << "Number of IR dust emission models: " << n_ir << endl;
	std::cout << "                      Value of df: " << df << endl;
	std::cout << "           Total number of models: " << n_models << endl;
	std::cout << "                             ptot: " << ptot << endl;
	std::cout << "                     chi2_optical: " << chi2_sav_opt << endl;
	std::cout << "                    chi2_infrared: " << chi2_sav_ir << endl;

	// ---------------------------------------------------------------------------
	// Compute percentiles of the (normalized) likelihood distributions
	// ---------------------------------------------------------------------------
	for (i = 0; i<NBINMAX1; i++){
		psfh[i] = psfh[i] / ptot;
		pir[i] = pir[i] / ptot;
		pmu[i] = pmu[i] / ptot;
		ptv[i] = ptv[i] / ptot;
		ptvism[i] = ptvism[i] / ptot;
		psfr[i] = psfr[i] / ptot;
		pssfr[i] = pssfr[i] / ptot;
		pa[i] = pa[i] / ptot;
		pldust[i] = pldust[i] / ptot;
		pism[i] = pism[i] / ptot;
		ptbg1[i] = ptbg1[i] / ptot;
		ptbg2[i] = ptbg2[i] / ptot;
		pxi1[i] = pxi1[i] / ptot;
		pxi2[i] = pxi2[i] / ptot;
		pxi3[i] = pxi3[i] / ptot;
		pmd[i] = pmd[i] / ptot;
	}

	get_percentiles(nbin_fmu, fmu_hist, psfh, pct_fmu_sfh);
	get_percentiles(nbin_fmu, fmu_hist, pir, pct_fmu_ir);
	get_percentiles(nbin_mu, mu_hist, pmu, pct_mu);
	get_percentiles(nbin_tv, tv_hist, ptv, pct_tv);
	get_percentiles(nbin_tv, tv_hist, ptvism, pct_tvism);
	get_percentiles(nbin_ssfr, ssfr_hist, pssfr, pct_ssfr);
	get_percentiles(nbin_sfr, sfr_hist, psfr, pct_sfr);
	get_percentiles(nbin_a, a_hist, pa, pct_mstr);
	get_percentiles(nbin_ld, ld_hist, pldust, pct_ld);
	get_percentiles(nbin_fmu_ism, fmuism_hist, pism, pct_ism);
	get_percentiles(nbin_tbg1, tbg1_hist, ptbg1, pct_tbg1);
	get_percentiles(nbin_tbg2, tbg2_hist, ptbg2, pct_tbg2);
	get_percentiles(nbin_xi, xi_hist, pxi1, pct_xi1);
	get_percentiles(nbin_xi, xi_hist, pxi2, pct_xi2);
	get_percentiles(nbin_xi, xi_hist, pxi3, pct_xi3);
	get_percentiles(nbin_md, md_hist, pmd, pct_md);

	for (i = 0; i<100; i++){
		psfh2[i] = 0;
		pir2[i] = 0;
		pmu2[i] = 0;
		ptv2[i] = 0;
		ptvism2[i] = 0;
		pssfr2[i] = 0;
		psfr2[i] = 0;
		pa2[i] = 0;
		pldust2[i] = 0;
		pism2[i] = 0;
		ptbg1_2[i] = 0;
		ptbg2_2[i] = 0;
		pxi1_2[i] = 0;
		pxi2_2[i] = 0;
		pxi3_2[i] = 0;
		pmd_2[i] = 0;
	}

	//New histogram parameters
	dfmu = 0.05f;
	fmu_min = 0;
	fmu_max = 1;
	dfmu_ism = 0.05f;
	fmuism_min = 0;
	fmuism_max = 1;
	dtv = 0.125f;
	dtvism = 0.075f;
	tv_min = 0;
	tv_max = 6;
	dssfr = 0.10f;
	ssfr_min = -13.0f;
	ssfr_max = -6.0f;
	dsfr = 0.10f;

	sfr_min = -8;
	sfr_max = 3;
	da = 0.10f;

	a_min = 2.0f;
	a_max = 13.0f;
	dtbg = 1;
	tbg2_min = 15;
	tbg2_max = 25;
	tbg1_min = 30;
	tbg1_max = 60;
	dxi = 0.05f;
	dmd = 0.10f;

	md_min = -2;
	md_max = 9;

	degrade_hist(dfmu, fmu_min, fmu_max, nbin_fmu, &nbin2_fmu, fmu_hist, fmu2_hist, psfh, psfh2);
	degrade_hist(dfmu, fmu_min, fmu_max, nbin_fmu, &nbin2_fmu, fmu_hist, fmu2_hist, pir, pir2);
	degrade_hist(dfmu, fmu_min, fmu_max, nbin_mu, &nbin2_mu, mu_hist, mu2_hist, pmu, pmu2);
	degrade_hist(dtv, tv_min, tv_max, nbin_tv, &nbin2_tv, tv_hist, tv2_hist, ptv, ptv2);
	degrade_hist(dtvism, tv_min, tv_max, nbin_tv, &nbin2_tvism, tv_hist, tvism2_hist, ptvism, ptvism2);
	degrade_hist(dssfr, ssfr_min, ssfr_max, nbin_ssfr, &nbin2_ssfr, ssfr_hist, ssfr2_hist, pssfr, pssfr2);
	degrade_hist(dsfr, sfr_min, sfr_max, nbin_sfr, &nbin2_sfr, sfr_hist, sfr2_hist, psfr, psfr2);
	degrade_hist(da, a_min, a_max, nbin_a, &nbin2_a, a_hist, a2_hist, pa, pa2);
	degrade_hist(da, a_min, a_max, nbin_ld, &nbin2_ld, ld_hist, ld2_hist, pldust, pldust2);
	degrade_hist(dfmu_ism, fmuism_min, fmuism_max, nbin_fmu_ism, &nbin2_fmu_ism, fmuism_hist, fmuism2_hist, pism, pism2);
	degrade_hist(dtbg, tbg1_min, tbg1_max, nbin_tbg1, &nbin2_tbg1, tbg1_hist, tbg1_2_hist, ptbg1, ptbg1_2);
	degrade_hist(dtbg, tbg2_min, tbg2_max, nbin_tbg2, &nbin2_tbg2, tbg2_hist, tbg2_2_hist, ptbg2, ptbg2_2);
	degrade_hist(dxi, fmu_min, fmu_max, nbin_xi, &nbin2_xi, xi_hist, xi2_hist, pxi1, pxi1_2);
	degrade_hist(dxi, fmu_min, fmu_max, nbin_xi, &nbin2_xi, xi_hist, xi2_hist, pxi2, pxi2_2);
	degrade_hist(dxi, fmu_min, fmu_max, nbin_xi, &nbin2_xi, xi_hist, xi2_hist, pxi3, pxi3_2);
	degrade_hist(dmd, md_min, md_max, nbin_md, &nbin2_md, md_hist, md2_hist, pmd, pmd_2);

	//---------------------------------------------------------------------------
	// Store fit results in .fit output file
	//---------------------------------------------------------------------------
	// Buffer we will use for massaging numbers in FORTRAN format.
	char dbuf[20];
	std::fprintf(fitfp, "# OBSERVED FLUXES (and errors):\n");
	std::fprintf(fitfp, " #   ");
	for (k = 0; k<nfilt; k++){
		if (k != nfilt - 1){
			std::fprintf(fitfp, "%-12s", filt_name[k]);
		}
		else{
			std::fprintf(fitfp, "%s", filt_name[k]);
		}
	}
	std::fprintf(fitfp, "\n");

	for (k = 0; k<nfilt; k++){
		std::fprintf(fitfp, "%12.3E", flux_obs[k]);
	}
	std::fprintf(fitfp, "\n");
	for (k = 0; k<nfilt; k++){
		std::fprintf(fitfp, "%12.3E", sigma[k]);
	}
	std::fprintf(fitfp, "\n");
	std::fprintf(fitfp, "#\n");

	std::fprintf(fitfp, "# ... Results of fitting the fluxes to the model.....\n");

	std::fprintf(fitfp, "#\n");
	std::fprintf(fitfp, "# BEST FIT MODEL: (i_sfh, i_ir, chi2, redshift)\n");

	// Adding 1 to ir_sav to get total number
	std::fprintf(fitfp, "%10i%10i%10.3f%12.6f\n", indx[sfh_sav], ir_sav + 1, chi2_sav / n_flux, redshift);

	std::fprintf(fitfp, "#.fmu(SFH)...fmu(IR)........mu......tauv");;
	std::fprintf(fitfp, "........sSFR..........M*.......Ldust");
	std::fprintf(fitfp, "......T_W^BC.....T_C^ISM....xi_C^tot");
	std::fprintf(fitfp, "..xi_PAH^tot..xi_MIR^tot....xi_W^tot.....tvism");
	std::fprintf(fitfp, ".......Mdust.....SFR");
	std::fprintf(fitfp, "\n");

	// TODO - Reimplement this solution to get around IEEE round-to-nearest-even problem.
	std::fprintf(fitfp, "%10.3f%10.3f%10.3f%10.3f",
		round_nup(fmu_sfh[sfh_sav], 3),
		round_nup(fmu_ir[ir_sav], 3),
		round_nup(mu[sfh_sav], 3),
		round_nup(tauv[sfh_sav], 3)
		);
	std::fprintf(fitfp, "%12.3E%12.3E%12.3E",
		ssfr[sfh_sav],
		a_sav,
		ldust[sfh_sav] * a_sav
		);
	std::fprintf(fitfp, "%10.1f%10.1f%10.3f%10.3f%10.3f%10.3f%10.3f",
		round_nup(tbg1[ir_sav], 1),
		round_nup(tbg2[ir_sav], 1),
		round_nup(fmu_ism[ir_sav], 3),
		round_nup(xi1[ir_sav], 3),
		round_nup(xi2[ir_sav], 3),
		round_nup(xi3[ir_sav], 3),
		round_nup(tvism[sfh_sav], 3)
		);
	std::fprintf(fitfp, "%12.3E%12.3E",
		mdust[ir_sav] * a_sav*ldust[sfh_sav],
		ssfr[sfh_sav] * a_sav
		);
	std::fprintf(fitfp, "\n");

	std::fprintf(fitfp, " #   ");
	for (k = 0; k<nfilt; k++){
		if (k != nfilt - 1){
			std::fprintf(fitfp, "%-12s", filt_name[k]);
		}
		else{
			std::fprintf(fitfp, "%s", filt_name[k]);
		}
	}
	std::fprintf(fitfp, "\n");

	for (k = 0; k<nfilt_sfh - nfilt_mix; k++){
		std::fprintf(fitfp, "%12.3E", a_sav*flux_sfh[k][sfh_sav]);
	}
	for (k = nfilt_sfh - nfilt_mix; k<nfilt_sfh; k++){
		std::fprintf(fitfp, "%12.3E", a_sav*flux_sfh[k][sfh_sav] + flux_ir[k - nfilt_sfh + nfilt_mix][ir_sav] * ldust[sfh_sav]);
	}
	for (k = nfilt_sfh; k<nfilt; k++){
		std::fprintf(fitfp, "%12.3E", a_sav*flux_ir[k - nfilt_sfh + nfilt_mix][ir_sav] * ldust[sfh_sav]);
	}
	std::fprintf(fitfp, "\n");

	std::fprintf(fitfp, "#\n");
	std::fprintf(fitfp, "# MARGINAL PDF HISTOGRAMS FOR EACH PARAMETER......\n");

	std::fprintf(fitfp, "# ... f_mu (SFH) ...\n");
	for (ibin = 0; ibin<nbin2_fmu; ibin++){
		std::fprintf(fitfp, "%10.4f", fmu2_hist[ibin]);
		print_fexp3(fitfp, psfh2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_fmu_sfh[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(psfh2, fmu2_hist, nbin2_fmu);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, fmu2_hist[0], fmu2_hist[nbin2_fmu - 1]);
	std::fprintf(fitfp, "%10.4f\n", fmu2_hist[1] - fmu2_hist[0]);

	std::fprintf(fitfp, "# ... f_mu (IR) ...\n");
	for (ibin = 0; ibin<nbin2_fmu; ibin++){
		std::fprintf(fitfp, "%10.4f", fmu2_hist[ibin]);
		print_fexp3(fitfp, pir2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_fmu_ir[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pir2, fmu2_hist, nbin2_fmu);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, fmu2_hist[0], fmu2_hist[nbin2_fmu - 1]);
	std::fprintf(fitfp, "%10.4f\n", fmu2_hist[1] - fmu2_hist[0]);

	std::fprintf(fitfp, "# ... mu parameter ...\n");
	for (ibin = 0; ibin<nbin2_mu; ibin++){
		std::fprintf(fitfp, "%10.4f", mu2_hist[ibin]);
		print_fexp3(fitfp, pmu2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_mu[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pmu2, mu2_hist, nbin2_mu);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, mu2_hist[0], mu2_hist[nbin2_mu - 1]);
	std::fprintf(fitfp, "%10.4f\n", mu2_hist[1] - mu2_hist[0]);

	std::fprintf(fitfp, "# ... tau_V ...\n");
	for (ibin = 0; ibin<nbin2_tv; ibin++){
		std::fprintf(fitfp, "%10.4f", tv2_hist[ibin]);
		print_fexp3(fitfp, ptv2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_tv[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(ptv2, tv2_hist, nbin2_tv);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, tv2_hist[0], tv2_hist[nbin2_tv - 1]);
	std::fprintf(fitfp, "%10.4f\n", tv2_hist[1] - tv2_hist[0]);

	std::fprintf(fitfp, "# ... sSFR_0.1Gyr ...\n");
	for (ibin = 0; ibin<nbin2_ssfr; ibin++){
		print_fexp3(fitfp, ssfr2_hist[ibin]);
		print_fexp3(fitfp, pssfr2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		print_fexp3(fitfp, pct_ssfr[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pssfr2, ssfr2_hist, nbin2_ssfr);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, ssfr2_hist[0], ssfr2_hist[nbin2_ssfr - 1]);
	std::fprintf(fitfp, "%10.4f\n", ssfr2_hist[1] - ssfr2_hist[0]);

	std::fprintf(fitfp, "# ... M(stars) ...\n");
	for (ibin = 0; ibin<nbin2_a; ibin++){
		print_fexp3(fitfp, a2_hist[ibin]);
		print_fexp3(fitfp, pa2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		print_fexp3(fitfp, pct_mstr[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pa2, a2_hist, nbin2_a);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, a2_hist[0], a2_hist[nbin2_a - 1]);
	std::fprintf(fitfp, "%10.4f\n", a2_hist[1] - a2_hist[0]);

	std::fprintf(fitfp, "# ... Ldust ...\n");
	for (ibin = 0; ibin<nbin2_ld; ibin++){
		print_fexp3(fitfp, ld2_hist[ibin]);
		print_fexp3(fitfp, pldust2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		print_fexp3(fitfp, pct_ld[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pldust2, ld2_hist, nbin2_ld);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, ld2_hist[0], ld2_hist[nbin2_ld - 1]);
	std::fprintf(fitfp, "%10.4f\n", ld2_hist[1] - ld2_hist[0]);

	std::fprintf(fitfp, "# ... T_C^ISM ...\n");
	for (ibin = 0; ibin<nbin2_tbg2; ibin++){
		std::fprintf(fitfp, "%10.4f", tbg2_2_hist[ibin]);
		print_fexp3(fitfp, ptbg2_2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_tbg2[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(ptbg2_2, tbg2_2_hist, nbin2_tbg2);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, tbg2_2_hist[0], tbg2_2_hist[nbin2_tbg2 - 1]);
	std::fprintf(fitfp, "%10.4f\n", tbg2_2_hist[1] - tbg2_2_hist[0]);

	std::fprintf(fitfp, "# ... T_W^BC ...\n");
	for (ibin = 0; ibin<nbin2_tbg1; ibin++){
		std::fprintf(fitfp, "%10.4f", tbg1_2_hist[ibin]);
		print_fexp3(fitfp, ptbg1_2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_tbg1[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(ptbg1_2, tbg1_2_hist, nbin2_tbg1);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, tbg1_2_hist[0], tbg1_2_hist[nbin2_tbg1 - 1]);
	std::fprintf(fitfp, "%10.4f\n", tbg1_2_hist[1] - tbg1_2_hist[0]);

	std::fprintf(fitfp, "# ... xi_C^tot ...\n");
	for (ibin = 0; ibin<nbin2_fmu_ism; ibin++){
		std::fprintf(fitfp, "%10.4f", fmuism2_hist[ibin]);
		print_fexp3(fitfp, pism2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_ism[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pism2, fmuism2_hist, nbin2_fmu_ism);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, fmuism2_hist[0], fmuism2_hist[nbin2_fmu_ism - 1]);
	std::fprintf(fitfp, "%10.4f\n", fmuism2_hist[1] - fmuism2_hist[0]);

	std::fprintf(fitfp, "# ... xi_PAH^tot ...\n");
	for (ibin = 0; ibin<nbin2_xi; ibin++){
		std::fprintf(fitfp, "%10.4f", xi2_hist[ibin]);
		print_fexp3(fitfp, pxi1_2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_xi1[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pxi1_2, xi2_hist, nbin2_xi);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, xi2_hist[0], xi2_hist[nbin2_xi - 1]);
	std::fprintf(fitfp, "%10.4f\n", xi2_hist[1] - xi2_hist[0]);

	std::fprintf(fitfp, "# ... xi_MIR^tot ...\n");
	for (ibin = 0; ibin<nbin2_xi; ibin++){
		std::fprintf(fitfp, "%10.4f", xi2_hist[ibin]);
		print_fexp3(fitfp, pxi2_2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_xi2[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pxi2_2, xi2_hist, nbin2_xi);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, xi2_hist[0], xi2_hist[nbin2_xi - 1]);
	std::fprintf(fitfp, "%10.4f\n", xi2_hist[1] - xi2_hist[0]);

	std::fprintf(fitfp, "# ... xi_W^tot ...\n");
	for (ibin = 0; ibin<nbin2_xi; ibin++){
		std::fprintf(fitfp, "%10.4f", xi2_hist[ibin]);
		print_fexp3(fitfp, pxi3_2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_xi3[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(pxi3_2, xi2_hist, nbin2_xi);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, xi2_hist[0], xi2_hist[nbin2_xi - 1]);
	std::fprintf(fitfp, "%10.4f\n", xi2_hist[1] - xi2_hist[0]);

	std::fprintf(fitfp, "# ... tau_V^ISM...\n");
	for (ibin = 0; ibin<nbin2_tvism; ibin++){
		std::fprintf(fitfp, "%10.4f", tvism2_hist[ibin]);
		print_fexp3(fitfp, ptvism2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_tvism[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(ptvism2, tvism2_hist, nbin2_tvism);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, tvism2_hist[0], tvism2_hist[nbin2_tvism - 1]);
	std::fprintf(fitfp, "%10.4f\n", tvism2_hist[1] - tvism2_hist[0]);

	std::fprintf(fitfp, "# ... M(dust)...\n");
	for (ibin = 0; ibin<nbin2_md; ibin++){
		std::fprintf(fitfp, "%10.4f", md2_hist[ibin]);
		print_fexp3(fitfp, pmd_2[ibin]);
		std::fprintf(fitfp, "\n");
	}

	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_md[k]);
	}
	std::fprintf(fitfp, "\n");
	hpbv = get_hpbv(pmd_2, md2_hist, nbin2_md);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, md2_hist[0], md2_hist[nbin2_md - 1]);
	std::fprintf(fitfp, "%10.4f\n", md2_hist[1] - md2_hist[0]);

	std::fprintf(fitfp, "# ... SFR_0.1Gyr ...\n");
	for (ibin = 0; ibin<nbin2_sfr; ibin++){
		print_fexp3(fitfp, sfr2_hist[ibin]);
		print_fexp3(fitfp, psfr2[ibin]);
		std::fprintf(fitfp, "\n");
	}
	std::fprintf(fitfp, "#....percentiles of the PDF......\n");
	for (k = 0; k<5; k++){
		std::fprintf(fitfp, "%8.3f", pct_sfr[k]);
	}
	std::fprintf(fitfp, "\n");

	hpbv = get_hpbv(psfr2, sfr2_hist, nbin2_sfr);
	std::fprintf(fitfp, "# theSkyNet2\n");
	std::fprintf(fitfp, "%10.4f%10.4f%10.4f", hpbv, sfr2_hist[0], sfr2_hist[nbin2_sfr - 1]);
	std::fprintf(fitfp, "%10.4f\n", sfr2_hist[1] - sfr2_hist[0]);

	std::fprintf(fitfp, " #...theSkyNet parameters of this model\n");
	std::fprintf(fitfp, "%15i%15i", indx[sfh_sav], ir_sav + 1);

	// Yuck! Do the FORTRAN formatting requirement.
	std::sprintf(dbuf, "%.5E", a_sav);
	get_fsci(dbuf);
	std::fprintf(fitfp, "%20s", dbuf);
	std::sprintf(dbuf, "%.3E", fmu_sfh[sfh_sav]);
	get_fsci(dbuf);
	std::fprintf(fitfp, "%20s", dbuf);
	std::sprintf(dbuf, "%.1E", redshift);
	get_fsci(dbuf);
	std::fprintf(fitfp, "%10s\n", dbuf);
}

//Find the bin with the highest probability value
double get_hpbv(double hist1[], double hist2[], int nbin){
	double max_pr = 0;
	double hpbv = 0;
	for (int ibin = 0; ibin<nbin; ibin++){
		if (ibin == 0){
			max_pr = hist1[ibin];
			hpbv = hist2[ibin];
		}
		else if (hist1[ibin] > max_pr){
			max_pr = hist1[ibin];
			hpbv = hist2[ibin];
		}
	}
	return hpbv;
}

// ---------------------------------------------------------------------------
// Degrades the resolution of the histograms containing the likelihood
// distribution of the parameters: to facilitate storage & visualization
// ---------------------------------------------------------------------------
//  delta : bin width
//  min   : minumum value
//  max   : maximum value
//  nbin1 : number of bins of high-res histogram
//  nbin2 : number of bins of output low-res histogram
//  hist1 : input high-res histogram x-axis
//  hist2 : output low-res histogram x-axis
//  prob1 : input histogram values
//  prob2 : output histogram values
void degrade_hist(double delta, double min, double max, int nbin1, int * nbin2, double hist1[], double hist2[], double prob1[], double prob2[]){
	int i = 0;
	int ibin = 0;
	double max2 = 0;
	double aux;

	max2 = max + (delta / 2);

	get_histgrid(delta, min, max2, nbin2, hist2);
	for (i = 0; i<nbin1; i++){
		aux = ((hist1[i] - min) / (max - min))*(*nbin2);
		ibin = (int)(aux);
		prob2[ibin] = prob2[ibin] + prob1[i];
	}
}

void degrade_histp(double delta, double min, double max, int nbin1, int * nbin2, double hist1[], double hist2[], double prob1[], double prob2[]){
	int i = 0;
	int ibin = 0;
	double max2 = 0;
	double aux;

	max2 = max + (delta / 2);

	get_histgrid(delta, min, max2, nbin2, hist2);
	for (i = 0; i<nbin1; i++){
		aux = ((hist1[i] - min) / (max - min))*(*nbin2);
		ibin = (int)(aux);
		prob2[ibin] = prob2[ibin] + prob1[i];
	}
}

//---------------------------------------------------------------------------
// Build histogram grid (i.e. vector of bins)
//---------------------------------------------------------------------------
// dv : bin width
// vmin : minumum value
// vmax : maximum value
// nbin : number of bins
// vout : output vector of bins
void get_histgrid(double dv, double vmin, double vmax, int* nbin, double vout[]){
	double x1, x2;
	(*nbin) = 0;
	x1 = vmin;
	x2 = vmin + dv;
	while (x2 <= vmax){
		vout[(*nbin)] = 0.5*(x1 + x2);
		x1 = x1 + dv;
		x2 = x2 + dv;
		(*nbin)++;
	}
}

// ---------------------------------------------------------------------------
// Calculates percentiles of the probability distibution
// for a given parameter: 2.5, 16, 50 (median), 84, 97.5
// 1. Sort the parameter + the probability array
// 2. Find the parameter value M for which:
//    P (x < M) = P (x > M) = percentiles
// ---------------------------------------------------------------------------
//           n : number of points (bins)
//         par : parameter value (vector of bins)
// probability : vector with prob of each parameter value (or bin)
//  percentile : vector containing 5 percentiles described above
void get_percentiles(int n, double par[], double probability[], double percentile[]){
	int i = 0;
	double pless = 0;
	int n_perc[5];
	double limit[5] = { 0.025, 0.16, 0.50, 0.84, 0.975 };
	sort2(par, probability, 0, n - 1);

	for (i = 0; i<5; i++){
		n_perc[i] = 0;
		pless = 0;
		while (pless <= limit[i]){
			pless = pless + probability[n_perc[i]];
			n_perc[i]++;
		}
		n_perc[i] = n_perc[i] - 1;
		percentile[i] = par[n_perc[i]];
	}
}

void get_percentilesp(int n, double par[], double probability[], double percentile[]){
	int i = 0;
	double pless = 0;
	int n_perc[5];
	double limit[5] = { 0.025, 0.16, 0.50, 0.84, 0.975 };
	sort2(par, probability, 0, n - 1);

	for (i = 0; i<5; i++){
		cout << "i " << i << endl;
		n_perc[i] = 0;
		pless = 0;
		while (pless <= limit[i]){
			//cout << " pless " << pless ;
			//cout << " n perc " << n_perc[i];
			pless = pless + probability[n_perc[i]];
			n_perc[i]++;
		}
		n_perc[i] = n_perc[i] - 1;
		percentile[i] = par[n_perc[i]];
		cout << "perc " << percentile[i] << endl;
		cout << "n perc " << n_perc[i] << endl;
	}
}

// ---------------------------------------------------------------------------
// Sorts an array arr(1:n) into ascending order using Quicksort
// while making the corresponding rearrangement of the array brr(1:n)
void sort2(double arr1[], double arr2[], int left, int right) {
	int i = left;
	int j = right;
	double temp1, temp2;
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
		sort2(arr1, arr2, left, j);
	if (i < right)
		sort2(arr1, arr2, i, right);
}

// ---------------------------------------------------------------------------
// Computes luminosity distance corresponding to a redshift z.
// Uses Mattig formulae for qo both 0 and non 0
// Revised January 1991 to implement cosmolgical constant
// Ho in km/sec/Mpc, DL is in Mpc
double get_dl(double h, double q, double z){
	double dl, d1, d2;
	double aa, bb, epsr, s, s0;
	double dd1, dd2;
	bool success;
	int npts;

	dl = 0;
	s = 0;

	if (z <= 0){
		return (1.0e-5f);
	}

	if (q == 0){
		dl = ((3.0e5f * z)*(1 + (z / 2))) / h;
	}
	else if (q > 0){
		d1 = (q*z) + ((q - 1)*(sqrt(1 + ((2 * q)*z)) - 1));
		d2 = ((h*q)*q) / 3.0e5f;
		dl = d1 / d2;
	}
	else if (q < 0){
		omega0 = (2 * (q + 1)) / 3;
		aa = 1;
		bb = 1 + z;
		success = false;
		s0 = 1.0e-10f;
		npts = 0;
		do{
			npts++;
			get_midpnt(get_funl, aa, bb, &s, npts);
			epsr = fabs(s - s0) / s0;
			if (epsr < 1.0e-4f){
				success = true;
			}
			else {
				s0 = s;
			}
		} while (!success);
		dd1 = s;
		dd2 = (3.0e5f * (1 + z)) / (h*sqrt(omega0));
		dl = dd1*dd2;
	}
	return dl;
}
// ---------------------------------------------------------------------------
// For non-zero cosmological constant
double get_funl(double x){
	double omegainv;
	omegainv = 1 / omega0;
	return (1 / sqrt(((x*x*x) + omegainv) - 1));
}

void get_midpnt(double(*func)(double), double a, double b, double* s, double n){
	int it, j;
	double ddel, del, sum, tnm, x;
	if (n == 1){
		(*s) = (b - a)*((*func)(0.5f*(a + b)));
	}
	else{
		it = pow(3, (n - 2));
		tnm = it;
		del = (b - a) / (3 * tnm);
		ddel = del + del;
		x = a + 0.5f*del;
		sum = 0;
		for (j = 0; j < it; j++){
			sum = sum + ((*func)(x));
			x = x + ddel;
			sum = sum + ((*func)(x));
			x = x + del;
		}
		(*s) = ((*s) + (b - a)*sum / tnm) / 3;
	}
}

// Returns cosmological constant = cosmol_c and parameter q
// 
// Omega is entered by the user
// omega=1.-omega_lambda
double get_cosmol_c(double h, double omega, double omega_lambda, double* q){
	if (omega_lambda == 0){
		*q = omega / 2;
	}
	else{
		*q = (3 * omega / 2) - 1;
	}
	return (omega_lambda / (3 * h*h));
}
// Some C helper functions

// Modifies string with scientific notation double to have 3 0s in exponent.
void get_fexp3(char dstr[]){
	int orig_len = (int)strlen(dstr);
	int i = orig_len;
	while (i >= 0 && !(dstr[i] == '+' || dstr[i] == '-')){
		i--;
	}
	i++;
	int base_end_pos = i;

	char * exp_str = new char[orig_len - base_end_pos + 1];

	char c = dstr[i];
	int j = 0;
	while (c != '\0'){
		c = dstr[i++];
		exp_str[j] = c;
		j++;
	}
	exp_str[j] = '\0';

	int exp = atoi(exp_str);
	std::sprintf(exp_str, "%03d", exp);

	for (int k = 0; k<(int)strlen(exp_str); k++){
		dstr[base_end_pos++] = exp_str[k];
	}

	dstr[i] = '\0';
	delete[] exp_str;
}

void print_fexp3(FILE * fitfp, double histvalue) {
	static char dstr[20];
	static double dvalue;
	int orig_len, i, base_end_pos;
	std::sprintf(dstr, "%.3E", histvalue);

	orig_len = (int)strlen(dstr);
	i = orig_len;
	while (i >= 0 && !(dstr[i] == '+' || dstr[i] == '-')){
		i--;
	}
	i++;
	base_end_pos = i;

	char * exp_str = new char[orig_len - base_end_pos + 1];

	char c = dstr[i];
	int j = 0;
	while (c != '\0'){
		c = dstr[i++];
		exp_str[j] = c;
		j++;
	}
	exp_str[j] = '\0';

	int exp = atoi(exp_str);
	std::sprintf(exp_str, "%03d", exp);

	for (int k = 0; k<(int)strlen(exp_str); k++){
		dstr[base_end_pos++] = exp_str[k];
	}

	dstr[i] = '\0';
	delete[] exp_str;

	std::fprintf(fitfp, "%12s", dstr);
}

// Very ugly function that modifies scientific notation string into FORTRAN style preceding 0.
void get_fsci(char dstr[]){
	int orig_len = (int)strlen(dstr);
	double orig_val;
	sscanf(dstr, "%lf", &orig_val);
	if (orig_val == 0){
		return;
	}
	int i = orig_len;
	while (i >= 0 && !(dstr[i] == '+' || dstr[i] == '-')){
		i--;
	}
	// Set the position where our base ends and sign starts.
	int base_end_pos = i;

	char * exp_str = new char[orig_len - base_end_pos + 1];

	char c = dstr[i];
	int j = 0;

	// Copy exponent into new char array.
	while (c != '\0'){
		c = dstr[i++];
		exp_str[j] = c;
		j++;
	}
	exp_str[j] = '\0';

	// This is our new exponent.
	int exp;
	if (orig_val != 0){
		exp = atoi(exp_str) + 1;
	}
	else {
		exp = atoi(exp_str);
	}

	// Always + if the exponent is 0.
	if (exp == 0){
		exp_str[0] = '+';
	}

	if (exp_str[0] == '+'){
		std::sprintf(exp_str, "+%02d", abs(exp));
	}
	else if (exp_str[0] == '-'){
		std::sprintf(exp_str, "-%02d", abs(exp));
	}

	char * old_dstr = new char[orig_len];
	std::strcpy(old_dstr, dstr);
	dstr[0] = '0';
	dstr[1] = '.';
	j = 2;

	for (int k = 0; k<base_end_pos; k++){
		if (old_dstr[k] != '.'){
			dstr[j++] = old_dstr[k];
		}
	}

	for (int k = 0; k<(int)strlen(exp_str); k++){
		dstr[j++] = exp_str[k];
	}
	dstr[j] = '\0';

	delete[] exp_str;
	delete[] old_dstr;
}

// Rounds up depending on double FP representability.
double round_nup(double n, int p){
	char buf1[20], buf2[20];
	// Simulate a print of full mantissa to check how to comes out.
	_snprintf(buf1, 20, "%.20f", n);
	_snprintf(buf2, 20, "%.*f%020d", p + 2, n, 0);
	// IEEE dictates n will get rounded to nearest even if tie and FP is EXACTLY representable.
	// We must override this behavior.
	if (strcmp(buf1, buf2) == 0){
		int m = pow(10, p);
		return round(n*m) / m;
	}
	return n;
}

Parser::Parser()
{
	ignoring = -1;
}

Parser::Parser(string file)
{
	input.open(file);
	ignoring = -1;

	//if( !input.is_open() )
	// throw ExcFailed( L"[Parser::Parser] Could not open file " + file + L"\n" );
}

void Parser::Ignore(const std::string& start, const std::string& end)
{
	excludeDelims.push_back(start);
	includeDelims.push_back(end);
}

void Parser::Rewind(void)
{
	input.seekg(0, ios::beg);
	input.clear();

	ignoring = -1;
	line.clear();
}

void Parser::Next(void)
{
	getline(input, line);

	if (!input.good())
		return;

	if (line.empty())
	{
		Next();
		return;
	}

	TrimLine(line);
	if (line.empty())
	{
		Next();
		return;
	}
}

void Parser::GetLine(std::string& _line)
{
	_line = line;
}

void Parser::GetTokens(std::vector<std::string>& tokens)
{
	tokens.clear();
	string buff;

	size_t from = 0;
	while (from < line.length())
	{
		GetNextToken(buff, from);
		tokens.push_back(buff);
	}
}

bool Parser::Good(void)
{
	return input.good();
}

void Parser::TrimLine(string& line)
{
	if (ignoring != -1)
	{
		size_t incPos = line.find(includeDelims[ignoring]);
		if (incPos != string::npos)
		{
			line = line.substr(incPos, line.length());
			ignoring = -1;
			TrimLine(line);
		}
		else
			line.clear();
	}
	else
	{
		for (size_t i = 0; i < excludeDelims.size(); i++)
		{
			size_t excPos = line.find(excludeDelims[i]);
			if (excPos != string::npos)
			{
				string tail = line.substr(excPos, line.length());
				line = line.substr(0, excPos);

				// If the includeDelim is the end of the line just return the head.
				if (includeDelims[i] == "\n")
					return;

				ignoring = i;
				TrimLine(tail);
				line += tail;
				return;
			}
		}
	}
}

void Parser::GetNextToken(std::string& container, size_t& from)
{
	size_t to = from;
	while (from != line.length() && (line[from] == ' ' || line[from] == '\t' || line[from] == '\r'))
		from++;

	to = from + 1;
	while (to != line.length() && line[to] != ' ' && line[to] != '\t' && line[to] != '\r')
		to++;

	container = line.substr(from, to - from);

	from = to;
}

