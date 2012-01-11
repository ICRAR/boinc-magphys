 	PROGRAM READ_OPTILIB_BIN

c       Reads the binary file containing the library of stellar spectra

	implicit none
        character infile*80
        integer niw,nage
        integer i,imod,nburst
        real tform,gamma,zmet,tauv0,mu,mstr1,mstr0,mstry
	real tlastburst,age_wm,age_wr
        real fmu,ldtot,fbc,aux,lha,lhb
	real wl(6918),fprop(6918),fprop0(6918)
        real age(1000),sfr(1000)
        real fburst(5),ftot(5),sfrav(5)

c	SEDs
c       niw: number of wavelength points
c       wl: wavelength (in A)
c       fprop: attenuated stellar spectrum (L_lambda in L_sun/A)
c       fprop0: unattenuated stellar spectrum (L_lambda in L_sun/A)

c       MODEL PARAMETERS:
c       tform: age of the galaxy (in yr)
c       gamma: star formation timescale (in Gyr^-1)
c       zmet: metallicity (in solar units)
c       tauv0: total V-band optical depth seen by young stars in birth clouds
c       mu: fraction of tauv0 contributed by the ambient (diffuse) ISM
c       nburst: number of random bursts
c       mstr1: effective stellar mass
c       mstr0: total mass of stars formed
c       mstry: mass of stars in birth clouds
c       tlastburst: time of last burst of star formation
c       fburst: fraction of total stellar mass formed in bursts
c       age_wm: mass weighted age
c       age_wr: r-band weighted age
c       lha: H-alpha line luminosity
c       lhb: H-beta line luminosity
c       ldtot: total luminosity absorbed by dust (birth clouds + ambient ISM)
c       fmu: fraction of total dust luminosity contributed by the ambient ISM
c       fbc: fraction of total V-band effective optical depth in the birth clouds
c            contributed by dust in the HII region


c       STAR FORMATION HISTORY
c       nage: number of time steps
c       age: age of the galaxy
c       sfr: star formation rate (function of age)
c       sfrav: star formation rate averaged over 1e+6, 1e+7, 1e+8, 1e+9 and 2e+9 yrs

	call getenv('OPTILIB',infile)
  
        close (29)
        open (29,file=infile,status='old',form='unformatted')

        read (29) niw,(wl(i),i=1,niw)
        write (*,*)  'Number of wavelength points = ',niw
        do imod=1,25000
              read (29,end=1) tform,gamma,zmet,tauv0,mu,nburst,
     .                     mstr1,mstr0,mstry,tlastburst,
     .                     (fburst(i),i=1,5),(ftot(i),i=1,5),
     .			   age_wm,age_wr,aux,aux,aux,aux,
     .                     lha,lhb,aux,aux,ldtot,fmu,fbc
              read (29) nage,(age(i),sfr(i),i=1,nage),(sfrav(i),i=1,5)
	      read (29) (fprop(i),fprop0(i),i=1,niw)
        enddo	   

1       stop
	end
