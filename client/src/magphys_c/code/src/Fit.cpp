/*
 *    (c) UWA, The University of Western Australia
 *    M468/35 Stirling Hwy
 *    Perth WA 6009
 *    Australia
 *
 *    Copyright by UWA, 2012-2013
 *    All rights reserved
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
 *    MA 02111-1307  USA
 */

#include <iostream>
using std::cerr;
using std::cout;
using std::endl;

#include <cmath>
#include <fstream>
#include <boost/algorithm/string.hpp>
#include "Fit.hpp"

namespace magphys {

    Fit::~Fit() {
        // Clean up
    }

    void Fit::initialise() {
        // {F77} c     COMPUTE LUMINOSITY DISTANCE from z given cosmology
        // {F77} c     Obtain cosmological constant and q
        // {F77}       clambda=cosmol_c(h,omega,omega_lambda,q)
        cosmol_c();
        
        // {F77} c     Compute distance in Mpc from the redshifts z
        // 
        calculateDistance();
    }
    
    void Fit::fit() {
        
    }
    
    /*
     * Compute q
     */
    void Fit::cosmol_c() {
        // {F77} c     ===========================================================================
        // {F77}       REAL*8 FUNCTION COSMOL_C(h,omega,omega_lambda,q)
        // {F77} c     ---------------------------------------------------------------------------
        // {F77} c     Returns cosmological constant = cosmol_c and parameter q
        // {F77} c
        // {F77} c     Omega is entered by the user
        // {F77} c     omega=1.-omega_lambda
        // {F77} c     ===========================================================================
        if(omega_lambda_ == 0) {
            q_ = omega_ / 2;
        } else {
            q_ = (3 * omega_ / 2) - 1;
        }
        omega0_ = (2 * (q_ + 1)) / 3;
    }
    
    void Fit::calculateDistance() {
        // {F77} c     Compute distance in Mpc from the redshifts z
        // {F77}       dist(i_gal)=dl(h,q,redshift(i_gal))
        // {F77}       dist(i_gal)=dist(i_gal)*3.086e+24/dsqrt(1.+redshift(i_gal))
        dist_ = get_dl() * (3.086e+24) / sqrt(1 + redshift_);
    }
    
    double Fit::get_dl() {
        // {F77}
        // {F77}
        // {F77} c     ===========================================================================
        // {F77}       REAL*8 FUNCTION DL(h,q,z)
        // {F77} c     ---------------------------------------------------------------------------
        // {F77} c     Computes luminosity distance corresponding to a redshift z.
        // {F77} c     Uses Mattig formulae for qo both 0 and non 0
        // {F77} c     Revised January 1991 to implement cosmolgical constant
        // {F77} c     Ho in km/sec/Mpc, DL is in Mpc
        // {F77} c     ===========================================================================
        // {F77}       implicit none
        // {F77}       real*8 h, q, z, d1, d2
        // {F77}       real*8 aa, bb, epsr, s, s0, funl
        // {F77}       real*8 dd1, dd2, omega0
        // {F77}       logical success
        // {F77}       integer npts
        // {F77}       external funl
        // {F77}       common /cosm/ omega0
        // {F77}
        // {F77}       if (z.le.0.) then
        // {F77}          dl=1.e-5               !10 pc
        // {F77}          return
        // {F77}       endif
        // {F77}
        // {F77}       if (q .eq. 0) then
        // {F77}          dl = ((3.e5 * z) * (1 + (z / 2.))) / h
        // {F77}       else if (q .gt. 0.) then
        // {F77}          d1 = (q * z) + ((q - 1.) * (sqrt(1. + ((2. * q) * z)) - 1.))
        // {F77}          d2 = ((h * q) * q) / 3.e5
        // {F77}          dl = d1 / d2
        // {F77}       else if (q .lt. 0.) then
        // {F77}          omega0 = (2. * (q + 1.)) / 3.
        // {F77}          aa = 1.
        // {F77}          bb = 1. + z
        // {F77}          success=.false.
        // {F77}          s0=1.e-10
        // {F77}          npts=0
        // {F77}          do while (.not.success)
        // {F77}             npts=npts+1
        // {F77}             call midpnt(funl,aa,bb,s,npts)
        // {F77}             epsr=abs(s-s0)/s0
        // {F77}             if (epsr.lt.1.e-4) then
        // {F77}                success=.true.
        // {F77}             else
        // {F77}                s0=s
        // {F77}             endif
        // {F77}          enddo
        // {F77}          dd1=s
        // {F77}     dd2 = (3.e5 * (1. + z)) / (h * sqrt(omega0))
        // {F77}     dl = dd1 * dd2
        // {F77}       end if
        // {F77}
        // {F77}       return
        // {F77}       end
        double dl = 0;
        double s = 0;
        
        if(redshift_ <= 0) {
            return (1.0e-5);
        }
        
        if(q_ == 0) {
            dl = ((3.0e5 * redshift_) * (1 + (redshift_ / 2))) / h_;
        } 
        else if(q_ > 0) {
            double d1 = (q_ * redshift_) + ((q_ - 1) * (sqrt(1 + ((2 * q_) * redshift_)) - 1));
            double d2 = ((h_ * q_) * q_) / 3.0e5;
            dl = d1 / d2;
        } 
        else if(q_ < 0) {
            double aa = 1;
            double bb = 1 + redshift_;
            bool success = false;
            double s0 = 1.0e-10;
            int npts = 0;
            do {                
                npts++;
                s = get_midpnt(aa, bb, s, npts);
                double epsr = fabs(s - s0) / s0;
                if(epsr < 1.0e-4) {
                    success = true;
                } else {
                    s0 = s;
                }
            } while(!success);
            double dd1 = s;
            double dd2 = (3.0e5 * (1 + redshift_)) / (h_ * sqrt(omega0_));
            dl = dd1 * dd2;
        }
        return dl;        
    }
    
    double Fit::get_funl(double x) {
        // {F77}
        // {F77} c     ===========================================================================
        // {F77}       REAL*8 FUNCTION FUNL(x)
        // {F77} c     ---------------------------------------------------------------------------
        // {F77} c     For non-zero cosmological constant
        // {F77} c     ===========================================================================
        // {F77}       real*8 x, omega0, omegainv
        // {F77}       common /cosm/ omega0
        // {F77}       omegainv = 1. / omega0
        // {F77}       funl = 1. / sqrt(((x ** 3.) + omegainv) - 1.)
        // {F77}       return
        // {F77}       end
        double omegainv = 1 / omega0_;
        return (1 / sqrt(((x * x * x) + omegainv) - 1));
    }

    
    double Fit::get_midpnt(double a, double b, double s, double n) {
        // {F77}
        // {F77}
        // {F77} c     ===========================================================================
        // {F77}       SUBROUTINE MIDPNT(func,a,b,s,n)
        // {F77} c     ===========================================================================
        // {F77}       INTEGER n
        // {F77}       REAL*8 a,b,s,func
        // {F77}       EXTERNAL func
        // {F77}       INTEGER it,j
        // {F77}       REAL*8 ddel,del,sum,tnm,x
        // {F77}       if (n.eq.1) then
        // {F77}          s=(b-a)*func(0.5*(a+b))
        // {F77}       else
        // {F77}          it=3**(n-2)
        // {F77}          tnm=it
        // {F77}          del=(b-a)/(3.*tnm)
        // {F77}          ddel=del+del
        // {F77}          x=a+0.5*del
        // {F77}          sum=0.
        // {F77}          do 11 j=1,it
        // {F77}             sum=sum+func(x)
        // {F77}             x=x+ddel
        // {F77}             sum=sum+func(x)
        // {F77}             x=x+del
        // {F77}  11      continue
        // {F77}          s=(s+(b-a)*sum/tnm)/3.
        // {F77}       endif
        // {F77}       return
        // {F77}       END
        double result;
        if(n == 1) {
            result = (b - a) * get_funl(0.5 * (a + b));
        } else {
            int it = pow(3, (n - 2));
            double tnm = it;
            double del = (b - a) / (3 * tnm);
            double ddel = del + del;
            double x = a + 0.5 * del;
            double sum = 0;
            for(int j = 0; j < it; j++) {
                sum = sum + get_funl(x);
                x = x + ddel;
                sum = sum + get_funl(x);
                x = x + del;
            }
            result = (s + (b - a) * sum / tnm) / 3;
        }
        return result;
    }

}
