# vlm.py
# 
# Created:  Your Name, Dec 2013
# Modified:         

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# suave imports
from SUAVE.Attributes.Gases import Air # you should let the user pass this as input
air = Air()
compute_speed_of_sound = air.compute_speed_of_sound

# python imports
import os, sys, shutil
from copy import deepcopy
from warnings import warn

# package imports
import numpy as np
import scipy as sp

def weissinger_vortex_lattice(conditions,configuration,wing):
    """ SUAVE.Methods.Aerodynamics.Pass_fidelity.vlm(conditions,configuration,geometry)
        Vortex lattice method to compute the lift coefficient and induced drag component

        Inputs:
            wing - geometry dictionary with fields:
                Sref - reference area

        Outputs:

        Assumptions:
        
    """

    #unpack
    
    
    
    span       = wing.span
    root_chord = wing.chord_root
    tip_chord  = wing.chord_tip
    sweep      = wing.sweep
    taper      = wing.taper
    twist_rc   = wing.twist_rc
    twist_tc   = wing.twist_tc
    sym_para   = wing.symmetric
    AR         = wing.ar
    Sref       = wing.sref
    orientation = wing.vertical

    n  = configuration.number_panels_spanwise
    nn = configuration.number_panels_chordwise

    # conditions
    aoa = conditions.aerodynamics.angle_of_attack
    
    # chord difference
    dchord=(root_chord-tip_chord)
    if sym_para is True :
        span=span/2
    deltax=span/n



    if orientation == False :

        section_length= np.empty(n)
        area_section=np.empty(n)
        sl=np.empty(n)
    
        xpos=np.empty(n)
    
        ya=np.empty(n)
        yb=np.empty(n)
        xa=np.empty(n)
        yab=np.empty(n)
        ybb=np.empty(n)
        y2=np.empty(n)   
    
        x=np.empty(n)
        y=np.empty(n)
        twist_distri=np.empty(n)
        xloc_leading=np.empty(n)
        xloc_trailing=np.empty(n)  
        RHS=np.empty([n,1])
        w=np.empty([n,n])
        wb=np.empty([n,n])
        A=np.empty([n,n])
        L=np.empty(n)
        T=np.empty(n)
    
        A_v=np.empty([n,n])
        v=np.empty(n)
    
        Lfi=np.empty(n)
        Lfk=np.empty(n)
    
        Lft=np.empty(n)
        Dg=np.empty(n)   
        D=np.empty(n)    
    
    
    
    
        #--discretizing the wing sections into panels--------------------------------
        for i in range(0,n):
    
            section_length[i]= dchord/span*(span-(i+1)*deltax+deltax/2) + tip_chord
            area_section[i]=section_length[i]*deltax
            sl[i]=section_length[i]
            twist_distri[i]=twist_rc + i/float(n)*(twist_tc-twist_rc)
            xpos[i]=(i)*deltax
    
            ya[i]=(i)*deltax
            yb[i]=(i+1)*deltax
            xa[i]=((i+1)*deltax-deltax/2)*np.tan(sweep)+ 0.25*sl[i]
    
            x[i]=((i+1)*deltax-deltax/2)*np.tan(sweep) + 0.75*sl[i]
            y[i]=((i+1)*deltax-deltax/2)
            xloc_leading[i]=((i+1)*deltax)*np.tan(sweep)
            xloc_trailing[i]=((i+1)*deltax)*np.tan(sweep)+sl[i]
    
    
        #------Influence coefficient computation-----------------------
        for i in range(0,n):
    
            RHS[i,0]=np.sin(twist_distri[i]+aoa)  #)
            #RHS[i,0]=Vinf*np.sin(twist_distri[i]+aoa)  #)
    
            for j in range(0,n):
    
    
                yad=y[i]-ya[j]
                xd=x[i]-xa[j]
                ybd=y[i]-yb[j]
    
                yadd=y[i]-yab[j]
                ybdd=y[i]-ybb[j]
    
    
                A[i,j]=whav(x[i],y[i],xa[j],ya[j])-whav(x[i],y[i],xa[j],yb[j])-whav(x[i],y[i],xa[j],-ya[j])+whav(x[i],y[i],xa[j],-yb[j])
                A[i,j]=A[i,j]*0.25/np.pi
    
        #---------------Vortex strength computation by matrix inversion-----------
        T=np.linalg.solve(A,RHS)
        
        #---Calculating the effective velocty--------------------------
        for i in range(0,n):
            v[i]=0.0      
            for j in range(0,n):
    
                A_v[i,j]=whav(xa[i],y[i],xa[j],ya[j])-whav(xa[i],y[i],xa[j],yb[j])-whav(xa[i],y[i],xa[j],-ya[j])+whav(xa[i],y[i],xa[j],-yb[j])
                A_v[i,j]=A[i,j]*0.25/np.pi*T[j]
                v[i]=v[i]+A_v[i,j]
    
    
            #Lfi[i]=-T[i]*(Vinf*np.sin(twist_tc)-v[i])
            #Lfk[i]=T[i]*Vinf*np.cos(twist_tc)
            
            Lfi[i]=-T[i]*(np.sin(twist_tc)-v[i])
            Lfk[i]=T[i]*np.cos(twist_tc)        
    
            Lft[i]=(-Lfi[i]*np.sin(twist_tc)+Lfk[i]*np.cos(twist_tc))
            Dg[i]=(Lfi[i]*np.cos(twist_tc)+Lfk[i]*np.sin(twist_tc))
    
        #---------Lift computation from elements---------------------------------
        LT=0.0
        DT=0.0
        arsec=0.0
    
        for i in range(0,n):
    
            L[i]=deltax*Lft[i]   #T(i)*v(i)*sin(alpha)
            D[i]=deltax*Dg[i]    
    
            LT=LT+L[i]
            DT=DT+D[i]
    
            arsec=arsec+area_section[i]
    
    
        # compute lift and drag coefficients
        #Cl=2*LT/(0.5*roc*Vinf**2*Sref)
        #Cd=2*DT/(0.5*roc*Vinf**2*Sref)       
    
        Cl=2*LT/(0.5*Sref)
        Cd=2*DT/(0.5*Sref)     
    
    else:
        
        Cl= 0.0
        Cd= 0.0         


    return Cl , Cd



# ----------------------------------------------------------------------
#   Helper Functions
# ----------------------------------------------------------------------
def whav(x1,y1,x2,y2):
    """ Helper function of vortex lattice method      
        Inputs:
            x1,x2 -x coordinates of bound vortex
            y1,y2 -y coordinates of bound vortex

        Sref - reference area for non dimensionalization
        Outpus:
            Cl_comp - lift coefficient
            Cd_comp - drag  coefficient       

        Assumptions:
            if needed

    """  


    if x1==x2:
        whv=1/(y1-y2)
    else:  
        whv=1/(y1-y2)*(1+ (np.sqrt((x1-x2)**2+(y1-y2)**2)/(x1-x2)))

    return whv