# Fidelity_Zero.py
# 
# Created:  Andrew, July 2014
# Modified:        


# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# SUAVE imports

import SUAVE

from SUAVE.Structure import Data
from SUAVE.Attributes import Units

# import methods
from SUAVE.Methods.Flight_Dynamics.Static_Stability.Approximations.Tube_Wing.taw_cmalpha import taw_cmalpha
from SUAVE.Methods.Flight_Dynamics.Static_Stability.Approximations.Tube_Wing.taw_cnbeta import taw_cnbeta
from SUAVE.Methods.Flight_Dynamics.Static_Stability.Approximations.datcom import datcom
from SUAVE.Methods.Flight_Dynamics.Dynamic_Stability import Approximations as Approximations
from SUAVE.Methods.Flight_Dynamics.Dynamic_Stability import Full_Linearized_Equations as Full_Linearized_Equations
from SUAVE.Methods.Flight_Dynamics.Dynamic_Stability.Full_Linearized_Equations import Supporting_Functions as Supporting_Functions


# python imports
import os, sys, shutil
from copy import deepcopy
from warnings import warn

# package imports
import numpy as np
import scipy as sp

# ----------------------------------------------------------------------
#  Class
# ----------------------------------------------------------------------

class Fidelity_Zero(Data):
    """ SUAVE.Attributes.Aerodynamics.Fidelity_Zero
        aerodynamic model that builds a surrogate model for clean wing 
        lift, using vortex lattic, and various handbook methods
        for everything else
        
        this class is callable, see self.__call__
        
    """
    
    def __defaults__(self):
        
        # Initialize quantities
        
        self.configuration = Data()
        self.geometry      = Data()
        
        return
    
    def initialize(self,vehicle):
                        
        # unpack
        geometry         = self.geometry
        configuration    = self.configuration
        
        # copy geometry
        for k in ['Fuselages','Wings','Propulsors']:
            geometry[k] = deepcopy(vehicle[k])
        
        # reference area
        geometry.reference_area = vehicle.S
        configuration.mass_props = vehicle.Mass_Props
        
    
    def __call__(self,conditions):
            """ process vehicle to setup geometry, condititon and configuration
                
                Inputs:
                    conditions - DataDict() of aerodynamic conditions
                    results - DataDict() of 
                    
                Outputs:

                    
                Assumptions:

                    
            """
            
            # unpack
            configuration = self.configuration
            geometry      = self.geometry
            q             = conditions.freestream.dynamic_pressure
            Sref          = geometry.reference_area    
            mach          = conditions.freestream.mach_number
            velocity      = conditions.freestream.velocity
            density       = conditions.freestream.density
            Span          = geometry.Wings['Main Wing'].span
            mac           = geometry.Wings['Main Wing'].chord_mac
            aero          = conditions.aerodynamics
            
            # Calculate CL_alpha 
            if not conditions.has_key('lift_curve_slope'):
                conditions.lift_curve_slope = (datcom(geometry.Wings['Main Wing'],mach))
            
            # Calculate change in downwash with respect to change in angle of attack
            for surf in geometry.Wings:
                e = surf.e
                sref = surf.sref
                span = (surf.ar * sref ) ** 0.5
                surf.CL_alpha = datcom(surf,mach)
                surf.ep_alpha = Supporting_Functions.ep_alpha(surf.CL_alpha, sref, span, e)
            
            # Static Stability Methods
            aero.cm_alpha = taw_cmalpha(geometry,mach,conditions,configuration)
            aero.cn_beta = taw_cnbeta(geometry,conditions,configuration)
            
            if np.count_nonzero(configuration.mass_props.I_cg) > 0:         
                # Dynamic Stability Approximation Methods
                if not aero.has_key('cn_r'):  
                    cDw = aero.drag_breakdown.parasite['Main Wing'].parasite_drag_coefficient # Might not be the correct value
                    l_v = geometry.Wings['Vertical Stabilizer'].origin[0] + geometry.Wings['Vertical Stabilizer'].aero_center[0] - geometry.Wings['Main Wing'].origin[0] - geometry.Wings['Main Wing'].aero_center[0]
                    aero.cn_r = Supporting_Functions.cn_r(cDw, geometry.Wings['Vertical Stabilizer'].sref, Sref, l_v, span, geometry.Wings['Vertical Stabilizer'].eta, geometry.Wings['Vertical Stabilizer'].CL_alpha)
                if not aero.has_key('cl_p'):
                    aero.cl_p = 0 # Need to see if there is a low fidelity way to calculate cl_p
                    
                if not aero.has_key('cl_beta'):
                    aero.cl_beta = 0 # Need to see if there is a low fidelity way to calculate cl_beta
                
                l_t = geometry.Wings['Horizontal Stabilizer'].origin[0] + geometry.Wings['Horizontal Stabilizer'].aero_center[0] - geometry.Wings['Main Wing'].origin[0] - geometry.Wings['Main Wing'].aero_center[0] #Need to check this is the length of the horizontal tail moment arm       
                
                if not aero.has_key('cm_q'):
                    aero.cm_q = Supporting_Functions.cm_q(conditions.lift_curve_slope, l_t,mac) # Need to check Cm_i versus Cm_alpha
                
                if not aero.has_key('cm_alpha_dot'):
                    aero.cm_alpha_dot = Supporting_Functions.cm_alphadot(aero.cm_alpha, geometry.Wings['Horizontal Stabilizer'].ep_alpha, l_t, mac) # Need to check Cm_i versus Cm_alpha
                    
                if not aero.has_key('cz_alpha'):
                    aero.cz_alpha = Supporting_Functions.cz_alpha(aero.drag_coefficient,conditions.lift_curve_slope)                   
                
                conditions.dutch_roll = Approximations.dutch_roll(velocity, aero.cn_beta, Sref, density, Span, configuration.mass_props.I_cg[2][2], aero.cn_r)
                
                if aero.cl_p != 0:                 
                    roll_tau = Approximations.roll(configuration.mass_props.I_cg[2][2], Sref, density, velocity, Span, aero.cl_p)
                    if aero.cl_beta != 0:
                        aero.cy_phi = Supporting_Functions.cy_phi(aero.lift_coefficient)
                        aero.cl_r = Supporting_Functions.cl_r( aero.lift_coefficient) # Will need to be changed
                        spiral_tau = Approximations.spiral(conditions.weights.total_mass, velocity, density, Sref, aero.cl_p, aero.cn_beta, aero.cy_phi, aero.cl_beta, aero.cn_r, aero.cl_r)
                conditions.short_period = Approximations.short_period(velocity, density, Sref, mac, aero.cm_q, aero.cz_alpha, conditions.weights.total_mass, aero.cm_alpha, configuration.mass_props.I_cg[1][1], aero.cm_alpha_dot)
                conditions.phugoid = Approximations.phugoid(conditions.freestream.gravity, conditions.freestream.velocity, aero.drag_coefficient, aero.lift_coefficient)
                
                # Dynamic Stability Full Linearized Methods
                if aero.has_key('cy_beta') and aero.cl_p != 0 and aero.cl_beta != 0:
                    if not aero.has_key('cy_psi'):
                        theta = conditions.frames.wind.body_rotations[:,1]
                        aero.cl_psi = Supporting_Functions.cy_psi(aero.lift_coefficient, theta)                     
                    if not aero.has_key('cz_u'):
                        if not aero.has_key('cL_u'):
                            aero.cL_u = 0
                        aero.cz_u = Supporting_Functions.cz_u(aero.lift_coefficient,velocity,aero.cL_u)
                    if not aero.has_key('cz_alpha_dot'):
                        aero.cz_alpha_dot = Supporting_Functions.cz_alphadot(aero.cm_alpha, geometry.Wings['Horizontal Stabilizer'].ep_alpha)
                    if not aero.has_key('cz_q'):
                        aero.cz_q = Supporting_Functions.cz_q(aero.cm_alpha)
                    if not aero.has_key('cx_u'):
                        aero.cx_u = Supporting_Functions.cx_u(aero.drag_coefficient)
                    if not aero.has_key('cx_alpha'):
                        aero.cx_alpha = Supporting_Functions.cx_alpha(aero.lift_coefficient, conditions.lift_curve_slope)
                
                    lateral_directional = Full_Linearized_Equations.lateral_directional(velocity, aero.cn_beta , Sref, density, Span, configuration.mass_props.I_cg[2][2], aero.cn_r, configuration.mass_props.I_cg[0][0], aero.cl_p, configuration.mass_props.I_cg[0][2], aero.cl_r, aero.cl_beta, aero.cn_p, aero.cy_phi, aero.cy_psi, aero.cy_beta, conditions.weights.total_mass)
                    longitudinal = Full_Linearized_Equations.longitudinal(velocity, density, Sref, mac, aero.cm_q, aero.cz_alpha, conditions.weights.total_mass, aero.cm_alpha, configuration.mass_props.I_cg[1][1], aero.cm_alpha_dot, aero.cz_u, aero.cz_alpha_dot, aero.cz_q, -aero.lift_coefficient, theta, aero.cx_u, aero.cx_alpha)
            
            return 