#! usr/local/bin/tcsh

set file=$USER_OBS

set n=`wc -l $file | awk '{print $1}'`
echo $n

set i = 1
while ($i < $n )
	echo $i | xargs -n 1 | ./fit_sed
	@ i = $i + 1
end
