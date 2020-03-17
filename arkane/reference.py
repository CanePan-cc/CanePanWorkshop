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
import string
from collections import namedtuple

import yaml

from arkane.common import ArkaneSpecies, ARKANE_CLASS_DICT, symbol_by_number
from arkane.encorr.isodesmic import ErrorCancelingSpecies
from arkane.util import read_supporting_information
from rmgpy import settings
from rmgpy.molecule import Molecule
from rmgpy.quantity import ArrayQuantity, ScalarQuantity
from rmgpy.rmgobject import RMGObject
from rmgpy.species import Species
from rmgpy.thermo import ThermoData


# Module level constants
REFERENCE_DB_PATH = os.path.join(settings['database.directory'], 'reference_sets')
MAIN_REFERENCE_PATH = os.path.join(REFERENCE_DB_PATH, 'main')


class ReferenceSpecies(ArkaneSpecies):
    """
    A class for storing high level reference data and quantum chemistry calculations for a variety of model chemistry
    selections for use in isodesmic reaction calculations
    """

    def __init__(self, species=None, smiles=None, adjacency_list=None, inchi=None, reference_data=None,
                 calculated_data=None, preferred_reference=None, index=None, label=None, cas_number=None,
                 symmetry_number=None, default_xyz_chemistry=None, **kwargs):
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
            default_xyz_chemistry (str): The model chemistry that should be used to get the default XYZ coordinates for
                this species.
            **kwargs: Arguments passed to the parent ArkaneSpecies class when loading from a YAML file. Not intended for
                user input
        """

        if species is None:
            if adjacency_list:
                species = Species().from_adjacency_list(adjacency_list, raise_atomtype_exception=False,
                                                        raise_charge_exception=False)
            elif smiles:
                species = Species(smiles=smiles)
            elif inchi:
                species = Species(inchi=inchi)
            else:
                raise ValueError('Either an rmgpy species object, smiles string, InChI string, or an adjacency list '
                                 'must be given to create a ReferenceSpecies object')

        super().__init__(species=species, label=label, **kwargs)

        self.reference_data = reference_data
        self.calculated_data = calculated_data
        self.index = index
        self.cas_number = cas_number
        self.preferred_reference = preferred_reference
        self.default_xyz_chemistry = default_xyz_chemistry

        # Alter the symmetry number calculated by RMG to the one provided by the user
        if symmetry_number:
            self.symmetry_number = symmetry_number

    def __repr__(self):
        if self.index:
            label = f'{self.smiles}({self.index})'
        else:
            label = f'{self.smiles}'

        return f'<ReferenceSpecies {label}>'

    @property
    def reference_data(self):
        return self._reference_data

    @reference_data.setter
    def reference_data(self, value):
        if not value:
            self._reference_data = {}
        elif isinstance(value, dict) and _is_valid_reference_data(value):
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
        elif isinstance(value, dict) and _is_valid_calculated_data(value):
            self._calculated_data = value
        else:
            raise ValueError('Calculated data must be given as a dictionary of the model chemistry (string) and '
                             'associated CalculatedDataEntry object')

    def save_yaml(self, path=MAIN_REFERENCE_PATH):
        """
        Save the reference species to a .yml file
        """
        if not os.path.exists(os.path.join(os.path.abspath(path), '')):
            os.mkdir(os.path.join(os.path.abspath(path), ''))
        valid_chars = "-_.()<=>+ %s%s" % (string.ascii_letters, string.digits)
        filename = os.path.join(''.join(c for c in self.label if c in valid_chars) + '.yml')
        full_path = os.path.join(path, filename)
        with open(full_path, 'w') as f:
            yaml.dump(data=self.as_dict(), stream=f)
        logging.debug(f'Dumping species {self.label} data as {filename}')

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
            raise ValueError(f'Cannot create ReferenceSpecies object from yaml file {path}: object defined by this '
                             f'file is not a ReferenceSpecies object')

        data = {key: data[key] for key in data.keys() if key != 'class'}
        class_dict = ARKANE_CLASS_DICT
        class_dict['ReferenceDataEntry'] = ReferenceDataEntry
        class_dict['CalculatedDataEntry'] = CalculatedDataEntry

        self.make_object(data, class_dict)

    def update_from_arkane_spcs(self, arkane_species, supporting_info_path=None):
        """
        Add in calculated data from an existing ArkaneSpecies object.

        Notes:
            If the model chemistry already exists then this calculated data will be overwritten by the data contained
            in arkane_species

        Args:
            arkane_species (ArkaneSpecies):  Matching Arkane species that was run at the desired model chemistry
            supporting_info_path (str): Path to 'supporting_information.csv' for the species, which is used to read in
                the unscaled frequencies, electronic energy, and T1 diagnostic if they exist
        """
        # First, check that the species matches
        if not self.species.is_isomorphic(arkane_species.species):
            raise ValueError(f'Cannot update reference species {self} from arkane species {arkane_species}, as these '
                             f'species are not isomorphic. The reference species has adjacency list:\n'
                             f'{self.species.to_adjacency_list()}\nWhile the arkane species has adjacency list:\n'
                             f'{arkane_species.species.to_adjacency_list()}')

        thermo_data = arkane_species.thermo_data
        # Only store H298 and S298 data
        thermo_data.Cpdata = None
        thermo_data.Tdata = None

        conformer = arkane_species.conformer
        symbols = [symbol_by_number[n] for n in conformer.number.value]
        isotopes = [int(round(m)) for m in conformer.mass.value]
        coords = conformer.coordinates.value
        xyz_dict = {'symbols': symbols, 'isotopes': isotopes, 'coords': coords}

        unscaled_freqs = None
        electronic_energy = None
        t1_diagnostic = None
        if supporting_info_path:
            supporting_info = read_supporting_information(supporting_info_path)
            unscaled_freqs = supporting_info['Calculated Frequencies (unscaled and prior to projection, cm^-1)']
            electronic_energy = supporting_info['Electronic energy (J/mol)']
            t1_diagnostic = supporting_info['T1 diagnostic']

        calc_data = CalculatedDataEntry(thermo_data=thermo_data, xyz_dict=xyz_dict, unscaled_freqs=unscaled_freqs,
                                        electronic_energy=electronic_energy, t1_diagnostic=t1_diagnostic)
        self.calculated_data[arkane_species.level_of_theory] = calc_data

    def to_error_canceling_spcs(self, model_chemistry, source=None):
        """
        Extract calculated and reference data from a specified model chemistry and source and return as a new
        ErrorCancelingSpecies object

        Args:
            model_chemistry (str): Model chemistry (level of theory) to use as the low level data
            source (str): Reference data source to take the high level data from

        Raises:
            KeyError: If `model_chemistry` is not available for this reference species

        Returns:
            ErrorCancelingSpecies
        """
        if model_chemistry not in self.calculated_data:
            raise KeyError(f'Model chemistry `{model_chemistry}` not available for species {self}')

        molecule = Molecule().from_adjacency_list(self.adjacency_list)

        reference_enthalpy = self.get_reference_enthalpy(source=source)
        low_level_h298 = self.calculated_data[model_chemistry].thermo_data.H298

        return ErrorCancelingSpecies(
            molecule, low_level_h298, model_chemistry,
            high_level_hf298=reference_enthalpy.h298,
            source=reference_enthalpy.source
        )

    def get_reference_enthalpy(self, source=None):
        """
        Extract reference data from a specified source

        Notes:
            If no source is given, the preferred source for this species. If the `preferred_source` attribute is not set
            then the preferred source is taken as the source with the lowest non-zero uncertainty

        Args:
            source (str): Reference data source to take the high level data from

        Raises:
            ValueError: If there is no reference data for this reference species

        Returns:
            NamedTuple of ScalarQuantity containing enthalpy and preferred source
        """
        if not self.reference_data:
            raise ValueError(f'No reference data is included for species {self}')

        ReferenceEnthalpy = namedtuple('ReferenceEnthalpy', ['h298', 'source'])
        preferred_source = source

        if preferred_source is None:
            preferred_source = self.get_preferred_source()

        return ReferenceEnthalpy(
            self.reference_data[preferred_source].thermo_data.H298,
            preferred_source
        )

    def get_preferred_source(self):
        """
        Obtain the preferred reference data source for the species

        Notes:
            If the 'preferred_source` attribute is set, return it,
            otherwise use the source with the lowest non-zero uncertainty.

        Returns:
            String with the preferred source
        """
        if self.preferred_reference is not None:
            preferred_source = self.preferred_reference
        else:  # Choose the source that has the smallest uncertainty
            sources = list(self.reference_data.keys())
            data = list(self.reference_data.values())
            preferred_source = sources[0]  # If all else fails, use the first source as the preferred one
            uncertainty = data[0].thermo_data.H298.uncertainty_si
            for i, entry in enumerate(data):
                if 0 < entry.thermo_data.H298.uncertainty_si < uncertainty:
                    uncertainty = entry.thermo_data.H298.uncertainty_si
                    preferred_source = sources[i]

        return preferred_source

    def get_default_xyz(self):
        """
        Return the XYZ coordinates of the default geometry for this species for use as a starting point for other
        quantum chemistry calculations

        Notes:
            The attribute `default_xyz_chemistry` must be set for this reference species, preferable to a model
            chemistry with a highly accurate equilibrium geometry

        Returns:
            ArrayQuantity
        """
        if self.default_xyz_chemistry:
            return self.calculated_data[self.default_xyz_chemistry].xyz_dict
        else:
            raise ValueError(f'The default model chemistry to use for XYZ coordinates has not been set '
                             f'for {self}')


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
        super().__init__()
        self.thermo_data = thermo_data
        self.atct_id = atct_id

    def __repr__(self):
        return str(self.as_dict())

    @property
    def thermo_data(self):
        return self._thermo_data

    @thermo_data.setter
    def thermo_data(self, value):
        if value is not None:
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
    def __init__(self, thermo_data, xyz_dict=None, unscaled_freqs=None, electronic_energy=None, t1_diagnostic=None,
                 fod=None):
        """

        Args:
            thermo_data (rmgpy.thermo.ThermoData): Actual thermochemistry values calculated using statistical mechanics
                at select points. Arkane fits a heat capacity model to this data
            xyz_dict (dict): An ARC style xyz dictionary for the cartesian coordinates
            unscaled_freqs (np.array): Unscaled harmonic frequencies
            electronic_energy (ScalarQuantity): The electronic single point energy
            t1_diagnostic (float): T1 diagnostic for coupled cluster calculations to check if single reference methods
                are suitable
            fod (float): Fractional Occupation number weighted electron Density
        """
        super().__init__()
        self.thermo_data = thermo_data
        self.xyz_dict = xyz_dict
        self.unscaled_freqs = unscaled_freqs
        self.electronic_energy = electronic_energy
        self.t1_diagnostic = t1_diagnostic
        self.fod = fod

    def __repr__(self):
        return str(self.as_dict())

    @property
    def thermo_data(self):
        return self._thermo_data

    @thermo_data.setter
    def thermo_data(self, value):
        if value is not None:
            if isinstance(value, ThermoData):
                self._thermo_data = value
            else:
                raise ValueError('thermo_data for a CalculatedDataEntry object must be an rmgpy ThermoData object')
        else:
            self._thermo_data = None

    @property
    def electronic_energy(self):
        return self._electronic_energy

    @electronic_energy.setter
    def electronic_energy(self, value):
        if value:  # Allow empty string, which is a possibility when reading an Arkane supporting info file
            if isinstance(value, ScalarQuantity):
                self._electronic_energy = value
            else:
                raise ValueError('electronic_energy for a CalculatedDataEntry object must be an rmgpy ScalarQuantity '
                                 'object')
        else:
            self._electronic_energy = None

    @property
    def unscaled_freqs(self):
        return self._unscaled_freqs

    @unscaled_freqs.setter
    def unscaled_freqs(self, value):
        if value:  # Allow empty string, which is a possibility when reading an Arkane supporting info file
            if isinstance(value, ArrayQuantity):
                self._unscaled_freqs = value
            else:
                raise ValueError('unscaled_freqs for a CalculatedDataEntry object must be an rmgpy ArrayQuantity '
                                 'object')
        else:
            self._unscaled_freqs = None


class ReferenceDatabase(object):
    """
    A class for loading and working with database of reference species, located at RMG-database/input/reference_sets/
    """
    def __init__(self):
        """
        Attributes:
            self.reference_sets (Dict[str, ReferenceSpecies]): {'set name': [ReferenceSpecies, ...], ...}
        """
        self.reference_sets = {}

    def load(self, paths=None, ignore_incomplete=True):
        """
        Load one or more set of reference species and append it on to the database

        Args:
            paths (list): A single path string, or a list of path strings pointing to a set of reference
                species to be loaded into the database. The string should point to the folder that has the name of the
                reference set. The name of sub-folders in a reference set directory should be indices starting from 0
                and should contain a YAML file that defines the ReferenceSpecies object of that index, named {index}.yml
            ignore_incomplete (bool): If ``True`` only species with both reference and calculated data will be added.
        """
        if paths is None:  # Default to the main reference set in RMG-database
            paths = [MAIN_REFERENCE_PATH]

        if isinstance(paths, str):  # Convert to a list with one element
            paths = [paths]

        molecule_list = []
        for path in paths:
            set_name = os.path.basename(path)
            logging.info(f'Loading in reference set `{set_name}` from {path} ...')
            spcs_files = os.listdir(path)
            reference_set = []
            for spcs in spcs_files:
                if '.yml' not in spcs:
                    continue
                ref_spcs = ReferenceSpecies.__new__(ReferenceSpecies)
                ref_spcs.load_yaml(os.path.join(path, spcs))
                molecule = Molecule().from_adjacency_list(ref_spcs.adjacency_list, raise_atomtype_exception=False,
                                                          raise_charge_exception=False)
                if ignore_incomplete:
                    if (len(ref_spcs.calculated_data) == 0) or (len(ref_spcs.reference_data) == 0):
                        logging.warning(f'Molecule {ref_spcs.smiles} from reference set `{set_name}` does not have any '
                                        f'reference data and/or calculated data. This entry will not be added')
                        continue
                # perform isomorphism checks to prevent duplicate species
                for mol in molecule_list:
                    if molecule.is_isomorphic(mol):
                        logging.warning(f'Molecule {ref_spcs.smiles} from reference set `{set_name}` already exists in '
                                        f'the reference database. The entry from this reference set will not be added. '
                                        f'The path for this species is {spcs}')
                        break
                else:
                    molecule_list.append(molecule)
                    reference_set.append(ref_spcs)

            self.reference_sets[set_name] = reference_set

    def save(self, database_root_path=None):
        """

        Args:
            database_root_path (str): Path to the reference set parent folder (typical subfolders include 'main' etc.)
        """
        if database_root_path is None:
            database_root_path = REFERENCE_DB_PATH

        for set_name, reference_set in self.reference_sets.items():
            set_path = os.path.join(database_root_path, set_name)
            for spcs in reference_set:
                spcs.save_yml(path=set_path)

    def extract_model_chemistry(self, model_chemistry, sets=None, as_error_canceling_species=True):
        """
        Return a list of ErrorCancelingSpecies or ReferenceSpecies objects from the reference species in the database
        that have entries for the requested model chemistry

        Args:
            model_chemistry (str): String that describes the level of chemistry used to calculate the low level data
            sets (list): A list of the names of the reference sets to include (all sets in the database will be used if
                not specified or `None`)
            as_error_canceling_species (bool): Return ErrorCancelingSpecies objects if True

        Returns:
            List[ErrorCancelingSpecies]
        """
        reference_list = []

        if sets is None:  # Load in all of the sets
            sets = self.reference_sets.keys()

        for set_name in sets:
            current_set = self.reference_sets[set_name]
            for ref_spcs in current_set:
                if model_chemistry not in ref_spcs.calculated_data:  # Move on to the next reference species
                    continue
                if not ref_spcs.reference_data:  # This reference species does not have any sources, continue on
                    continue
                reference_list.append(ref_spcs)

        if as_error_canceling_species:
            reference_list = [s.to_error_canceling_spcs(model_chemistry) for s in reference_list]

        return reference_list

    def list_available_chemistry(self, sets=None):
        """
        List the set of available model chemistries present in at least one reference species in the database

        Args:
            sets (list): A list of the names of the reference sets to include (all sets in the database will be used if
                not specified or `None`)

        Returns:
            List[str]
        """
        model_chemistry_set = set()
        if sets is None:  # Load in all of the sets
            sets = self.reference_sets.keys()

        for set_name in sets:
            current_set = self.reference_sets[set_name]
            for ref_spcs in current_set:
                model_chemistry_set.update(ref_spcs.calculated_data.keys())

        return list(model_chemistry_set)

    def get_species_from_index(self, indices, set_name='main'):
        """
        Returns a list of reference species from the requested reference set that matches the indices in order

        Args:
            indices (List(int)): A list of reference species indices to return (in order)
            set_name (str): The name of the reference set to search in (only one set)

        Returns:
            List
        """
        if not isinstance(indices, list):
            indices = [indices]

        reference_species_list = []
        search_set = self.reference_sets[set_name]
        for index in indices:
            if not isinstance(index, int):
                index = int(index)
            for ref_spcs in search_set:
                if ref_spcs.index == index:
                    reference_species_list.append(ref_spcs)
                    break
            else:
                raise ValueError(f'No reference species with index {index} was found in reference set {set_name}')

        return reference_species_list

    def get_species_from_label(self, labels, set_name='main'):
        """
        Returns a list of reference species from the requested reference set that matches the labels in order

        Args:
            labels (List(str)): A list of labels that match the returned reference species (in order)
            set_name (str): The name of the reference set to search in (only one set)

        Returns:
            List
        """
        if not isinstance(labels, list):
            labels = [labels]

        reference_species_list = []
        search_set = self.reference_sets[set_name]
        for label in labels:
            if not isinstance(label, str):
                label = str(label)
            for ref_spcs in search_set:
                if ref_spcs.label == label:
                    reference_species_list.append(ref_spcs)
                    break
            else:
                raise ValueError(f'No reference species with label "{label}" was found in reference set {set_name}')

        return reference_species_list


def _is_valid_reference_data(data_dictionary):
    """
    Determine if the given reference_data dictionary is supplied in a valid format
    Args:
        data_dictionary (dict): reference_data dictionary

    Returns:
        bool
    """
    if all(isinstance(source, str) for source in data_dictionary.keys()):
        if all(isinstance(data_entry, ReferenceDataEntry) for data_entry in data_dictionary.values()):
            return True
    return False


def _is_valid_calculated_data(data_dictionary):
    """
    Determine if the given calculated_data dictionary is supplied in a valid format
    Args:
        data_dictionary (dict): calculated_data dictionary

    Returns:
        bool
    """
    if all(isinstance(source, str) for source in data_dictionary.keys()):
        if all(isinstance(data_entry, CalculatedDataEntry) for data_entry in data_dictionary.values()):
            return True
    return False


if __name__ == '__main__':
    pass
