c     ===========================================================================
      PROGRAM FIT_SED
c     ---------------------------------------------------------------------------
c     Authors :   E. da Cunha & S. Charlot
c     Latest revision :   Sep. 16th, 2010
c     ---------------------------------------------------------------------------
c     Model & Method descibed in detail in:
c     da Cunha, Charlot & Elbaz, 2008, MNRAS 388, 1595
c     ---------------------------------------------------------------------------
c     Compares model fluxes with observed fluxes from the ultraviolet to the
c     far-infrared by computing the chi^2 goodness-of-fit of each model.
c     The probability of each model is exp(-1/2 chi^2)
c     The code also builds the likelihood distribution of each parameter
c
c     INPUTS:
c     - filter file - define USER_FILTERS in .galsbit_tcshrc
c     - file with redshifts & observed fluxes of the
c     galaxies - define USER_OBS in .magphys_tcshrc
c     - file with redshifts at which libraries
c     were computed "zlibs.dat"
c     - .lbr files generated with get_optic_colors.f
c     & get_infrared_colors.f
c     - number of the galaxy to fit: i_gal
c
c     OUTPUTS: - "name".fit file containing:
c     -- observed fluxes
c     -- mininum chi2
c     -- best-fit model parameters & fluxes
c     -- likelihood distribution of each parameter
c     -- 2.5th, 16th, 50th, 84th, 97.5th percentile
c     of each parameter
c     - "name".sed file containing the best-fit SED
c     ===========================================================================


c     ===========================================================================
c     Author : Kevin Vinsen
c	  Date : 29th May 2012
c     ---------------------------------------------------------------------------
c     Added minor changes to allow the code to run from the command line and not
c     to perform the normalisation against the models. Instead it writes the
c     parameters required to normalise it later.
c     The skyNet project is a citizen science project and we cannot expect the
c     general public to download the 3 large .bin files
c     ===========================================================================

      implicit none
      integer isave,i,j,k,i_gal,io,largo
      integer nmax,galmax,nmod
      parameter(nmax=50,galmax=5000) !nmax: maxium number of photometric points/filters
      integer n_obs,n_models,ibin  !galmax: maximum number of galaxies in one input file
      integer kfilt_sfh(nmax),kfilt_ir(nmax),nfilt_sfh,nfilt_ir,nfilt_mix
      integer nprop_sfh,nprop_ir
      integer n_sfh,n_ir,i_ir,i_sfh,ir_sav,sfh_sav
      integer nfilt,filt_id(nmax),fit(nmax),ifilt
      parameter(nmod=50001,nprop_sfh=24,nprop_ir=8)
      character*12 filt_name(nmax)
      character*100 outfile1,outfile2
      character*500 filter_header
      character*30 gal_name(galmax),aux_name
      character*6 numz
      character optlib*34,irlib*26
      character filters*80,obs*80
c     redshift libs
      integer nz,nzmax
      parameter(nzmax=5000)
      real*8 zlib(nzmax),diffz(nzmax)
c     observations, filters, etc.
      real*8 w(galmax,nmax),redshift(galmax),dist(galmax)
      real*8 flux_obs(galmax,nmax),sigma(galmax,nmax),aux
      real*8 flux_sfh(nmod,nmax),ssfr(nmod)
      real*8 lambda_eff(nmax),lambda_rest(nmax)
c     model libraries, parameters, etc.
      integer n_flux,indx(nmod)
      real*8 fprop_sfh(nmod,nprop_sfh),fmu_sfh(nmod)
      real*8 fprop_ir(nmod,nprop_ir),fmu_ir(nmod)
      real*8 ldust(nmod),mstr1(nmod),logldust(nmod),lssfr(nmod)
      real*8 flux_ir(nmod,nmax),tvism(nmod),tauv(nmod),mu(nmod)
      real*8 tbg1(nmod),tbg2(nmod),xi1(nmod),xi2(nmod),xi3(nmod)
      real*8 fmu_ism(nmod),mdust(nmod),lmdust(nmod),logmdust(nmod)
c     chi2, scaling factors, etc.
      real*8 flux_mod(nmax)
      real*8 chi2,chi2_sav,chi2_new,df
      real*8 a,num,den,a_sav
      real*8 ptot,prob,chi2_new_opt,chi2_new_ir
      real*8 chi2_opt,chi2_ir,chi2_sav_opt,chi2_sav_ir
c     histograms
      real*8 fmu_min,fmu_max,dfmu
      real*8 ssfr_min,ssfr_max,dssfr
      real*8 fmuism_min,fmuism_max,dfmu_ism
      real*8 mu_min,mu_max,dmu
      real*8 tv_min,tv_max,dtv,dtvism
      real*8 sfr_min,sfr_max,dsfr
      real*8 a_min,a_max,da
      real*8 md_min,md_max,dmd
      real*8 ld_min,ld_max,dldust
      real*8 tbg1_min,tbg1_max,dtbg,tbg2_min,tbg2_max
      real*8 xi_min,xi_max,dxi
      real*8 pct_sfr(5),pct_fmu_sfh(5),pct_fmu_ir(5)
      real*8 pct_mu(5),pct_tv(5),pct_mstr(5)
      real*8 pct_ssfr(5),pct_ld(5),pct_tbg2(5)
      real*8 pct_tbg1(5),pct_xi1(5),pct_xi2(5)
      real*8 pct_xi3(5),pct_tvism(5),pct_ism(5),pct_md(5)
      integer nbinmax1,nbinmax2
c theSkyNet parameter (nbinmax1=1500,nbinmax2=150)
      parameter (nbinmax1=3000,nbinmax2=300)
      real*8 psfh2(nbinmax2),pir2(nbinmax2),pmu2(nbinmax2)
      real*8 ptv2(nbinmax2),pxi2_2(nbinmax2),pssfr2(nbinmax2)
      real*8 pa2(nbinmax2),pldust2(nbinmax2)
      real*8 ptbg1_2(nbinmax2),ptbg2_2(nbinmax2),pxi1_2(nbinmax2)
      real*8 ptvism2(nbinmax2),pism2(nbinmax2),pxi3_2(nbinmax2)
      real*8 fmuism2_hist(nbinmax2),md2_hist(nbinmax2)
      real*8 ssfr2_hist(nbinmax2),psfr2(nbinmax2),pmd_2(nbinmax2)
      real*8 fmu2_hist(nbinmax2),mu2_hist(nbinmax2),tv2_hist(nbinmax2)
      real*8 sfr2_hist(nbinmax2),a2_hist(nbinmax2),ld2_hist(nbinmax2)
      real*8 tbg1_2_hist(nbinmax2),tbg2_2_hist(nbinmax2),xi2_hist(nbinmax2)
      real*8 tvism2_hist(nbinmax2)
c theSkyNet
c     The highest probability bin values
       real*8 hpbv, get_hpbv
       real*8 min_hpbv
       parameter(min_hpbv = 0.00001)
c theSkyNet
      integer nbin_fmu,nbin_mu,nbin_tv,nbin_a,nbin2_tvism
      integer nbin_tbg1,nbin_tbg2,nbin_xi,nbin_sfr,nbin_ld
      integer nbin2_fmu,nbin2_mu,nbin2_tv,nbin2_a,nbin_fmu_ism
      integer nbin2_fmu_ism,nbin_md,nbin2_md,nbin_ssfr,nbin2_ssfr
      integer nbin2_tbg1,nbin2_tbg2,nbin2_xi,nbin2_sfr,nbin2_ld
      real*8 sfh_hist(nmod),ir_hist(nmod)
      real*8 fmu_hist(nbinmax1),psfh(nbinmax1),pism(nbinmax1)
      real*8 pir(nbinmax1),ptbg1(nbinmax1)
      real*8 mu_hist(nbinmax1),pmu(nbinmax1),ptbg2(nbinmax1)
      real*8 tv_hist(nbinmax1),ptv(nbinmax1),ptvism(nbinmax1)
      real*8 sfr_hist(nbinmax1),psfr(nbinmax1),fmuism_hist(nbinmax1)
      real*8 pssfr(nbinmax1),a_hist(nbinmax1),pa(nbinmax1)
      real*8 ld_hist(nbinmax1),pldust(nbinmax1)
      real*8 tbg1_hist(nbinmax1),tbg2_hist(nbinmax1)
      real*8 ssfr_hist(nbinmax1),xi_hist(nbinmax1),pxi1(nbinmax1)
      real*8 pxi2(nbinmax1),pxi3(nbinmax1)
      real*8 md_hist(nbinmax1),pmd(nbinmax1)
      real*8 i_fmu_sfh(nmod),i_fmu_ir(nmod)
      real*8 i_mu(nmod),i_tauv(nmod),i_tvism(nmod)
      real*8 i_lssfr(nmod),i_fmu_ism(nmod)
      real*8 i_tbg1(nmod),i_xi1(nmod),i_xi2(nmod),i_xi3(nmod)
      real*8 i_tbg2(nmod)
c     cosmological parameters
      real*8 h,omega,omega_lambda,clambda,q
      real*8 cosmol_c,dl
c     histogram parameters: min,max,bin width
      data fmu_min/0./,fmu_max/1.0005/,dfmu/0.001/
      data fmuism_min/0./,fmuism_max/1.0005/,dfmu_ism/0.001/
      data mu_min/0./,mu_max/1.0005/,dmu/0.001/
      data tv_min/0./,tv_max/6.0025/,dtv/0.005/
      data ssfr_min/-13./,ssfr_max/-5.9975/,dssfr/0.05/
c theSkyNet data sfr_min/-3./,sfr_max/3.5005/,dsfr/0.005/
c theSkyNet data a_min/7./,a_max/13.0025/,da/0.005/
c theSkyNet data ld_min/7./,ld_max/13.0025/,dldust/0.005/
      data sfr_min/-8./,sfr_max/3.5005/,dsfr/0.005/
      data a_min/2./,a_max/13.0025/,da/0.005/
      data ld_min/2./,ld_max/13.0025/,dldust/0.005/
      data tbg1_min/30./,tbg1_max/60.0125/,dtbg/0.025/
      data tbg2_min/15./,tbg2_max/25.0125/
      data xi_min/0./,xi_max/1.0001/,dxi/0.001/
c theSkyNet data md_min/3./,md_max/9./,dmd/0.005/
      data md_min/-2./,md_max/9./,dmd/0.005/
c     cosmology
      data h/70./,omega/0.30/,omega_lambda/0.70/
      data isave/0/
c     save parameters
      save flux_ir,flux_sfh,fmu_ir,fmu_sfh
      save mstr1,ssfr,ldust,mu,tauv,fmu_ism
      save lssfr,logldust,tvism
      save tbg1,tbg2,xi1,xi2,xi3
      save flux_obs,sigma,dist
      save mdust


c     ---------------------------------------------------------------------------
c     Are we in skynet mode
c     ---------------------------------------------------------------------------
      integer numargs
      character*80 arg
      logical skynet
      integer ios
      character*100 buffer1, buffer2
      logical found_old_entry
      integer gal_number_found
      integer nfilt_dust,n_irbysfh
      real*8 logldusta

      numargs = iargc ( )
      if (numargs .eq. 0) then
c     Do nothing as this is the normal model
          skynet = .FALSE.
      else if (numargs .eq. 3) then
          skynet = .TRUE.
          call getarg ( 1, arg )
          read( arg, *) i_gal
          call getarg( 2, filters)
          call getarg( 3, obs)
      else
        write(*,*) "Requires arguments: pixel to fit, filters file, observations file"
		call EXIT(-1)
	  endif

c     ---------------------------------------------------------------------------

c     ---------------------------------------------------------------------------
c     Set things up: what filters to use, observations and models:
c     ---------------------------------------------------------------------------

c     READ FILTER FILE: "filters.dat"
      if (skynet .eqv. .FALSE.) then
          call getenv('USER_FILTERS',filters)
      endif
      close(22)
      open(22,file=filters,status='old')
      do i=1,1
         read(22,*)
      enddo
      io=0
      ifilt=0
      do while(io.eq.0)
         ifilt=ifilt+1
         read(22,*,iostat=io) filt_name(ifilt),lambda_eff(ifilt),filt_id(ifilt),fit(ifilt)
      enddo
      nfilt=ifilt-1
      close(22)

c     READ FILE WITH OBSERVATIONS:
      if (skynet .eqv. .FALSE.) then
          call getenv('USER_OBS',obs)
      endif
      close(20)
      open(20,file=obs,status='old')
      do i=1,1
         read(20,*)
      enddo
      io=0
      n_obs=0
      do while(io.eq.0)
         n_obs=n_obs+1
         read(20,*,iostat=io) gal_name(n_obs),redshift(n_obs),
     +        (flux_obs(n_obs,k),sigma(n_obs,k),k=1,nfilt)
      enddo
      n_obs=n_obs-1
      close(20)

c     READ FILE WITH REDSHIFTS OF THE MODEL LIBRARIES
      close(24)
      open(24,file='zlibs.dat',status='old')
      io=0
      nz=0
      do while(io.eq.0)
         nz=nz+1
         read(24,*,iostat=io) i,zlib(nz)
         enddo
         nz=nz-1
      close(24)

c     CHOOSE GALAXY TO FIT (enter corresponding i)
      if (skynet .eqv. .FALSE.) then
          write (6,'(x,a,$)') 'Choose galaxy - enter i_gal: '
          read (5,*) i_gal
      endif
      write(*,*) i_gal, n_obs

c     Do we have the observation
      if (i_gal .gt. n_obs) then
         write(*,*) 'Observation does not exist'
         call EXIT(0)
      endif

c     WHAT OBSERVATIONS DO YOU WANT TO FIT?
c     fit(ifilt)=1: fit flux from filter ifilt
c     fit(ifilt)=0: do not fit flux from filter ifilt (set flux=-99)
      do ifilt=1,nfilt
         if (fit(ifilt).eq.0) then
            flux_obs(i_gal,ifilt)=-99.
            sigma(i_gal,ifilt)=-99.
         endif
      enddo

c     Count number of non-zero fluxes (i.e. detections) to fit
      n_flux=0
      do k=1,nfilt
         if (flux_obs(i_gal,k).gt.0) then
            n_flux=n_flux+1
         endif
      enddo

c theSkyNet
         write(*,*) 'n_flux =',n_flux
      if (n_flux < 4) then
         call EXIT(0)
      endif
c theSkyNet

c     COMPUTE LUMINOSITY DISTANCE from z given cosmology
c     Obtain cosmological constant and q
      clambda=cosmol_c(h,omega,omega_lambda,q)

c     Compute distance in Mpc from the redshifts z
      dist(i_gal)=dl(h,q,redshift(i_gal))
      dist(i_gal)=dist(i_gal)*3.086e+24/dsqrt(1.+redshift(i_gal))


c     OUTPUT FILES
c     name.fit: fit results, PDFs etc
c     name.sed: best-fit SED
      aux_name=gal_name(i_gal)
      close(31)
c     ---------------------------------------------------------------------------
      if (skynet .eqv. .FALSE.) then
	      outfile1=aux_name(1:largo(aux_name))//'.fit'
	      outfile2=aux_name(1:largo(aux_name))//'.sed'
	      open (31, file=outfile1, status='unknown')
c     ---------------------------------------------------------------------------
      else
          write(outfile1, '(I0,a)') i_gal, '.fit'
          open (31, file=outfile1, status='unknown')
          write(31, *) '####### ',gal_name(i_gal)
      endif

c     Choose libraries according to the redshift of the source
c     Find zlib(i) closest of the galaxie's redshift
      do i=1,nz
         diffz(i)=abs(zlib(i)-redshift(i_gal))
      enddo
      call sort2(nz,diffz,zlib)
c     diff(1): minimum difference
c     zlib(1): library z we use for this galaxy
c              (if diffz(1) not gt 0.005)
      if (diffz(1).gt.0.005.and.mod(redshift(i_gal)*1000,10.).ne.5) then
         write(*,*) 'No model library at this galaxy redshift...'
         stop
      endif

      write(numz,'(f6.4)') zlib(1)
      optlib = 'starformhist_cb07_z'//numz//'.lbr'
      irlib = 'infrared_dce08_z'//numz//'.lbr'

      write(*,*) 'z= ',redshift(i_gal)
      write(*,*) 'optilib=',optlib
      write(*,*) 'irlib=',irlib

c     ---------------------------------------------------------------------------
c     What part of the SED are the filters sampling at the redshift of the galaxy?
c     - lambda(rest-frame) < 2.5 mic : emission purely stellar (attenuated by dust)
c     - 2.5 mic < lambda(rest-frame) < 10 mic : stellar + dust emission
c     - lambda(rest-frame) > 10 mic : emission purely from dust
c     ---------------------------------------------------------------------------

         nfilt_sfh=0            !nr of filters sampling the stellar emission
         nfilt_ir=0             !nr of filters sampling the dust emission
         nfilt_mix=0            !nr of filters sampling stellar+dust emission
         do i=1,nfilt
            lambda_rest(i)=lambda_eff(i)/(1.+redshift(i_gal))
            if (lambda_rest(i).lt.10.) then
               nfilt_sfh=nfilt_sfh+1
               kfilt_sfh(nfilt_sfh)=i
            endif
            if (lambda_rest(i).gt.2.5) then
               nfilt_ir=nfilt_ir+1
               kfilt_ir(nfilt_ir)=i
            endif
            if (lambda_rest(i).gt.2.5.and.lambda_rest(i).le.10) then
               nfilt_mix=nfilt_mix+1
            endif
         enddo
         nfilt_dust=nfilt_ir+nfilt_mix

         write(*,*) '   '
         write(*,*) 'At this redshift: '

         do k=1,nfilt_sfh-nfilt_mix
            write(*,*) 'purely stellar... ',filt_name(k)
         enddo
         do k=nfilt_sfh-nfilt_mix+1,nfilt_sfh
            write(*,*) 'mix stars+dust... ',filt_name(k)
         enddo
         do k=nfilt_sfh+1,nfilt
            write(*,*) 'purely dust... ',filt_name(k)
         enddo

c     ---------------------------------------------------------------------------
c     MODELS: read libraries of models with parameters + AB mags at z
c     attenuated stellar emission - optlib: starformhist_cb07_z###.lbr
c     --> nfilt_sfh model absolute AB mags
c     dust emission - irlib: infrared_dce08_z###.lbr
c     --> nfilt_ir model absolute AB mags
c     ---------------------------------------------------------------------------

         if (isave.eq.0) then
            io=0

c     READ OPTLIB
            close(21)
            open(21,file=optlib,status='old')
            do i=1,2
               read(21,*) !2 lines of header
            enddo
            write(*,*) 'Reading SFH library...'
            i_sfh=0
            io=0
            do while(io.eq.0)
               i_sfh=i_sfh+1
               read(21,*,iostat=io) indx(i_sfh),(fprop_sfh(i_sfh,j),j=1,nprop_sfh),
     +              (flux_sfh(i_sfh,j),j=1,nfilt_sfh)
               if (io.eq.0) then
c     Relevant physical parameters
                  fmu_sfh(i_sfh)=fprop_sfh(i_sfh,22)            ! fmu parameter Ld(ISM)/Ld(tot) - optical
                  mstr1(i_sfh)=fprop_sfh(i_sfh,6)               ! stellar mass
                  ldust(i_sfh)=fprop_sfh(i_sfh,21)/mstr1(i_sfh) ! total luminosity of dust (normalize to Mstar)
                  logldust(i_sfh)=dlog10(ldust(i_sfh))          ! log(Ldust)
                  mu(i_sfh)=fprop_sfh(i_sfh,5)                  ! mu parameter (CF00 model)
                  tauv(i_sfh)=fprop_sfh(i_sfh,4)                ! optical V-band depth tauV (CF00 model)
                  ssfr(i_sfh)=fprop_sfh(i_sfh,10)/mstr1(i_sfh)  ! recent SSFR_0.01Gyr / stellar mass
                  lssfr(i_sfh)=dlog10(ssfr(i_sfh))              ! log(SSFR_0.01Gyr)
                  tvism(i_sfh)=mu(i_sfh)*tauv(i_sfh)            ! mu*tauV=V-band optical depth for ISM
c     .lbr contains absolute AB magnitudes -> convert to fluxes Fnu in Lo/Hz
c     Convert all magnitudes to Lo/Hz (except H lines luminosity: in Lo)
c     Normalise SEDs to stellar mass
                  do k=1,nfilt_sfh
                     flux_sfh(i_sfh,k)=3.117336e+6
     +                    *10**(-0.4*(flux_sfh(i_sfh,k)+48.6))
                     flux_sfh(i_sfh,k)=flux_sfh(i_sfh,k)/mstr1(i_sfh)
c     1+z factor which is required in model fluxes
                     flux_sfh(i_sfh,k)=flux_sfh(i_sfh,k)/(1+redshift(i_gal))
                  enddo
               endif
            enddo
            close(21)
            n_sfh=i_sfh-1

c     READ IRLIB
            close(20)
            open(20,file=irlib,status='old')
            do i=1,2
               read(20,*)  !2 lines of header
            enddo
            write(*,*) 'Reading IR dust emission library...'
            i_ir=0
            io=0
            do while(io.eq.0)
               i_ir=i_ir+1
               read(20,*,iostat=io) (fprop_ir(i_ir,j),j=1,nprop_ir),
     +              (flux_ir(i_ir,j),j=1,nfilt_ir)
c     IR model parameters
               fmu_ir(i_ir)=fprop_ir(i_ir,1)       ! fmu parameter Ld(ISM)/Ld(tot) - infrared
               fmu_ism(i_ir)=fprop_ir(i_ir,2)      ! xi_C^ISM [cont. cold dust to Ld(ISM)]
               tbg2(i_ir)=fprop_ir(i_ir,4)         ! T_C^ISM [eq. temp. cold dust in ISM]
               tbg1(i_ir)=fprop_ir(i_ir,3)         ! T_W^BC [eq. temp. warm dust in birth clouds]
               xi1(i_ir)=fprop_ir(i_ir,5)          ! xi_PAH^BC Ld(PAH)/Ld(BC)
               xi2(i_ir)=fprop_ir(i_ir,6)          ! xi_MIR^BC Ld(MIR)/Ld(BC)
               xi3(i_ir)=fprop_ir(i_ir,7)          ! xi_W^BC Ld(warm)/Ld(BC)
               mdust(i_ir)=fprop_ir(i_ir,8)        !dust mass
               logmdust(i_ir)=dlog10(mdust(i_ir))  !dust mass log10
c     .lbr contains absolute AB magnitudes -> convert to fluxes Fnu in Lo/Hz
c     Convert all magnitudes to Lo/Hz
               do k=1,nfilt_ir
                  flux_ir(i_ir,k)=3.117336e+6
     +                 *10**(-0.4*(flux_ir(i_ir,k)+48.6))
                  flux_ir(i_ir,k)=flux_ir(i_ir,k)/(1+redshift(i_gal))
               enddo
c     Re-define IR parameters: xi^tot
               xi1(i_ir)=xi1(i_ir)*(1.-fmu_ir(i_ir))+
     +              0.550*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_PAH^tot Ld(PAH)/Ld(tot)
               xi2(i_ir)=xi2(i_ir)*(1.-fmu_ir(i_ir))+
     +              0.275*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_MIR^tot Ld(MIR)/Ld(tot)
               xi3(i_ir)=xi3(i_ir)*(1.-fmu_ir(i_ir))+
     +              0.175*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_W^tot Ld(warm)/Ld(tot)
               fmu_ism(i_ir)=fmu_ism(i_ir)*fmu_ir(i_ir)  ! xi_C^tot Ld(cold)/Ld(tot)
            enddo
 201        format(0p7f12.3,1pe12.3,1p14e12.3,1p3e12.3)
            close(20)
            n_ir=i_ir-1
            isave=1
         endif

c     ---------------------------------------------------------------------------
c     COMPARISON BETWEEN MODELS AND OBSERVATIONS:
c
c     Compare everything in the sample units:
c     Lnu (i.e. luminosity per unit frequency) in Lsun/Hz
c
c     Model fluxes: already converted from AB mags to Lnu in Lsun/Hz
c     Fluxes and physical parameters from optical library per unit Mstar=1 Msun
c     Fluxes and physical parameters from infrared library per unit Ldust=1 Lsun
c
c     Observed fluxes & uncertainties
c     Convert from Fnu in Jy to Lnu in Lo/Hz [using luminosity distance dist(i_gal)]
c     ---------------------------------------------------------------------------

c     Observed fluxes: Jy -> Lsun/Hz
         do k=1,nfilt
            if (flux_obs(i_gal,k).gt.0) then
               flux_obs(i_gal,k)=flux_obs(i_gal,k)*1.e-23
     +              *3.283608731e-33*(dist(i_gal)**2)
               sigma(i_gal,k)=sigma(i_gal,k)*1.e-23
     +              *3.283608731e-33*(dist(i_gal)**2)
            endif
            if (sigma(i_gal,k).lt.0.05*flux_obs(i_gal,k)) then
               sigma(i_gal,k)=0.05*flux_obs(i_gal,k)
            endif
         enddo

         do k=1,nfilt
            if (sigma(i_gal,k).gt.0.0) then
               w(i_gal,k) = 1.0 / (sigma(i_gal,k)**2)
            endif
         enddo

c     ---------------------------------------------------------------------------
c     Initialize variables:
         n_models=0
         chi2_sav=1.e+30
         ptot=0.
         prob=0.
         do k=1,nfilt
            flux_mod(k)=0.
         enddo
	 do i=1,nmod
	    sfh_hist(i)=0.
	    ir_hist(i)=0.
	 enddo
c theSkyNet do i=1,1500
         do i=1,nbinmax1
            psfh(i)=0.
            pir(i)=0.
            pmu(i)=0.
            ptv(i)=0.
            ptvism(i)=0.
            pssfr(i)=0.
            psfr(i)=0.
            pa(i)=0.
            pldust(i)=0.
            ptbg1(i)=0.
            ptbg2(i)=0.
            pism(i)=0.
            pxi1(i)=0.
            pxi2(i)=0.
            pxi3(i)=0.
            pmd(i)=0.
         enddo

c     ---------------------------------------------------------------------------
c     Compute histogram grids of the parameter likelihood distributions before
c     starting the big loop in which we compute chi^2 for each allowed combination
c     of stellar+dust emission model (to save time).
c
c     The high-resolution marginalized likelihood distributions will be
c     computed on-the-run
c     ---------------------------------------------------------------------------

c     f_mu (SFH) & f_mu (IR)
         call get_histgrid(dfmu,fmu_min,fmu_max,nbin_fmu,fmu_hist)
c     mu parameter
         call get_histgrid(dmu,mu_min,mu_max,nbin_mu,mu_hist)
c     tauv (dust optical depth)
         call get_histgrid(dtv,tv_min,tv_max,nbin_tv,tv_hist)
c     sSFR
         call get_histgrid(dssfr,ssfr_min,ssfr_max,nbin_ssfr,ssfr_hist)
c     SFR
         call get_histgrid(dsfr,sfr_min,sfr_max,nbin_sfr,sfr_hist)
c     Mstars
         call get_histgrid(da,a_min,a_max,nbin_a,a_hist)
c     Ldust
         call get_histgrid(dldust,ld_min,ld_max,nbin_ld,ld_hist)
c     fmu_ism
         call get_histgrid(dfmu_ism,fmuism_min,fmuism_max,nbin_fmu_ism,
     +        fmuism_hist)
c     T_BGs (ISM)
         call get_histgrid(dtbg,tbg1_min,tbg1_max,nbin_tbg1,tbg1_hist)
c     T_BGs (BC)
         call get_histgrid(dtbg,tbg2_min,tbg2_max,nbin_tbg2,tbg2_hist)
c     xi's (PAHs, VSGs, BGs)
         call get_histgrid(dxi,xi_min,xi_max,nbin_xi,xi_hist)
c     Mdust
         call get_histgrid(dmd,md_min,md_max,nbin_md,md_hist)

c     Compute histogram indexes for each parameter value
c     [makes code faster -- implemented by the Nottingham people]
         do i_sfh=1, n_sfh
            aux=((fmu_sfh(i_sfh)-fmu_min)/(fmu_max-fmu_min))*nbin_fmu
            ibin=1 + dint(aux)
            i_fmu_sfh(i_sfh) = max(1,min(ibin,nbin_fmu))

            aux = ((mu(i_sfh)-mu_min)/(mu_max-mu_min)) * nbin_mu
            ibin=1 + dint(aux)
            i_mu(i_sfh) = max(1,min(ibin,nbin_mu))

            aux=((tauv(i_sfh)-tv_min)/(tv_max-tv_min)) * nbin_tv
            ibin=1 + dint(aux)
            i_tauv(i_sfh) = max(1,min(ibin,nbin_tv))

            aux=((tvism(i_sfh)-tv_min)/(tv_max-tv_min)) * nbin_tv
            ibin=1 + dint(aux)
            i_tvism(i_sfh) = max(1,min(ibin,nbin_tv))

            if (lssfr(i_sfh).lt.ssfr_min) then
               lssfr(i_sfh)=ssfr_min !set small sfrs to sfr_min
            endif
            aux=((lssfr(i_sfh)-ssfr_min)/(ssfr_max-ssfr_min))* nbin_ssfr
            ibin=1 + dint(aux)
            i_lssfr(i_sfh) = max(1,min(ibin,nbin_sfr))
         enddo

         do i_ir=1, n_ir
            aux=((fmu_ir(i_ir)-fmu_min)/(fmu_max-fmu_min)) * nbin_fmu
            ibin=1 + dint(aux)
            i_fmu_ir(i_ir) = max(1,min(ibin,nbin_fmu))

            aux=((fmu_ism(i_ir)-fmuism_min)/(fmuism_max-fmuism_min))*nbin_fmu_ism
            ibin=1 + dint(aux)
            i_fmu_ism(i_ir) = max(1,min(ibin,nbin_fmu_ism))

            aux=((tbg1(i_ir)-tbg1_min)/(tbg1_max-tbg1_min))* nbin_tbg1
            ibin=1 + dint(aux)
            i_tbg1(i_ir) = max(1,min(ibin,nbin_tbg1))

            aux=((tbg2(i_ir)-tbg2_min)/(tbg2_max-tbg2_min))* nbin_tbg2
            ibin=1 + dint(aux)
            i_tbg2(i_ir) = max(1,min(ibin,nbin_tbg2))

            aux=((xi1(i_ir)-xi_min)/(xi_max-xi_min)) * nbin_xi
            ibin=1 + dint(aux)
            i_xi1(i_ir) = max(1,min(ibin,nbin_xi))

            aux=((xi2(i_ir)-xi_min)/(xi_max-xi_min)) * nbin_xi
            ibin=1 + dint(aux)
            i_xi2(i_ir) = max(1,min(ibin,nbin_xi))

            aux=((xi3(i_ir)-xi_min)/(xi_max-xi_min)) * nbin_xi
            ibin=1 + dint(aux)
            i_xi3(i_ir) = max(1,min(ibin,nbin_xi))
         enddo

c     ---------------------------------------------------------------------------
c     HERE STARTS THE ACTUAL FIT
c
c     For each model in the stellar library, find all the models in the infrared
c     dust emission library for which the proportion of dust luminosity from stellar
c     birth clouds and diffuse ISM is the same, i.e. same "fmu" parameter (+/- df)
c     Scale each infrared model satisfying this condition to the total dust
c     luminosity Ldust predicted by the stellar+attenuation model
c     [this satisfies the energy balance]
c
c
c     For each combination of model, compute the chi^2 goodness-of-fit
c     by comparing the observed UV-to-IR fluxes with the model predictions
c
c     The scaling factor "a" is in practice the stellar mass of the model
c     since all the fluxes are normalised to Mstar
c
c     The probability of each model is p=exp(-chi^2/2)
c     Compute marginal likelihood distributions of each parameter
c     and build high-resolution histogram of each PDF
c     ---------------------------------------------------------------------------
         write(*,*) 'Starting fit.......'
         DO i_sfh=1,n_sfh
c     Check progress of the fit...
            if (i_sfh.eq.(n_sfh/4)) then
               write (*,*) '25% done...', i_sfh, " / ", n_sfh, " opt. models"
            else if (i_sfh.eq.(n_sfh/2)) then
               write (*,*) '50% done...', i_sfh, " / ", n_sfh, " opt. models"
            else if (i_sfh.eq.(3*n_sfh/4)) then
               write (*,*) '75% done...', i_sfh, " / ", n_sfh, " opt. models"
            else if (i_sfh/n_sfh.eq.1) then
               write (*,*) '100% done...', n_sfh, " opt. models - fit finished"
            endif

            df=0.15             !fmu_opt=fmu_ir +/- dfmu
            n_irbysfh=0

c     Search for the IR models with f_mu within the range set by df
            DO i_ir=1,n_ir

               num=0.
               den=0.
               chi2=0.
               chi2_opt=0.
               chi2_ir=0.

               if (abs(fmu_sfh(i_sfh)-fmu_ir(i_ir)).le.df) then

                  n_models=n_models+1 !to keep track of total number of combinations
                  n_irbysfh=n_irbysfh+1

c     Only Compute flux_mod, chi, prob, bestfit Once per SFH, if no Dust Filters.
                  if ( (nfilt_dust.ne.0).or.((nfilt_dust.eq.0).and.(n_irbysfh.eq.1)) ) then
            	
c     Build the model flux array by adding SFH & IR
                     do k=1,nfilt_sfh-nfilt_mix
                        flux_mod(k)=flux_sfh(i_sfh,k)
                     enddo
                     do k=nfilt_sfh-nfilt_mix+1,nfilt_sfh
                        flux_mod(k)=flux_sfh(i_sfh,k)+
     +                       ldust(i_sfh)*flux_ir(i_ir,k-nfilt_sfh+nfilt_mix) !k-(nfilt_sfh-nfilt_mix)
                     enddo
                     do k=nfilt_sfh+1,nfilt
                        flux_mod(k)=ldust(i_sfh)*flux_ir(i_ir,k-nfilt_sfh+nfilt_mix)
                     enddo
c     Compute scaling factor "a" - this is the number that minimizes chi^2
                     do k=1,nfilt
                        if (flux_obs(i_gal,k).gt.0) then
                           num=num+(flux_mod(k)*flux_obs(i_gal,k)*w(i_gal,k))
                           den=den+((flux_mod(k)*flux_mod(k))*w(i_gal,k))
c                       den=den+((flux_mod(k)**2)*w(i_gal,k))
                     endif
                     enddo
                     a=num/den
c     Compute chi^2 goodness-of-fit
                     do k=1,nfilt_sfh
                        if (flux_obs(i_gal,k).gt.0) then
                           chi2=chi2+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
     +                          *(flux_obs(i_gal,k)-(a*flux_mod(k))))*w(i_gal,k))
c                          chi2=chi2+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
c    +                       **2)*w(i_gal,k))
                           chi2_opt=chi2
                        endif
                      enddo

                     if (chi2.lt.600.) then
                        do k=nfilt_sfh+1,nfilt
                           if (flux_obs(i_gal,k).gt.0) then
                              chi2=chi2+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
     +                             *(flux_obs(i_gal,k)-(a*flux_mod(k))))*w(i_gal,k))
c                             chi2=chi2+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
c    +                             **2)*w(i_gal,k))
c                             chi2_ir=chi2_ir+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
c    +                             **2)*w(i_gal,k))
                           endif
                        enddo
                     endif
c     Probability
                     prob=dexp(-0.5*chi2)
c     Best fit model
                     chi2_new=chi2
                     chi2_new_opt=chi2_opt
                     chi2_new_ir=chi2_ir
                     if (chi2_new.lt.chi2_sav) then
                        chi2_sav=chi2_new
                        sfh_sav=i_sfh
                        ir_sav=i_ir
                        a_sav=a
                        chi2_sav_opt=chi2_new_opt
c     Only Compute chi2_sav_ir if needed.
                        chi2_sav_ir=0.
                        if (chi2.lt.600.) then
                           do k=nfilt_sfh+1,nfilt
                              if (flux_obs(i_gal,k).gt.0) then
                                 chi2_sav_ir=chi2_sav_ir+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
     +                                *(flux_obs(i_gal,k)-(a*flux_mod(k))))*w(i_gal,k))
c                                chi2_sav_ir=chi2_sav_ir+(((flux_obs(i_gal,k)-(a*flux_mod(k)))
c    +                                   **2)*w(i_gal,k))
                              endif
                           enddo
                        endif
                     endif

                     a=dlog10(a)
                     logldusta=logldust(i_sfh)+dlog10(exp(a*2.30258509299404568402D0)) !Part of MDust
                  endif             !nfilt_dust condition

c     MARGINAL PROBABILITY DENSITY FUNCTIONS
c     Locate each value on the corresponding histogram bin
c     and compute probability histogram
c     (normalize only in the end of the big loop)
c     for now just add up probabilities in each bin

                  if (nfilt_dust.ne.0) then !has dust must calc for each i_ir since prob will change.
                     ptot=ptot+prob
                     sfh_hist(i_sfh)=sfh_hist(i_sfh)+prob
c     Mstar
                     aux=((a-a_min)/(a_max-a_min)) * nbin_a
                     ibin=1+dint(aux)
                     ibin = max(1,min(ibin,nbin_a))
                     pa(ibin)=pa(ibin)+prob
c     SFR_0.1Gyr
                     aux=((lssfr(i_sfh)+a-sfr_min)/(sfr_max-sfr_min))
     +                    * nbin_sfr
                     ibin= 1+dint(aux)
                     ibin = max(1,min(ibin,nbin_sfr))
                     psfr(ibin)=psfr(ibin)+prob
c     Ldust
                     aux=((logldust(i_sfh)+a-ld_min)/(ld_max-ld_min))
     +                    * nbin_ld
                     ibin=1+dint(aux)
                     ibin = max(1,min(ibin,nbin_ld))
                     pldust(ibin)=pldust(ibin)+prob

                  endif         !has dust condition

                  ir_hist(i_ir)=ir_hist(i_ir)+prob
                  
c     Mdust. Replaced 10.0**a with exp(a*log(10)) using a constant for log(10).
                  lmdust(i_ir)=logmdust(i_ir)+logldusta
c                  lmdust(i_ir)=dlog10(mdust(i_ir)*ldusta)
c                  lmdust(i_ir)=dlog10(mdust(i_ir)*ldust(i_sfh)*10.0**a)
                  aux=((lmdust(i_ir)-md_min)/(md_max-md_min))*nbin_md
                  ibin=1+dint(aux)
                  ibin = max(1,min(ibin,nbin_md))
                  pmd(ibin)=pmd(ibin)+prob

               endif            !df condition
            ENDDO               !loop in i_ir
            
            if (nfilt_dust.eq.0) then !has no dust, Save prob * n_irbysfh

               ptot=ptot+(prob*n_irbysfh)
               sfh_hist(i_sfh)=sfh_hist(i_sfh)+(prob*n_irbysfh)
c     Mstar
               aux=((a-a_min)/(a_max-a_min)) * nbin_a
               ibin=1+dint(aux)
               ibin = max(1,min(ibin,nbin_a))
               pa(ibin)=pa(ibin)+(prob*n_irbysfh)
c     SFR_0.1Gyr
               aux=((lssfr(i_sfh)+a-sfr_min)/(sfr_max-sfr_min))
     +              * nbin_sfr
               ibin= 1+dint(aux)
               ibin = max(1,min(ibin,nbin_sfr))
               psfr(ibin)=psfr(ibin)+(prob*n_irbysfh)
c     Ldust
               aux=((logldust(i_sfh)+a-ld_min)/(ld_max-ld_min))
     +              * nbin_ld
               ibin=1+dint(aux)
               ibin = max(1,min(ibin,nbin_ld))
               pldust(ibin)=pldust(ibin)+(prob*n_irbysfh)

            endif         !has no dust condition
            
         ENDDO                  !loop in i_sfh

c Expand sfh_hist
         do i_sfh=1,n_sfh
c     f_mu (SFH)
            psfh(i_fmu_sfh(i_sfh))=psfh(i_fmu_sfh(i_sfh))+sfh_hist(i_sfh)
c     mu
            pmu(i_mu(i_sfh))=pmu(i_mu(i_sfh))+sfh_hist(i_sfh)
c     tauV
            ptv(i_tauv(i_sfh))=ptv(i_tauv(i_sfh))+sfh_hist(i_sfh)
c     tvism
            ptvism(i_tvism(i_sfh))=ptvism(i_tvism(i_sfh))+sfh_hist(i_sfh)
c     sSFR_0.1Gyr
            pssfr(i_lssfr(i_sfh))=pssfr(i_lssfr(i_sfh))+sfh_hist(i_sfh)
         enddo
         
         do i_ir=1,n_ir
c     f_mu (IR)
            pir(i_fmu_ir(i_ir))=pir(i_fmu_ir(i_ir))+ir_hist(i_ir)
c     xi_C^tot
            pism(i_fmu_ism(i_ir))=pism(i_fmu_ism(i_ir))+ir_hist(i_ir)
c     T_C^ISM
            ptbg1(i_tbg1(i_ir))=ptbg1(i_tbg1(i_ir))+ir_hist(i_ir)
c     T_W^BC
            ptbg2(i_tbg2(i_ir))=ptbg2(i_tbg2(i_ir))+ir_hist(i_ir)
c     xi_PAH^tot
            pxi1(i_xi1(i_ir))=pxi1(i_xi1(i_ir))+ir_hist(i_ir)
c     xi_MIR^tot
            pxi2(i_xi2(i_ir))=pxi2(i_xi2(i_ir))+ir_hist(i_ir)
c     xi_W^tot
            pxi3(i_xi3(i_ir))=pxi3(i_xi3(i_ir))+ir_hist(i_ir)         
         enddo
	
c     Chi2-weighted models: normalize to total probability ptot
         write(*,*) 'Number of random SFH models:       ', n_sfh
         write(*,*) 'Number of IR dust emission models: ', n_ir
         write(*,*) 'Value of df:                       ', df
         write(*,*) 'Total number of models:            ', n_models
         write(*,*) 'ptot= ',ptot
         write(*,*) 'chi2_optical= ',chi2_sav_opt
         write(*,*) 'chi2_infrared= ',chi2_sav_ir

c     ---------------------------------------------------------------------------
c     Compute percentiles of the (normalized) likelihood distributions
c     ---------------------------------------------------------------------------
c theSkyNet do i=1,1500
         do i=1,3000
            psfh(i)=psfh(i)/ptot
            pir(i)=pir(i)/ptot
            pmu(i)=pmu(i)/ptot
            ptv(i)=ptv(i)/ptot
            ptvism(i)=ptvism(i)/ptot
            psfr(i)=psfr(i)/ptot
            pssfr(i)=pssfr(i)/ptot
            pa(i)=pa(i)/ptot
            pldust(i)=pldust(i)/ptot
            pism(i)=pism(i)/ptot
            ptbg1(i)=ptbg1(i)/ptot
            ptbg2(i)=ptbg2(i)/ptot
            pxi1(i)=pxi1(i)/ptot
            pxi2(i)=pxi2(i)/ptot
            pxi3(i)=pxi3(i)/ptot
            pmd(i)=pmd(i)/ptot
         enddo

         call get_percentiles(nbin_fmu,fmu_hist,psfh,pct_fmu_sfh)
         call get_percentiles(nbin_fmu,fmu_hist,pir,pct_fmu_ir)
         call get_percentiles(nbin_mu,mu_hist,pmu,pct_mu)
         call get_percentiles(nbin_tv,tv_hist,ptv,pct_tv)
         call get_percentiles(nbin_tv,tv_hist,ptvism,pct_tvism)
         call get_percentiles(nbin_ssfr,ssfr_hist,pssfr,pct_ssfr)
         call get_percentiles(nbin_sfr,sfr_hist,psfr,pct_sfr)
         call get_percentiles(nbin_a,a_hist,pa,pct_mstr)
         call get_percentiles(nbin_ld,ld_hist,pldust,pct_ld)
         call get_percentiles(nbin_fmu_ism,fmuism_hist,pism,pct_ism)
         call get_percentiles(nbin_tbg1,tbg1_hist,ptbg1,pct_tbg1)
         call get_percentiles(nbin_tbg2,tbg2_hist,ptbg2,pct_tbg2)
         call get_percentiles(nbin_xi,xi_hist,pxi1,pct_xi1)
         call get_percentiles(nbin_xi,xi_hist,pxi2,pct_xi2)
         call get_percentiles(nbin_xi,xi_hist,pxi3,pct_xi3)
         call get_percentiles(nbin_md,md_hist,pmd,pct_md)

c     ---------------------------------------------------------------------------
c     Degrade the resolution od the likelihood distribution histograms
c     from 3000 max bins to 100 max bins for storing in output file + plotting
c     ---------------------------------------------------------------------------
         do i=1,100
            psfh2(i)=0.
            pir2(i)=0.
            pmu2(i)=0.
            ptv2(i)=0.
            ptvism2(i)=0.
            pssfr2(i)=0.
            psfr2(i)=0.
            pa2(i)=0.
            pldust2(i)=0.
            pism2(i)=0.
            ptbg1_2(i)=0.
            ptbg2_2(i)=0.
            pxi1_2(i)=0.
            pxi2_2(i)=0.
            pxi3_2(i)=0.
            pmd_2(i)=0.
         enddo

c     New histogram parameters
         dfmu=0.05
         fmu_min=0.
         fmu_max=1.
         dfmu_ism=0.05
         fmuism_min=0.
         fmuism_max=1.
         dtv=0.125
         dtvism=0.075
         tv_min=0.
         tv_max=6.
         dssfr=0.10
         ssfr_min=-13.0
         ssfr_max=-6.0
         dsfr=0.10
c theSkyNet sfr_min=-3.
         sfr_min=-8.
         sfr_max=3.
         da=0.10
c theSkyNet a_min=7.0
         a_min=2.0
         a_max=13.0
         dtbg=1.
         tbg2_min=15.
         tbg2_max=25.
         tbg1_min=30.
         tbg1_max=60.
         dxi=0.05
         dmd=0.10
c theSkyNet md_min=3.
         md_min=-2.
         md_max=9.

         call degrade_hist(dfmu,fmu_min,fmu_max,nbin_fmu,nbin2_fmu,
     +        fmu_hist,fmu2_hist,psfh,psfh2)
         call degrade_hist(dfmu,fmu_min,fmu_max,nbin_fmu,nbin2_fmu,
     +        fmu_hist,fmu2_hist,pir,pir2)
         call degrade_hist(dfmu,fmu_min,fmu_max,nbin_mu,nbin2_mu,
     +        mu_hist,mu2_hist,pmu,pmu2)
         call degrade_hist(dtv,tv_min,tv_max,nbin_tv,nbin2_tv,tv_hist,
     +        tv2_hist,ptv,ptv2)
         call degrade_hist(dtvism,tv_min,tv_max,nbin_tv,nbin2_tvism,
     +        tv_hist,tvism2_hist,ptvism,ptvism2)
         call degrade_hist(dssfr,ssfr_min,ssfr_max,nbin_ssfr,nbin2_ssfr,
     +        ssfr_hist,ssfr2_hist,pssfr,pssfr2)
         call degrade_hist(dsfr,sfr_min,sfr_max,nbin_sfr,nbin2_sfr,
     +        sfr_hist,sfr2_hist,psfr,psfr2)
         call degrade_hist(da,a_min,a_max,nbin_a,nbin2_a,a_hist,
     +        a2_hist,pa,pa2)
         call degrade_hist(da,a_min,a_max,nbin_ld,nbin2_ld,ld_hist,
     +        ld2_hist,pldust,pldust2)
         call degrade_hist(dfmu_ism,fmuism_min,fmuism_max,
     +        nbin_fmu_ism,nbin2_fmu_ism,
     +        fmuism_hist,fmuism2_hist,pism,pism2)
         call degrade_hist(dtbg,tbg1_min,tbg1_max,nbin_tbg1,
     +        nbin2_tbg1,
     +        tbg1_hist,tbg1_2_hist,ptbg1,ptbg1_2)
         call degrade_hist(dtbg,tbg2_min,tbg2_max,nbin_tbg2,
     +        nbin2_tbg2,
     +        tbg2_hist,tbg2_2_hist,ptbg2,ptbg2_2)
         call degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,nbin2_xi,
     +        xi_hist,xi2_hist,pxi1,pxi1_2)
         call degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,nbin2_xi,
     +        xi_hist,xi2_hist,pxi2,pxi2_2)
         call degrade_hist(dxi,fmu_min,fmu_max,nbin_xi,nbin2_xi,
     +        xi_hist,xi2_hist,pxi3,pxi3_2)
         call degrade_hist(dmd,md_min,md_max,nbin_md,nbin2_md,
     +        md_hist,md2_hist,pmd,pmd_2)

c     ---------------------------------------------------------------------------
c     Store fit results in .fit output file
c     ---------------------------------------------------------------------------
         write(31,702)
 702     format('# OBSERVED FLUXES (and errors):')
         write(filter_header,*) (filt_name(k),k=1,nfilt)
         write(31,*) '#  '//filter_header(1:largo(filter_header))

         write(31,701) (flux_obs(i_gal,k),k=1,nfilt)
         write(31,701) (sigma(i_gal,k),k=1,nfilt)
         write(31,703)
 703     format('#')

         write(31,800)
 800     format('# ... Results of fitting the fluxes to the model.....')
 802     format('#.fmu(SFH)...fmu(IR)........mu......tauv',
     +        '........sSFR..........M*.......Ldust',
     +        '......T_W^BC.....T_C^ISM....xi_C^tot',
     +        '..xi_PAH^tot..xi_MIR^tot....xi_W^tot.....tvism',
     +        '.......Mdust.....SFR')
 803     format(0p4f10.3,1p3e12.3,0p2f10.1,0p5f10.3,1p2e12.3)

         write(31,703)
         write(31,804)
 804     format('# BEST FIT MODEL: (i_sfh, i_ir, chi2, redshift)')
         write(31,311) indx(sfh_sav),ir_sav,chi2_sav/n_flux,
     +        redshift(i_gal)
 311     format(2i10,0pf10.3,0pf12.6)
         write(31,802)
         write(31,803) fmu_sfh(sfh_sav),fmu_ir(ir_sav),mu(sfh_sav),
     +        tauv(sfh_sav),ssfr(sfh_sav),a_sav,
     +        ldust(sfh_sav)*a_sav,tbg1(ir_sav),tbg2(ir_sav),
     +        fmu_ism(ir_sav),xi1(ir_sav),
     +        xi2(ir_sav),xi3(ir_sav),
     +        tvism(sfh_sav),mdust(ir_sav)*a_sav*ldust(sfh_sav),
     +        ssfr(sfh_sav)*a_sav

         write(31,*) '#  '//filter_header(1:largo(filter_header))
         write(31,701) (a_sav*flux_sfh(sfh_sav,k),k=1,nfilt_sfh-nfilt_mix),
     +        (a_sav*(flux_sfh(sfh_sav,k)
     +        +flux_ir(ir_sav,k-nfilt_sfh+nfilt_mix)*ldust(sfh_sav)),
     +        k=nfilt_sfh-nfilt_mix+1,nfilt_sfh),
     +        (a_sav*flux_ir(ir_sav,k-nfilt_sfh+nfilt_mix)*ldust(sfh_sav),
     +        k=nfilt_sfh+1,nfilt)
 701     format(1p50e12.3)

         write(31,703)
         write(31,805)
 805     format('# MARGINAL PDF HISTOGRAMS FOR EACH PARAMETER......')

 807     format(0pf10.4,1pe12.3e3)
 60      format('#....percentiles of the PDF......')
 61      format(0p5f8.3)
 62      format(1p5e12.3e3)

c theSkyNet
 900     format('# theSkyNet2')
 901     format(4(0pf10.4))
c theSkyNet

         write(31,806)
 806     format('# ... f_mu (SFH) ...')
         do ibin=1,nbin2_fmu
c theSkyNet
            write(31,807) fmu2_hist(ibin),psfh2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_fmu_sfh(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(psfh2, fmu2_hist, nbin2_fmu)
         write(31, 900)
         write(31, 901) hpbv, fmu2_hist(1), fmu2_hist(nbin2_fmu), fmu2_hist(2) - fmu2_hist(1)
c theSkyNet

         write(31,808)
 808     format('# ... f_mu (IR) ...')
         do ibin=1,nbin2_fmu
c theSkyNet
            write(31,807) fmu2_hist(ibin),pir2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_fmu_ir(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pir2, fmu2_hist, nbin2_fmu)
         write(31, 900)
         write(31, 901) hpbv, fmu2_hist(1), fmu2_hist(nbin2_fmu), fmu2_hist(2) - fmu2_hist(1)
c theSkyNet

         write(31,809)
 809     format('# ... mu parameter ...')
         do ibin=1,nbin2_mu
c theSkyNet
            write(31,807) mu2_hist(ibin),pmu2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_mu(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pmu2, mu2_hist, nbin2_mu)
         write(31, 900)
         write(31, 901) hpbv, mu2_hist(1), mu2_hist(nbin2_mu), mu2_hist(2) - mu2_hist(1)
c theSkyNet

         write(31,810)
 810     format('# ... tau_V ...')
         do ibin=1,nbin2_tv
c theSkyNet
            write(31,807) tv2_hist(ibin),ptv2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_tv(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(ptv2, tv2_hist, nbin2_tv)
         write(31, 900)
         write(31, 901) hpbv, tv2_hist(1), tv2_hist(nbin2_tv), tv2_hist(2) - tv2_hist(1)
c theSkyNet

         write(31,811)
 811     format('# ... sSFR_0.1Gyr ...')
         do ibin=1,nbin2_ssfr
c theSkyNet
            write(31,812) ssfr2_hist(ibin),pssfr2(ibin)
         enddo
 812     format(1p2e12.3e3)
         write(31,60)
         write(31,62) (pct_ssfr(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pssfr2, ssfr2_hist, nbin2_ssfr)
         write(31, 900)
         write(31, 901) hpbv, ssfr2_hist(1), ssfr2_hist(nbin2_ssfr), ssfr2_hist(2) - ssfr2_hist(1)
c theSkyNet

         write(31,813)
 813     format('# ... M(stars) ...')
         do ibin=1,nbin2_a
c theSkyNet
            write(31,812) a2_hist(ibin),pa2(ibin)
         enddo
         write(31,60)
         write(31,62) (pct_mstr(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pa2, a2_hist, nbin2_a)
         write(31, 900)
         write(31, 901) hpbv, a2_hist(1), a2_hist(nbin2_a), a2_hist(2) - a2_hist(1)
c theSkyNet

         write(31,814)
 814     format('# ... Ldust ...')
         do ibin=1,nbin2_ld
c theSkyNet
            write(31,812) ld2_hist(ibin),pldust2(ibin)
         enddo
         write(31,60)
         write(31,62) (pct_ld(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pldust2, ld2_hist, nbin2_ld)
         write(31, 900)
         write(31, 901) hpbv, ld2_hist(1), ld2_hist(nbin2_ld), ld2_hist(2) - ld2_hist(1)
c theSkyNet

         write(31,815)
 815     format('# ... T_C^ISM ...')
         do ibin=1,nbin2_tbg2
c theSkyNet
            write(31,807) tbg2_2_hist(ibin),ptbg2_2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_tbg2(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(ptbg2_2, tbg2_2_hist, nbin2_tbg2)
         write(31, 900)
         write(31, 901) hpbv, tbg2_2_hist(1), tbg2_2_hist(nbin2_tbg2), tbg2_2_hist(2) - tbg2_2_hist(1)
c theSkyNet

         write(31,820)
 820     format('# ... T_W^BC ...')
         do ibin=1,nbin2_tbg1
c theSkyNet
            write(31,807) tbg1_2_hist(ibin),ptbg1_2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_tbg1(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(ptbg1_2, tbg1_2_hist, nbin2_tbg1)
         write(31, 900)
         write(31, 901) hpbv, tbg1_2_hist(1), tbg1_2_hist(nbin2_tbg1), tbg1_2_hist(2) - tbg1_2_hist(1)
c theSkyNet

         write(31,821)
 821     format('# ... xi_C^tot ...')
         do ibin=1,nbin2_fmu_ism
c theSkyNet
            write(31,807) fmuism2_hist(ibin),pism2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_ism(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pism2, fmuism2_hist, nbin2_fmu_ism)
         write(31, 900)
         write(31, 901) hpbv, fmuism2_hist(1), fmuism2_hist(nbin2_fmu_ism), fmuism2_hist(2) - fmuism2_hist(1)
c theSkyNet

         write(31,816)
 816     format('# ... xi_PAH^tot ...')
         do ibin=1,nbin2_xi
c theSkyNet
            write(31,807) xi2_hist(ibin),pxi1_2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_xi1(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pxi1_2, xi2_hist, nbin2_xi)
         write(31, 900)
         write(31, 901) hpbv, xi2_hist(1), xi2_hist(nbin2_xi), xi2_hist(2) - xi2_hist(1)
c theSkyNet

         write(31,817)
 817     format('# ... xi_MIR^tot ...')
         do ibin=1,nbin2_xi
c theSkyNet
            write(31,807) xi2_hist(ibin),pxi2_2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_xi2(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pxi2_2, xi2_hist, nbin2_xi)
         write(31, 900)
         write(31, 901) hpbv, xi2_hist(1), xi2_hist(nbin2_xi), xi2_hist(2) - xi2_hist(1)
c theSkyNet

         write(31,818)
 818     format('# ... xi_W^tot ...')
         do ibin=1,nbin2_xi
c theSkyNet
            write(31,807) xi2_hist(ibin),pxi3_2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_xi3(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pxi3_2, xi2_hist, nbin2_xi)
         write(31, 900)
         write(31, 901) hpbv, xi2_hist(1), xi2_hist(nbin2_xi), xi2_hist(2) - xi2_hist(1)
c theSkyNet

         write(31,81)
 81      format('# ... tau_V^ISM...')
         do ibin=1,nbin2_tvism
c theSkyNet
            write(31,807) tvism2_hist(ibin),ptvism2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_tvism(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(ptvism2, tvism2_hist, nbin2_tvism)
         write(31, 900)
         write(31, 901) hpbv, tvism2_hist(1), tvism2_hist(nbin2_tvism), tvism2_hist(2) - tvism2_hist(1)
c theSkyNet

         write(31,888)
 888     format('# ... M(dust)...')
         do ibin=1,nbin2_md
c theSkyNet
            write(31,807) md2_hist(ibin),pmd_2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_md(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(pmd_2, md2_hist, nbin2_md)
         write(31, 900)
         write(31, 901) hpbv, md2_hist(1), md2_hist(nbin2_md), md2_hist(2) - md2_hist(1)
c theSkyNet

         write(31,889)
 889     format('# ... SFR_0.1Gyr ...')
         do ibin=1,nbin2_sfr
c theSkyNet
            write(31,812) sfr2_hist(ibin),psfr2(ibin)
         enddo
         write(31,60)
         write(31,61) (pct_sfr(k),k=1,5)
c theSkyNet
         hpbv = get_hpbv(psfr2, sfr2_hist, nbin2_sfr)
         write(31, 900)
         write(31, 901) hpbv, sfr2_hist(1), sfr2_hist(nbin2_sfr), sfr2_hist(2) - sfr2_hist(1)
c theSkyNet

c     ---------------------------------------------------------------------------
         if (skynet .eqv. .TRUE.) then
            write(31,*) '#...theSkyNet parameters of this model'
            write(31,'(2I15,E20.6,E20.4,E10.2)') indx(sfh_sav),ir_sav,a_sav,fmu_sfh(sfh_sav),redshift(i_gal)

            close (31)
         else
c     ---------------------------------------------------------------------------

            write(*,*) 'Storing best-fit SED...'
            write(*,*) outfile2
            call get_bestfit_sed(indx(sfh_sav),ir_sav,a_sav,
     +           fmu_sfh(sfh_sav),redshift(i_gal),outfile2)
         endif
         STOP
         END

c theSkyNet
c     ===========================================================================
      REAL*8 FUNCTION GET_HPBV(hist1, hist2, nbin)
c     ---------------------------------------------------------------------------
c     Find the bin with the highest probability value
c     ---------------------------------------------------------------------------
      implicit none
      integer nbin, ibin
      real*8  hist1(nbin), hist2(nbin), max_pr

      do ibin=1,nbin
         if (ibin .eq. 1) then
            max_pr = hist1(ibin)
            get_hpbv = hist2(ibin)
         else if (hist1(ibin) .gt. max_pr) then
            max_pr = hist1(ibin)
            get_hpbv = hist2(ibin)
         endif
      enddo
      RETURN
      END
c theSkyNet

c     ===========================================================================
      SUBROUTINE DEGRADE_HIST(delta,min,max,nbin1,nbin2,hist1,hist2,prob1,prob2)
c     ---------------------------------------------------------------------------
c     Degrades the resolution of the histograms containing the likelihood
c     distribution of the parameters: to facilitate storage & visualization
c     ---------------------------------------------------------------------------
c     delta : bin width
c     min   : minumum value
c     max   : maximum value
c     nbin1 : number of bins of high-res histogram
c     nbin2 : number of bins of output low-res histogram
c     hist1 : input high-res histogram x-axis
c     hist2 : output low-res histogram x-axis
c     prob1 : input histogram values
c     prob2 : output histogram values
c     ===========================================================================
      implicit none
      integer nbin1,nbin2,i,ibin,maxnbin2
      parameter(maxnbin2=200)
      real*8 delta,max,min,max2
      real*8 hist1(nbin1),prob1(nbin1)
      real*8 hist2(maxnbin2),prob2(maxnbin2)
      real*8 aux

      max2=0.
      max2=max+(delta/2.)

      call get_histgrid(delta,min,max2,nbin2,hist2)

      do i=1,nbin1
         aux=((hist1(i)-min)/(max-min)) * nbin2
         ibin=1+dint(aux)
         prob2(ibin)=prob2(ibin)+prob1(i)
      enddo

      RETURN
      END

c     ===========================================================================
      SUBROUTINE GET_HISTGRID(dv,vmin,vmax,nbin,vout)
c     ---------------------------------------------------------------------------
c     Build histogram grid (i.e. vector of bins)
c     ---------------------------------------------------------------------------
c       dv : bin width
c     vmin : minumum value
c     vmax : maximum value
c     nbin : number of bins
c     vout : output vector of bins
c     ===========================================================================
      implicit none
      integer nbin,ibin,maxnbin
      parameter(maxnbin=5000)
      real*8 vout(maxnbin)
      real*8 vmin,vmax,x1,x2,dv

      ibin=1
      x1=vmin
      x2=vmin+dv
      do while (x2.le.vmax)
         vout(ibin)=0.5*(x1+x2)
         ibin=ibin+1
         x1=x1+dv
         x2=x2+dv
      enddo
      nbin=ibin-1
      return
      END

c     ===========================================================================
      SUBROUTINE GET_PERCENTILES(n,par,probability,percentile)
c     ---------------------------------------------------------------------------
c     Calculates percentiles of the probability distibution
c     for a given parameter: 2.5, 16, 50 (median), 84, 97.5
c     1. Sort the parameter + the probability array
c     2. Find the parameter value M for which:
c        P (x < M) = P (x > M) = percentiles
c     ---------------------------------------------------------------------------
c               n : number of points (bins)
c             par : parameter value (vector of bins)
c     probability : vector with prob of each parameter value (or bin)
c      percentile : vector containing 5 percentiles described above
c     ===========================================================================
      integer n,n_perc(5),i
      real*8 par(n),probability(n),pless
      real*8 percentile(5),limit(5)

      data limit/0.025,0.16,0.50,0.84,0.975/

      call sort2(n,par,probability)

      pless=0.
      do i=1,5
         n_perc(i)=1
         pless=0.
         do while (pless.le.limit(i))
            pless=pless+probability(n_perc(i))
            n_perc(i)=n_perc(i)+1
         enddo
         n_perc(i)=n_perc(i)-1
         percentile(i)=par(n_perc(i))
      enddo

      return
      END

c     ===========================================================================
      SUBROUTINE sort2(n,arr,brr)
c     ---------------------------------------------------------------------------
c     Sorts an array arr(1:n) into ascending order using Quicksort
c     while making the corresponding rearrangement of the array brr(1:n)
c     ===========================================================================
      INTEGER n,M,NSTACK
      REAL*8 arr(n),brr(n)
      PARAMETER (M=7,NSTACK=5000)
      INTEGER i,ir,j,jstack,k,l,istack(NSTACK)
      REAL*8 a,b,temp
      jstack=0
      l=1
      ir=n
 1    if (ir-l.lt.M) then
         do j=l+1,ir
            a=arr(j)
            b=brr(j)
            do i=j-1,l,-1
               if (arr(i).le.a) goto 2
               arr(i+1)=arr(i)
               brr(i+1)=brr(i)
            enddo
            i=l-1
 2          arr(i+1)=a
            brr(i+1)=b
         enddo
         if (jstack.eq.0) return
         ir=istack(jstack)
         l=istack(jstack-1)
         jstack=jstack-2
      else
         k=(l+ir)/2
         temp=arr(k)
         arr(k)=arr(l+1)
         arr(l+1)=temp
         temp=brr(k)
         brr(k)=brr(l+1)
         brr(l+1)=temp
         if (arr(l).gt.arr(ir)) then
            temp=arr(l)
            arr(l)=arr(ir)
            arr(ir)=temp
            temp=brr(l)
            brr(l)=brr(ir)
            brr(ir)=temp
         endif
         if (arr(l+1).gt.arr(ir)) then
            temp=arr(l+1)
            arr(l+1)=arr(ir)
            arr(ir)=temp
            temp=brr(l+1)
            brr(l+1)=brr(ir)
            brr(ir)=temp
         endif
         if (arr(l).gt.arr(l+1)) then
            temp=arr(l)
            arr(l)=arr(l+1)
            arr(l+1)=temp
            temp=brr(l)
            brr(l)=brr(l+1)
            brr(l+1)=temp
         endif
         i=l+1
         j=ir
         a=arr(l+1)
         b=brr(l+1)
 3       continue
         i=i+1
         if (arr(i).lt.a) goto 3
 4       continue
         j=j-1
         if (arr(j).gt.a) goto 4
         if (j.lt.i) goto 5
         temp=arr(i)
         arr(i)=arr(j)
         arr(j)=temp
         temp=brr(i)
         brr(i)=brr(j)
         brr(j)=temp
         goto 3
 5       arr(l+1)=arr(j)
         arr(j)=a
         brr(l+1)=brr(j)
         brr(j)=b
         jstack=jstack+2
         if (jstack.gt.NSTACK) write (*,*) 'NSTACK too small in sort2'
         if (ir-i+1.ge.j-l) then
            istack(jstack)=ir
            istack(jstack-1)=i
            ir=j-1
         else
            istack(jstack)=j-1
            istack(jstack-1)=l
            l=i
         endif
      endif
      goto 1
      END


c     ===========================================================================
      REAL*8 FUNCTION DL(h,q,z)
c     ---------------------------------------------------------------------------
c     Computes luminosity distance corresponding to a redshift z.
c     Uses Mattig formulae for qo both 0 and non 0
c     Revised January 1991 to implement cosmolgical constant
c     Ho in km/sec/Mpc, DL is in Mpc
c     ===========================================================================
      implicit none
      real*8 h, q, z, d1, d2
      real*8 aa, bb, epsr, s, s0, funl
      real*8 dd1, dd2, omega0
      logical success
      integer npts
      external funl
      common /cosm/ omega0

      if (z.le.0.) then
         dl=1.e-5               !10 pc
         return
      endif

      if (q .eq. 0) then
         dl = ((3.e5 * z) * (1 + (z / 2.))) / h
      else if (q .gt. 0.) then
         d1 = (q * z) + ((q - 1.) * (sqrt(1. + ((2. * q) * z)) - 1.))
         d2 = ((h * q) * q) / 3.e5
         dl = d1 / d2
      else if (q .lt. 0.) then
         omega0 = (2. * (q + 1.)) / 3.
         aa = 1.
         bb = 1. + z
         success=.false.
         s0=1.e-10
         npts=0
         do while (.not.success)
            npts=npts+1
            call midpnt(funl,aa,bb,s,npts)
            epsr=abs(s-s0)/s0
            if (epsr.lt.1.e-4) then
               success=.true.
            else
               s0=s
            endif
         enddo
         dd1=s
	 dd2 = (3.e5 * (1. + z)) / (h * sqrt(omega0))
	 dl = dd1 * dd2
      end if

      return
      end

c     ===========================================================================
      REAL*8 FUNCTION FUNL(x)
c     ---------------------------------------------------------------------------
c     For non-zero cosmological constant
c     ===========================================================================
      real*8 x, omega0, omegainv
      common /cosm/ omega0
      omegainv = 1. / omega0
      funl = 1. / sqrt(((x ** 3.) + omegainv) - 1.)
      return
      end


c     ===========================================================================
      SUBROUTINE MIDPNT(func,a,b,s,n)
c     ===========================================================================
      INTEGER n
      REAL*8 a,b,s,func
      EXTERNAL func
      INTEGER it,j
      REAL*8 ddel,del,sum,tnm,x
      if (n.eq.1) then
         s=(b-a)*func(0.5*(a+b))
      else
         it=3**(n-2)
         tnm=it
         del=(b-a)/(3.*tnm)
         ddel=del+del
         x=a+0.5*del
         sum=0.
         do 11 j=1,it
            sum=sum+func(x)
            x=x+ddel
            sum=sum+func(x)
            x=x+del
 11      continue
         s=(s+(b-a)*sum/tnm)/3.
      endif
      return
      END

c     ===========================================================================
      REAL*8 FUNCTION COSMOL_C(h,omega,omega_lambda,q)
c     ---------------------------------------------------------------------------
c     Returns cosmological constant = cosmol_c and parameter q
c
c     Omega is entered by the user
c     omega=1.-omega_lambda
c     ===========================================================================
      real*8 h,omega,omega_lambda,q

c     Cosmological constant
      cosmol_c=omega_lambda/(3.*h**2)
c     Compute q=q0
      if (omega_lambda.eq.0.) then
         q=omega/2.
      else
         q=(3.*omega/2.) - 1.
      endif
      return
      end

c     ===========================================================================
      REAL*8 FUNCTION T(h, q, z, lamb)
c     ---------------------------------------------------------------------------
c     Returns age of universe at redshift z
c     ===========================================================================
      implicit none
      real*8 h, q, z, a, b, c, hh0, cosh, x, lamb
      real*8 aa, bb, epsr, s0, s, funq, omega0
      integer npts
      logical success
      external funq
      common /cosm/ omega0

c     H = Ho in km/sec/Mpc
c     Q = qo  (if problems with qo = 0, try 0.0001)

      a(q,z) = (sqrt(1. + ((2. * q) * z)) / (1. - (2. * q))) / (1. + z)
      b(q) = q / (abs((2. * q) - 1.) ** 1.5)
      c(q,z) = ((1. - (q * (1. - z))) / q) / (1. + z)

      cosh(x) = dlog10(x + sqrt((x ** 2) - 1.))
      hh0 = h * 0.001022
c     in (billion years)**(-1)

      if (lamb .ne. 0.0) then
         omega0 = (2. * (q + 1.)) / 3.
         aa = 0.
         bb = 1. / (1. + z)
         success=.false.
         s0=1.e-10
         npts=0
         do while (.not.success)
            npts=npts+1
            call midpnt(funq,aa,bb,s,npts)
            epsr=abs(s-s0)/s0
            if (epsr.lt.1.e-4) then
               success=.true.
            else
               s0=s
            endif
         enddo
         t=s
      else if (q .eq. 0.0) then
         t = 1. / (1. + z)
      else if (q .lt. 0.5) then
         t = a(q,z) - (b(q) * cosh(c(q,z)))
      else if (q .eq. 0.5) then
         t = (2. / 3.) / ((1. + z) ** 1.5)
      else
         t = a(q,z) + (b(q) * cos(c(q,z)))
      end if

      t = t / hh0

      return
      end


c     ===========================================================================
      REAL*8 FUNCTION FUNQ(x)
c     ---------------------------------------------------------------------------
c     For non-zero cosmological constant
c     ===========================================================================
      real*8 x, omega0, omegainv
      common /cosm/ omega0
      omegainv = 1. / omega0
      funq = sqrt(omegainv) / (x*sqrt((omegainv-1.)+(1./(x**3.))))
      return
      end

c     ===========================================================================
      FUNCTION LARGO(A)
c     ---------------------------------------------------------------------------
c     Returns significant length of string a
c     ===========================================================================
      Character*(*) a
      largo=0
      do i=1,len(a)
         if (a(i:i).ne.' ') largo=i
      enddo
      return
      end


c     ===========================================================================
      SUBROUTINE GET_BESTFIT_SED(i_opt,i_ir,dmstar,dfmu_aux,dz,outfile)
c     ---------------------------------------------------------------------------
c     Gets the total (UV-to-infrared) best-fit SED
c
c     Gets stellar spectrum and dust emission spectra from .bin files
c     and adds them to get total SED, and writes output in .sed file
c
c        i_opt : index in the Optical library
c         i_ir : index in the Infrared library
c       dmstar : stellar mass (scaling)
c     dfmu_aux : fmu_optical (to check if we got the right model)
c           dz : redshift
c      outfile : .sed file (output)
c     ===========================================================================
      implicit none
      character infile1*80,infile2*80
      character*10 outfile
      integer nage,niw_opt,niw_ir,niw_tot
      integer i,imod,nburst,k
      integer i_opt,i_ir,indx
      parameter(niw_tot=12817)
      real tform,gamma,zmet,tauv0,mu,mstr1,mstr0,mstry,tlastburst,age_wm,age_wr
      real fmu,ldtot,fbc,aux,lha,lhb
      real wl_opt(6918),opt_sed(6918),opt_sed0(6918)
      real wl_ir(6450),ir_sed(6450),irprop(8)
      real age(1000),sfr(1000)
      real fburst(5),ftot(5),sfrav(5)
      real*8 dfmu_aux,dmstar,dz
      real fmu_aux,mstar,z
      real fmuopt(50000),fmuir(50000)
      real fopt(6918),fopt0(6918),ldust
      real fir(6450),fopt_int(niw_tot),fopt_int0(niw_tot)
      real sedtot(niw_tot),wl(niw_tot)
      real fir_new(niw_tot),fopt_new(niw_tot),fopt_aux(niw_tot)
      real fopt_new0(niw_tot),fopt_aux0(niw_tot)

      mstar=sngl(dmstar)
      fmu_aux=sngl(dfmu_aux)
      z=sngl(dz)

      call getenv('OPTILIB',infile1)
      call getenv('IRLIB',infile2)

      close (29)
      open (29,file=infile1,status='old',form='unformatted')

      close (30)
      open (30,file=infile2,status='old',form='unformatted')

      close (31)
      open (31,file=outfile,status='unknown')

      write(31,*) '#...Main parameters of this model:'
      write(31,319)

c     Read Optical SEDs and properties (1st file = models 1 to 25000)
 7    read (29) niw_opt,(wl_opt(i),i=1,niw_opt)
      indx=0
      do imod=1,25000
         indx=indx+1
         read (29,end=1) tform,gamma,zmet,tauv0,mu,nburst,
     .        mstr1,mstr0,mstry,tlastburst,
     .        (fburst(i),i=1,5),(ftot(i),i=1,5),
     .        age_wm,age_wr,aux,aux,aux,aux,
     .        lha,lhb,aux,aux,ldtot,fmu,fbc
         read (29) nage,(age(i),sfr(i),i=1,nage),(sfrav(i),i=1,5)
         sfrav(3)=sfrav(3)/mstr1
         read (29) (opt_sed(i),opt_sed0(i),i=1,niw_opt)

         if (indx.eq.i_opt) then
            fmuopt(imod)=fmu
c     Normalise Optical SED by stellar mass of the model
            do i=1,niw_opt
               fopt(i)=opt_sed(i)/mstr1
               fopt0(i)=opt_sed0(i)/mstr1
            enddo
            ldust=ldtot/mstr1
            goto 2
         endif
      enddo

 2    if (int(fmu*1000).eq.int(fmu_aux*1000)
     +     .or.int(fmu*1000).eq.(int(fmu_aux*1000)-1)
     +     .or.int(fmu*1000).eq.(int(fmu_aux*1000)+1)) then
         write(*,*) 'optical... done'
      endif
      if (int(fmu*1000).ne.int(fmu_aux*1000)
     +     .and.int(fmu*1000).ne.(int(fmu_aux*1000)-1)
     +     .and.int(fmu*1000).ne.(int(fmu_aux*1000)+1) ) then
         call getenv('OPTILIBIS',infile1)
         close(29)
         open (29,file=infile1,status='old',form='unformatted')
         goto 7
      endif

c     Read Infrared SEDs and properties
      read (30) niw_ir,(wl_ir(i),i=1,niw_ir)
      do imod=1,50000
         read (30) (irprop(i),i=1,8)
         read (30) (ir_sed(i),i=1,niw_ir)
         fmuir(imod)=irprop(1)
         if (imod.eq.i_ir) then
            do i=1,niw_ir
               fir(i)=ir_sed(i)
            enddo
            goto 3
         endif
      enddo
 3    write(*,*) 'infrared... done'

      write(*,*) 'Ldust/L_sun= ',mstar*ldust

      write(31,315)
 315  format('#...fmu(Opt).....fmu(IR)....tform/yr.......gamma',
     +     '........Z/Zo........tauV..........mu.....M*/Msun',
     +     '....SFR(1e8).....Ld/Lsun')
      write(31,316) fmu,irprop(1),tform,gamma,zmet,tauv0,mu,mstar,
     +     sfrav(3),ldust*mstar
 316  format(0p2f12.3,1pe12.3,0p4f12.3,1p3e12.3)

      write(31,319)
      write(31,317)
 317  format('#...xi_C^ISM....T_W^BC/K...T_C^ISM/K...xi_PAH^BC',
     +     '...xi_MIR^BC.....xi_W^BC....Mdust/Mo')
      write(31,318) (irprop(k),k=2,7),irprop(8)*ldust*mstar
 318  format(0p6f12.3,1pe12.3)

      write(31,319)
 319  format('#')
      write(31,314)
 314  format('#...Spectral Energy Distribution [lg(L_lambda/LoA^-1)]:')
      write(31,312)
 312  format('#...lg(lambda/A)...Attenuated...Unattenuated')


c     Wavelength vectors are not the same for the Optical and IR spectra
c     Make new wavelength vector by combining them
      do i=1,6367
         wl(i)=wl_opt(i)
         fir_new(i)=0.
      enddo
      do i=6368,niw_tot
         wl(i)=wl_ir(i-6367)
         fir_new(i)=fir(i-6367)
      enddo

c     Interpolate the optical SED in the new wavelength grid (do it in log)
      do i=1,niw_opt
         fopt_aux(i)=log10(fopt(i))
         fopt_aux0(i)=log10(fopt0(i))
      enddo

      do i=1,niw_tot
         call interp(wl_opt,fopt_aux,niw_opt,4,wl(i),fopt_int(i))
         fopt_new(i)=10**(fopt_int(i))
         call interp(wl_opt,fopt_aux0,niw_opt,4,wl(i),fopt_int0(i))
         fopt_new0(i)=10**(fopt_int0(i))
      enddo

c     Final SEDs - write output file
      do i=1,niw_tot-1
         sedtot(i)=fopt_new(i)+ldust*fir_new(i)
         sedtot(i)=mstar*sedtot(i)
         fopt_new0(i)=fopt_new0(i)*mstar
         write(31,311) log10(wl(i)*(1.+z)),log10(sedtot(i)/(1.+z)),
     +        log10(fopt_new0(i)/(1.+z))
      enddo
 311  format(3f15.6)

 1    stop
      end

c     ===========================================================================
      SUBROUTINE INTERP(x,y,npts,nterms,xin,yout)
c     ---------------------------------------------------------------------------
c     INTERPOLATOR
c     description of parameters
c     x      - array of data points for independent variable
c     y      - array of data points for dependent variable
c     npts   - number of pairs of data points
c     nterms - number of terms in fitting polynomial
c     xin    - input value of x
c     yout   - interplolated value of y
c
c     comments
c     dimension statement valid for nterms up to 10
c     value of nterms may be modified by the program
c     ===========================================================================
      implicit real (a-h,o-z)
      integer npts
      dimension x(npts),y(npts)
      dimension delta(10),a(10)
c     search for appropriate value of x(1)
 11   do 19 i=1,npts
         if (xin-x(i)) 13,17,19
 13      i1 = i-nterms/2
         if (i1) 15,15,21
 15      i1 = 1
         go to 21
 17      yout = y(i)
 18      go to 61
 19   continue
      i1 = npts - nterms + 1
 21   i2 = i1 + nterms -1
      if (npts-i2) 23,31,31
 23   i2 = npts
      i1 = i2 - nterms +1
 25   if (i1) 26,26,31
 26   i1 = 1
 27   nterms = i2 - i1 + 1

c     evaluate deviations delta
 31   denom = x(i1+1) - x(i1)
      deltax = (xin-x(i1))/denom
      do 35 i=1,nterms
         ix = i1 + i - 1
 35      delta(i) = (x(ix)-x(i1))/denom

c     accumulate coefficients a
 40      a(1) = y(i1)
 41      do 50 k=2,nterms
            prod = 1.0
            sum = 0.0
            imax = k-1
            ixmax = i1 + imax
            do 49 i=1,imax
               j = k-i
               prod = prod*(delta(k)-delta(j))
 49            sum = sum - a(j)/prod
 50            a(k) = sum + y(ixmax)/prod

c     accumulate sum of expansion
 51            sum = a(1)
               do 57 j=2,nterms
                  prod = 1.0
                  imax = j-1
                  do 56 i=1,imax
 56                  prod = prod*(deltax-delta(i))
 57                  sum = sum + a(j)*prod
 60                  yout = sum

 61                  return
                     end



