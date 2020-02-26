#!/usr/bin/env python3

###############################################################################
#                                                                             #
# RMG - Reaction Mechanism Generator                                          #
#                                                                             #
# Copyright (c) 2002-2019 Prof. William H. Green (whgreen@mit.edu),           #
# Prof. Richard H. West (r.west@neu.edu) and the RMG Team (rmg_dev@mit.edu)   #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the 'Software'),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
###############################################################################

"""

"""
import logging
import math
import os.path
from copy import deepcopy

from rmgpy.data.base import Database, Entry, DatabaseError
from rmgpy.exceptions import InputError


################################################################################

def save_entry(f, entry):
    """
    Write a Pythonic string representation of the given `entry` in the solvation
    database to the file object `f`.
    """
    f.write('entry(\n')
    f.write('    index = {0:d},\n'.format(entry.index))
    f.write('    label = "{0}",\n'.format(entry.label))
    f.write('    bindingEnergies = {\n')
    for key, value in entry.bindingEnergies.items():
        f.write("        '" + key + "':" + str(value) + ",\n")
    f.write("    }\n")
    f.write('    surfaceSiteDensity = {0},\n'.format(entry.surfaceSiteDesnity))
    f.write('    facet = "{0}",\n'.format(entry.facet))
    f.write('    metal = "{0}",\n'.format(entry.metal))
    f.write(f'    shortDesc = """{entry.short_desc.strip()}""",\n')
    f.write(f'    longDesc = \n"""\n{entry.long_desc.strip()}\n""",\n')
    f.write(')\n\n')


################################################################################


################################################################################

class MetalLibrary(Database):
    """
    A class for working with a RMG metal library.
    """

    def __init__(self, label='', name='', short_desc='', long_desc=''):
        Database.__init__(self, label=label, name=name, short_desc=short_desc, long_desc=long_desc)

    def load_entry(self,
                   index,
                   label,
                   metal='',
                   facet='',
                   surfaceSiteDensity=(),
                   bindingEnergies={},
                   shortDesc='',
                   longDesc='',
                   ):
        """
        Method for parsing entries in database files.
        Note that these argument names are retained for backward compatibility.
        """

        self.entries[label] = Entry(
            index=index,
            label=label,
            metal=metal,
            facet=facet,
            surface_site_density=surfaceSiteDensity,
            binding_energies=bindingEnergies,
            short_desc=shortDesc,
            long_desc=longDesc.strip(),
        )

    def load(self, path):
        """
        Load the metal library from the given path
        """
        Database.load(self, path, local_context={}, global_context={})

    def save_entry(self, f, entry):
        """
        Write the given `entry` in the metal database to the file object `f`.
        """
        return save_entry(f, entry)

    def get_binding_energies(self, label):
        """
        Get a metal's binding energies from its name
        """
        return self.entries[label].binding_energies

    def get_surface_site_density(self, label):
        """
        Get a metal's surface site desnity from its name
        """
        return self.entries[label].surface_site_density


################################################################################

class MetalDatabase(object):
    """
    A class for working with the RMG metal database.
    """

    def __init__(self):
        self.libraries = {}
        self.libraries['surface'] = MetalLibrary()
        self.groups = {}
        self.local_context = {}
        self.global_context = {}

    def __reduce__(self):
        """
        A helper function used when pickling a MetalDatabase object.
        """
        d = {
            'libraries': self.libraries,
        }
        return (MetalDatabase, (), d)

    def __setstate__(self, d):
        """
        A helper function used when unpickling a MetalDatabase object.
        """
        self.libraries = d['libraries']

    def load(self, path, libraries=None, depository=True):
        """
        Load the metal database from the given `path` on disk, where `path`
        points to the top-level folder of the solvation database.
        
        Load the metal library
        """

        self.libraries['surface'].load(os.path.join(path, 'libraries', 'metal.py'))

    def get_binding_energies(self, metal_name):
        try:
            metal_data = self.libraries['surface'].get_binding_energies(metal_name)
        except:
            raise DatabaseError('Metal {0!r} not found in database'.format(metal_name))
        return metal_data

    def get_surface_site_density(self, metal_name):
        try:
            metal_data = self.libraries['surface'].get_surface_site_density(metal_name)
        except:
            raise DatabaseError('Metal {0!r} not found in database'.format(metal_name))
        return metal_data

    def save(self, path):
        """
        Save the metal database to the given `path` on disk, where `path`
        points to the top-level folder of the metal database.
        """
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.mkdir(path)
        self.save_libraries(os.path.join(path, 'libraries'))

    def save_libraries(self, path):
        """
        Save the metal libraries to the given `path` on disk, where `path`
        points to the top-level folder of the metal libraries.
        """
        if not os.path.exists(path):
            os.mkdir(path)
        for library in self.libraries.keys():
            self.libraries[library].save(os.path.join(path, library + '.py'))

    def load_old(self, path):
        """
        Load the old RMG metal database from the given `path` on disk, where
        `path` points to the top-level folder of the old RMG database.
        """

        raise NotImplementedError()

    def save_old(self, path):
        """
        Save the old metal database to the given `path` on disk, where
        `path` points to the top-level folder of the old RMG database.
        """
        # Depository not used in old database, so it is not saved

        raise NotImplementedError()

