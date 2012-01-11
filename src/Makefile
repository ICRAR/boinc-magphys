RM = /bin/rm -f
UTILIB = ./public_utilities.a
#FC =  g77 -ggdb -O0 -ffixed-line-length-132 -fbounds-check
FC = gfortran -std=legacy -ffixed-line-length-none

.f.o:
	$(FC) -c $<

make_zgrid: make_zgrid.f filter.dec $(UTILIB)
	$(FC) make_zgrid.f $(UTILIB) -o make_zgrid

get_optic_colors: get_optic_colors.f filter.dec $(UTILIB)
	$(FC) get_optic_colors.f $(UTILIB) -o get_optic_colors
	
get_infrared_colors: get_infrared_colors.f filter.dec $(UTILIB)
	$(FC) get_infrared_colors.f $(UTILIB) -o get_infrared_colors

fit_sed: fit_sed.f $(UTILIB)
	$(FC) fit_sed.f $(UTILIB) -o fit_sed
	
read_optilib_bin: read_optilib_bin.f $(UTILIB)
	$(FC) read_optilib_bin.f $(UTILIB) -o read_optilib_bin
	
read_irlib_bin: read_irlib_bin.f $(UTILIB)
	$(FC) read_irlib_bin.f $(UTILIB) -o read_irlib_bin		

clean:
	$(RM) public_utilities.a $(OBJFILES)

all:
	make public_utilities.a
	make make_zgrid get_optic_colors get_infrared_colors fit_sed
	make read_optilib_bin read_irlib_bin

#---------------------------------------------------------------------------
#commands to build library public_utilities.a
SRCFILES = make_zgrid.f get_optic_colors.f get_infrared_colors.f fit_sed.f read_optilib_bin.f read_irlib_bin.f

OBJFILES = make_zgrid.o get_optic_colors.o get_infrared_colors.o fit_sed.o read_optilib_bin.o read_irlib_bin.o

public_utilities.a: $(OBJFILES)
	ar ruv public_utilities.a $?
	ranlib public_utilities.a
