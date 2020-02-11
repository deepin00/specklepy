import os
from configparser import ConfigParser
from astropy.table import Table

from specklepy.exceptions import SpecklepyTypeError
from specklepy.logging import logging
from specklepy.io.filemanager import FileManager


class ParameterSet(object):

    def __init__(self, parameter_file, defaults_file=None, essential_attributes=None, make_dirs=None):
        """Class that carries parameters.

        This class carries all the important parameters and is also capable
        of reading parameter files, where essential parameters can be defined,
        which are completed from a defaults file if not provided in the
        parameter file.

        Args:
            parameter_file (str):
                Path to a file that contains parameters
            defaults_file (str, optional):
                Path to a file that contains default parameters.
            essential_attributes (list, optional):
                List of attributes that are essential and are thus filled from
                the defaults file, if not provided in the parameter file.
            make_dirs (list, optional):
                List of directory paths to create, if they are not existing yet.
        """

        # Check input parameters
        if isinstance(parameter_file, str):
            # Check whether file exist
            if not os.path.isfile(parameter_file):
                raise FileNotFoundError("Parameter file {} not found!".format(parameter_file))
            self.parameter_file = parameter_file
        else:
            raise SpecklepyTypeError('ParameterSet', argname='parameter_file', argtype=type(parameter_file), expected='str')

        if isinstance(defaults_file, str):
            if not os.path.isfile(defaults_file):
                raise FileNotFoundError("Defaults file {} not found!".format(defaults_file))
            self.defaults_file = defaults_file
        elif defaults_file is None:
            self.defaults_file = defaults_file
        else:
            raise SpecklepyTypeError('ParameterSet', argname='defaults_file', argtype=type(defaults_file), expected='str')

        if essential_attributes is None:
            essential_attributes = []
        if make_dirs is None:
            make_dirs = []

        # Read parameter_file
        parser = ConfigParser(inline_comment_prefixes="#")
        parser.optionxform = str  # make option names case sensitive
        logging.info("Reading parameter file {}".format(self.parameter_file))
        parser.read(self.parameter_file)
        for section in parser.sections():
            for key in parser[section]:
                value = parser[section][key]
                # Interprete data type
                try:
                    setattr(self, key, eval(value))
                except:
                    setattr(self, key, value)


        # Complete list of essential attributes from defaults file
        if self.defaults_file is not None:
            defaults = ConfigParser(inline_comment_prefixes="#")
            defaults.optionxform = str  # make option names case sensitive
            logging.info("Reading defaults file {}".format(self.defaults_file))
            defaults.read(self.defaults_file)
            for attr in essential_attributes:
                if not hasattr(self, attr):
                    attr_set = False
                    for section in defaults.sections():
                        for key in defaults[section]:
                            if key == attr:
                                value = defaults[section][key]
                                # Interprete data type
                                try:
                                    setattr(self, key, eval(value))
                                except:
                                    setattr(self, key, value)
                                attr_set = True
                    if not attr_set:
                        logging.warning("Essential parameter '{}' not found in parameter file or config file!".format(attr))

        # Create directories
        self.makedirs(dir_list=make_dirs)

        # Create file lists
        try:
            self.inFiles = FileManager(self.inDir).files
        except AttributeError:
            logging.warn("ParameterSet instance is not storing 'inFiles' due to missing entry 'inDir' parameter in parameter file!")



    def makedirs(self, dir_list):
        """
        This function makes sure that the paths exist and creates if not.
        """
        for key in dir_list:
            path = getattr(self, key)
            path = os.path.dirname(path) + '/' # Cosmetics to allow for generic input for inDir
            if not os.path.exists(path):
                logging.info('Creating {} directory {}'.format(key, path))
                os.makedirs(path)
