
# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# python imports
import numpy as np

# SUAVE imports
from Unknown_Throttle import Unknown_Throttle

# import units
from SUAVE.Attributes import Units
km = Units.km
hr = Units.hr
deg = Units.deg

# ----------------------------------------------------------------------
#  Class
# ----------------------------------------------------------------------

class Linear_Speed_Constant_Rate(Unknown_Throttle):

    # ------------------------------------------------------------------
    #   Data Defaults
    # ------------------------------------------------------------------  
    
    def __defaults__(self):
        self.tag = 'Constant Mach, Constant Altitude Cruise'
        
        # --- User Inputs
        
        self.altitude_start = None # Optional
        self.altitude_end   = 10. * km
        self.climb_rate     = 3.  * Units.m / Units.s
        self.air_speed_start      = 100 * Units.m / Units.s
        self.air_speed_end        = 200 * Units.m / Units.s
        
        return

    # ------------------------------------------------------------------
    #   Methods For Initialization
    # ------------------------------------------------------------------  
    
    def check_inputs(self):
        """ Segment.check():
            error checking of segment inputs
        """
        
        ## CODE
        
        return

    def initialize_conditions(self,conditions,numerics,initials=None):
        
        # initialize time and mass
        # initialize altitude, atmospheric conditions,
        # climb segments are discretized on altitude
        conditions = Unknown_Throttle.initialize_conditions(self,conditions,numerics,initials)
        
        # unpack user inputs
        Vo   = self.air_speed_start
        Vf   = self.air_speed_end
        climb_rate  = self.climb_rate
        
        # process velocity vector
        v_mag = (Vf-Vo)*numerics.dimensionless_time + Vo
        v_z   = -climb_rate # z points down
        v_x   = np.sqrt( v_mag**2 - v_z**2 )
        conditions.frames.inertial.velocity_vector[:,0] = v_x[:,0]
        conditions.frames.inertial.velocity_vector[:,2] = v_z
        
        # freestream conditions
        # freestream.velocity, dynamic pressure, mach number, ReL
        conditions = self.compute_freestream(conditions)
        
        return conditions
        
