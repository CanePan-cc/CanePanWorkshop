#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
This module defines the ReferenceSpecies class, which are used in isodesmic reaction calculations

"""

import logging
import os

import yaml

from arkane.common import ArkaneSpecies, ARKANE_CLASS_DICT
from rmgpy import settings
from rmgpy.molecule import Molecule
from rmgpy.rmgobject import RMGObject
from rmgpy.species import Species
from rmgpy.statmech import Conformer
from rmgpy.thermo import ThermoData


class ReferenceSpecies(ArkaneSpecies):
    """
    A class for storing high level reference data and quantum chemistry calculations for a variety of model chemistry
    selections for use in isodesmic reaction calculations
    """

    def __init__(self, species=None, smiles=None, adjacency_list=None, inchi=None, reference_data=None,
                 calculated_data=None, preferred_reference=None, index=None, label=None, cas_number=None,
                 symmetry_number=None, **kwargs):
        """
        One of the following must be provided: species, smiles, adjacency_list, inchi.

        Args:
            species (rmgpy.molecule.Species): Molecule object representing the reference species
            smiles (str): SMILES string representing the reference species
            adjacency_list (str): An RMG adjacency list representation of the reference species
            inchi (str): InChI string representing the reference species
            reference_data (dict): Formatted as {'source_string': ReferenceDataEntry, ...}
            calculated_data (dict): Formatted as {'model_chemistry': CalculatedDataEntry, ...}
            preferred_reference (str): The source string key for the reference data to use for isodesmic reactions
            index (int): Index of this species in the database of reference species located at
                `RMG-database/input/reference_sets/`
            label (str): A user defined label for easily identifying the species
            cas_number (str): CAS number associated with the reference species
            symmetry_number (int): The true symmetry number of the species (if not provided will default to the number
                calculated by RMG)
            **kwargs: Arguments passed to the parent ArkaneSpecies class when loading from a YAML file. Not intended for
                user input
        """

        if species is None:
            if smiles:
                species = Species(smiles=smiles)
            elif inchi:
                species = Species(inchi=inchi)
            elif adjacency_list:
                species = Species().from_adjacency_list(adjacency_list)
            else:
                raise ValueError('Either an rmgpy species object, smiles string, InChI string, or an adjacency list '
                                 'must be given to create a ReferenceSpecies object')

        super(ReferenceSpecies, self).__init__(species=species, label=label, **kwargs)

        self.reference_data = reference_data
        self.calculated_data = calculated_data
        self.index = index
        self.cas_number = cas_number
        self.preferred_reference = preferred_reference

        # Alter the symmetry number calculated by RMG to the one provided by the user
        if symmetry_number:
            self.symmetry_number = symmetry_number

    def __repr__(self):
        if self.index:
            label = '{0}({1})'.format(self.smiles, self.index)
        else:
            label = '{0}'.format(self.smiles)

        return '<ReferenceSpecies {0}>'.format(label)

    @property
    def reference_data(self):
        return self._reference_data

    @reference_data.setter
    def reference_data(self, value):
        if not value:
            self._reference_data = {}
        elif isinstance(value, dict):
            if all(isinstance(source, str) for source in value.keys()):
                if all(isinstance(data_entry, ReferenceDataEntry) for data_entry in value.values()):
                    self._reference_data = value
        else:
            raise ValueError('Reference data must be given as a dictionary of the data source (string) and associated '
                             'ReferenceDataEntry object')

    @property
    def calculated_data(self):
        return self._calculated_data

    @calculated_data.setter
    def calculated_data(self, value):
        if not value:
            self._calculated_data = {}
        elif isinstance(value, dict):
            if all(isinstance(source, str) for source in value.keys()):
                if all(isinstance(data_entry, CalculatedDataEntry) for data_entry in value.values()):
                    self._calculated_data = value
        else:
            raise ValueError('Calculated data must be given as a dictionary of the model chemistry (string) and '
                             'associated CalculatedDataEntry object')

    def load_yaml(self, path, label=None, pdep=False):
        """
        Load a ReferenceSpecies object from a YAML file.

        Args:
            path (str): Location on disk of the YAML file
            label: Unused argument from parent class ArkaneSpecies
            pdep: Unused argument from parent class ArkaneSpecies
        """
        with open(path, 'r') as f:
            data = yaml.safe_load(stream=f)

        if data['class'] != 'ReferenceSpecies':
            raise ValueError('Cannot create ReferenceSpecies object from yaml file {0}: object defined by this file is'
                             'not a ReferenceSpecies object'.format(path))

        data = {key: data[key] for key in data.keys() if key != 'class'}
        class_dict = ARKANE_CLASS_DICT
        class_dict['ReferenceDataEntry'] = ReferenceDataEntry
        class_dict['CalculatedDataEntry'] = CalculatedDataEntry

        self.make_object(data, class_dict)


class ReferenceDataEntry(RMGObject):
    """
    A class for storing reference data for a specific species from a single source
    """
    def __init__(self, thermo_data, atct_id=None):
        """

        Args:
            thermo_data (rmgpy.thermo.ThermoData): Thermochemistry (Hf298, Cp, ...) from the reference for a species
            atct_id (str): ID number in the Active Thermochemical Tables if the source is ATcT
        """
        super(ReferenceDataEntry, self).__init__()
        self.thermo_data = thermo_data
        self.atct_id = atct_id

    def __repr__(self):
        return str(self.as_dict())

    @property
    def thermo_data(self):
        return self._thermo_data

    @thermo_data.setter
    def thermo_data(self, value):
        if value:
            if isinstance(value, ThermoData):
                self._thermo_data = value
            else:
                raise ValueError('thermo_data for a ReferenceDataEntry object must be an rmgpy ThermoData instance')
        else:
            self._thermo_data = None


class CalculatedDataEntry(RMGObject):
    """
    A class for storing a single entry of statistical mechanical and thermochemistry information calculated at a single
    model chemistry or level of theory
    """
    def __init__(self, conformer, thermo_data, t1_diagnostic=None, fod=None):
        """

        Args:
            conformer (rmgpy.statmech.Conformer): Conformer object generated from an Arkane job. Stores many pieces of
                information gained from quantum chemistry calculations, including coordinates, frequencies etc.
            thermo_data (rmgpy.thermo.ThermoData): Actual thermochemistry values calculated using statistical mechanics
                at select points. Arkane fits a heat capacity model to this data
            t1_diagnostic (float): T1 diagnostic for coupled cluster calculations to check if single reference methods
                are suitable
            fod (float): Fractional Occupation number weighted electron Density
        """
        super(CalculatedDataEntry, self).__init__()
        self.conformer = conformer
        self.thermo_data = thermo_data
        self.t1_diagnostic = t1_diagnostic
        self.fod = fod

    def __repr__(self):
        return str(self.as_dict())

    @property
    def conformer(self):
        return self._conformer

    @conformer.setter
    def conformer(self, value):
        if value:
            if isinstance(value, Conformer):
                self._conformer = value
            else:
                raise ValueError('conformer for a CalculatedDataEntry object must be an rmgpy Conformer instance')
        else:
            self._conformer = None

    @property
    def thermo_data(self):
        return self._thermo_data

    @thermo_data.setter
    def thermo_data(self, value):
        if value:
            if isinstance(value, ThermoData):
                self._thermo_data = value
            else:
                raise ValueError('thermo_data for a CalculatedDataEntry object must be an rmgpy ThermoData object')


class ReferenceDatabase(object):
    """
    A class for loading and working with database of reference species, located at RMG-database/input/reference_sets/
    """
    def __init__(self):
        """
        Attributes:
            self.reference_sets (dict): {'set name': [ReferenceSpecies, ...], ...}
        """
        self.reference_sets = {}

    def load(self, paths=''):
        """
        Load one or more set of reference species and append it on to the database

        Args:
            paths (Union[list, str]): A single path string, or a list of path strings pointing to a set of reference
                species to be loaded into the database. The string should point to the folder that has the name of the
                reference set. The name of sub-folders in a reference set directory should be indices starting from 0
                and should contain a YAML file that defines the ReferenceSpecies object of that index, named {index}.yml
        """
        if not paths:  # Default to the main reference set in RMG-database
            paths = [os.path.join(settings['database.directory'], 'reference_sets/main')]

        if isinstance(paths, str):  # Convert to a list with one element
            paths = [paths]

        molecule_list = []
        for path in paths:
            set_name = os.path.basename(path)
            logging.info('Loading in reference set `{0}` from {1} ...'.format(set_name, path))
            spcs_files = os.listdir(path)
            reference_set = []
            for spcs in spcs_files:
                if '.yml' not in spcs:
                    continue
                ref_spcs = ReferenceSpecies.__new__(ReferenceSpecies)
                ref_spcs.load_yaml(os.path.join(path, spcs))
                molecule = Molecule().from_adjacency_list(ref_spcs.adjacency_list)
                if (len(ref_spcs.calculated_data) == 0) or (len(ref_spcs.reference_data) == 0):
                    logging.warning('Molecule {0} from reference set `{1}` does not have any reference data and/or '
                                    'calculated data. This entry will not be added'.format(ref_spcs.smiles, set_name))
                    continue
                # perform isomorphism checks to prevent duplicate species
                for mol in molecule_list:
                    if molecule.is_isomorphic(mol):
                        logging.warning('Molecule {0} from reference set `{1}` already exists in the reference '
                                        'database. The entry from this reference set will not be added. The path for '
                                        'this species is {2}'.format(ref_spcs.smiles, set_name, spcs))
                        break
                else:
                    molecule_list.append(molecule)
                    reference_set.append(ref_spcs)

            self.reference_sets[set_name] = reference_set


if __name__ == '__main__':
    pass
