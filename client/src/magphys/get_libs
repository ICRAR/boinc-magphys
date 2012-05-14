#! usr/local/bin/tcsh

set file='zlibs.dat'

foreach line (`awk ' {print $1";"$2}' $file`)

   set z=`echo $line | awk 'BEGIN {FS=";"} {print $2}'`

   echo $z "70.,0.30,0.70" | xargs -n 1 | ./get_optic_colors

   echo $z "70.,0.30,0.70" | xargs -n 1 | ./get_infrared_colors
   
end
