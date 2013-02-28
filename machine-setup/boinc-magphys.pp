# BOINC & MAGPHYS
package { 'httpd':
    ensure => installed,
}
package { 'httpd-devel':
    ensure => installed,
}
package { 'autoconf':
    ensure => installed,
}
package { 'automake':
    ensure => installed,
}
package { 'binutils':
    ensure => installed,
}
package { 'gcc':
    ensure => installed,
}
package { 'gcc-c++':
    ensure => installed,
}
package { 'libstdc++46-static':
    ensure => installed,
}
package { 'gdb':
    ensure => installed,
}
package { 'libtool':
    ensure => installed,
}
package { 'make':
    ensure => installed,
}
package { 'gcc-gfortran':
    ensure => installed,
}
package { 'openssl':
    ensure => installed,
}
package { 'openssl-devel':
    ensure => installed,
}
package { 'mysql-devel':
    ensure => installed,
}
package { 'php':
    ensure => installed,
}
package { 'php-cli':
    ensure => installed,
}
package { 'php-gd':
    ensure => installed,
}
package { 'php-mysql':
    ensure => installed,
}
package { 'python-devel':
    ensure => installed,
}
package { 'python27':
    ensure => installed,
}
package { 'python27-devel':
    ensure => installed,
}
package { 'MySQL-python':
    ensure => installed,
}
package { 'subversion':
    ensure => installed,
}
package { 'rubygem-rake':
    ensure => installed,
}
package { 'mysql-server':
    ensure => installed,
}
package { 'mod_fcgid':
    ensure => installed,
}
package { 'php-fpm':
    ensure => installed,
}
package { 'postfix':
    ensure => installed,
}
package { 'ca-certificates':
    ensure => installed,
}

# Reporting and plotting
package { 'expect-devel':
    ensure => installed,
}
package { 'freetype-devel':
    ensure => installed,
}
package { 'freetype':
    ensure => installed,
}
package { 'libpng-devel':
    ensure => installed,
}
package { 'libpng':
    ensure => installed,
}

# NAGIOS
package { 'nrpe':
    ensure => installed,
}
package { 'nagios-common':
    ensure => installed,
}
package { 'nagios-plugins':
    ensure => installed,
}
package { 'nagios-plugins-all':
    ensure => installed,
}

# Create the apache user for the web site
user { 'apache':
  ensure  => present,
  groups => ['ec2-user'],
}

service { 'httpd':
    ensure => running,
    enable => true,
    require => Package['httpd'],
}


# Where the raw galaxies will reside
file { "/home/ec2-user/galaxies":
    ensure => "directory",
    owner  => ec2-user,
    group  => ec2-user,
    mode   => 775,
}

# Where the BOINC code will reside
file { "/home/ec2-user/boinc":
    ensure => "directory",
    owner  => ec2-user,
    group  => ec2-user,
    mode   => 775,
}

# When we generate an image this is where it goes
file { "/home/ec2-user/galaxyImages":
    ensure => "directory",
    owner  => ec2-user,
    group  => ec2-user,
    mode   => 775,
}

# Where the output fits files go if generated
file { "/home/ec2-user/output_fits":
    ensure => "directory",
    owner  => ec2-user,
    group  => ec2-user,
    mode   => 775,
}

# Where the HDF5 archive files go
file { "/home/ec2-user/archive":
    ensure => "directory",
    owner  => ec2-user,
    group  => ec2-user,
    mode   => 775,
}
