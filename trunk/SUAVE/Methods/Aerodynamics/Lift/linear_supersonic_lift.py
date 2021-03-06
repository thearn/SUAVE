# linear_supersonic_lift.py
# 
# Created:  Tim MacDonald 7/1/14
# Modified: Tim MacDonald 7/14/14
#
# Adapted from vortex lattice code to strip theory

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

def linear_supersonic_lift(conditions,configuration,wing):
    """ Computes lift using linear supersonic theory

        Inputs:
            wing - geometry dictionary with fields:
            Sref - reference area

        Outputs:
            Cl - lift coefficient

        Assumptions:
            - Reference area of the passed wing is the desired 
            reference area for Cl
            - Compressibility effects are not handled
        
    """

    # Unpack
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

    aoa = conditions.aerodynamics.angle_of_attack
    
    n  = configuration.number_panels_spanwise
    
    # chord difference
    dchord=(root_chord-tip_chord)
    
    # Check if the wing is symmetric
    # If so, reduce the span by half for calculations
    if sym_para is True :
        span=span/2
        
    # Width of strips
    deltax=span/n

    if orientation == False : # No lift for vertical surfaces

        # Intialize arrays with number of strips
        section_length= np.empty(n)
        area_section=np.empty(n)
        twist_distri=np.empty(n)
        
        # Discretize the wing sections into strips
        for i in range(0,n):
    
            section_length[i]= dchord/span*(span-(i+1)*deltax+deltax/2) + tip_chord
            area_section[i]=section_length[i]*deltax
            twist_distri[i]=twist_rc + i/float(n)*(twist_tc-twist_rc)
        
        # Initialize variables
        area_tot = 0.0        
        cl_tot_base = 0.0
        cl = np.array([0.0]*n)
        
        for j in range(0,n):
            # Note that compressibility effects are not included here
            cl[j] = 4*(aoa-twist_distri[j])*area_section[j]
            area_tot = area_tot+area_section[j]
            cl_tot_base = cl_tot_base + cl[j]
    
        Cl=cl_tot_base/area_tot # Lift 
    
    else:
        
        Cl= 0.0       


    return Cl