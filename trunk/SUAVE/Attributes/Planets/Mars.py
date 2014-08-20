# Constants.py: Physical constants and helepr functions
# 
# Created By:       J. Sinsay
# Updated:          M. Colonno   04/09/2013
#                   T. Lukaczyk  06/23/2013

""" SUAVE Data Class for Constants """

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# classes
from Planet import Planet
from SUAVE.Attributes.Constants import Composition

# ----------------------------------------------------------------------
#  Mars 
# ----------------------------------------------------------------------
     
class Mars(Planet):
    """ Physical constants specific to Mars and Mars' atmosphere """
    def __defaults__(self):
        self.mass              = 6.4174e24  kg  # kg
        self.mean_radius       = 3.3895e6  # m
        self.sea_level_gravity = 3.71  # m/s^2   

