""" Vehicle.py: SUAVE Vehicle container class with database + input / output functionality """

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

from SUAVE.Structure import Data, Container, Data_Exception, Data_Warning
from SUAVE import Components
from SUAVE.Components import Component_Exception
from SUAVE.Methods.Utilities import switch

from copy import deepcopy

# ----------------------------------------------------------------------
#  Vehicle Data Class
# ----------------------------------------------------------------------

class Vehicle(Data):
    ''' SUAVE.Vehicle(**kwarg)
        Arbitrary Vehicle Initialization

        Inputs:
            optional, dictionary of data for initialization

    '''

    def __defaults__(self):
        self.tag = 'Vehicle'
        self.Fuselages  = Components.Fuselages.Fuselage.Container()
        self.Wings      = Components.Wings.Wing.Container()
        self.Propulsors = Components.Propulsors.Propulsor.Container()
        self.Energy     = Components.Energy.Energy()
        self.Systems    = Components.Systems.System.Container()
        self.Mass_Props = Components.Mass_Props()
        self.Cost       = Components.Cost()
        self.Envelope   = Components.Envelope()
        self.Configs    = ConfigContainer()

        self.max_lift_coefficient_factor = 1.0

        # Temporary
        self.PASS       = Components.Component()

    _component_root_map = None

    def __init__(self,*args,**kwarg):
        # will set defaults
        super(Vehicle,self).__init__(*args,**kwarg)

        self._component_root_map = {
            Components.Fuselages.Fuselage              : self['Fuselages']              ,
            Components.Wings.Wing                      : self['Wings']                  ,
            Components.Systems.System                  : self['Systems']                ,
            Components.Cost                            : self['Cost']                   ,
            Components.Propulsors.Propulsor            : self['Propulsors']             ,
            Components.Energy.Storages.Storage         : self['Energy']['Storages']     ,
            Components.Energy.Distributors.Distributor : self['Energy']['Distributors'] ,
            Components.Energy.Converters.Converter     : self['Energy']['Converters']   ,
            Components.Energy.Networks.Network         : self['Energy']['Networks']     ,
            #Components.Mass_Props                      : self['Mass_Props']             ,
            #Components.Envelope                        : self['Envelope']               ,
            #Components.PASS                            : self['PASS']                   ,
        }

        return

    def find_component_root(self,component):
        """ find pointer to component data root.
        """

        component_type = type(component)

        # find component root by type, allow subclasses
        for component_type, component_root in self._component_root_map.iteritems():
            if isinstance(component,component_type):
                break
        else:
            raise Component_Exception , "Unable to place component type %s" % component.typestring()

        return component_root

    #: get_component_root()

    def append_component(self,component):
        """ adds a component to vehicle """

        # assert database type
        if not isinstance(component,Data):
            raise Component_Exception, 'input component must be of type Data()'

        # find the place to store data
        component_root = self.find_component_root(component)

        # store data
        component_root.append(component)

        return


    def new_configuration(self,tag,ref_index=None,new_index=None):
        """ config = SUAVE.Vehicle.new_configuration(name,ref=None,index=None)
            start a new configuration, with tag name, appended to Vehicle.Configs[]
            each new configuration is a linked copy to its reference
            the first configuration is a linked copy to Vehicle

            Inputs:
                tag       - name of the new configuration
                ref_index - optional, index or key to reference the configuration
                            default, will referernce to the last configuration
                new_index - optional, index before which to add the configuration
                            default, will append to the end of Vehicle.Configs

            Outputs:
                config - a reference to the new configuration

            See also:
                SUAVE.Data.linked_copy()

        """

        # first config
        if not self.Configs:
            # linked copy from self
            #new_config = self.linked_copy()
            new_config = deepcopy(self)

            # avoid recursion problems
            del new_config.Configs

        # not first config
        else:
            # ref_index default is end
            if ref_index is None: ref_index = -1

            # get linked copy
            #new_config = self.Configs[ref_index].linked_copy()
            new_config = deepcopy(self.Configs[ref_index])

        # prepare new config
        new_config.tag = tag
        new_config.Functions = FunctionContainer()

        # new_index default is end
        if new_index is None: new_index = len(self.Configs)

        # insert new config
        self.Configs.insert(new_index,tag,new_config)

        return new_config

class ConfigContainer(Container):
    def __str__(self,indent=''):

        args = ''

        # trunk data name
        if not indent:
            args += str(type(self)) + '\n'
            indent = '  '
        else:
            args += '\n'

        for key in self.keys():
            args += indent + key + '\n'

        return args

class FunctionContainer(Container):
    pass