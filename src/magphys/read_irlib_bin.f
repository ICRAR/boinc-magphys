      PROGRAM READ_IRLIB_BIN

c     Reads the binary file containing the library of dust emission spectra

      implicit none
      character infile*80
      integer i,imod,k,niw
      real wl(6450),irsed(6450)
      real fmu,xic_ism,tw_bc,tc_ism,xipah_bc
      real ximir_bc,xiw_bc,mdust

c	SEDs
c       niw: number of wavelength points
c       wl: wavelength (in A)
c       irsed: attenuated stellar spectrum (L_lambda in L_sun/A)

c       MODEL PARAMETERS:
c       fmu: fraction of total luminosity of dust contributed by the diffuse ISM
c       xic_ism: contribution of cold dust to the dust luminosity of the ISM
c       tw_bc: equilibrium temperature of warm dust in birth clouds
c       tc_ism: equilibrium temperature of cold dust in the diffuse ISM
c       xipah_bc: contribution of PAHs to the dust luminosity of the birth clouds
c       ximir_bc: contribution of mid-infrared continuum to the dust luminosity of the birth clouds
c       xiw_bc: contribution of warm dust in thermal equilibrium to the dust luminosity of the birth clouds
c       mdust: dust mass

        call getenv('IRLIB',infile)
        close (29)
        open (29,file=infile,status='old',form='unformatted')


        read(29) niw,(wl(i),i=1,niw)
        write (*,*)  'Number of wavelength points = ',niw
        do imod=1,25000
                 read(29) fmu,xic_ism,tw_bc,tc_ism,xipah_bc,
     +                    ximir_bc,xiw_bc,mdust
                 read(29) (irsed(i),k=i,niw)
        enddo

 1      stop
        end
