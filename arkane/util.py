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
This module contains different utilities used in Arkane.
"""

import csv
import os

import numpy as np

from rmgpy.exceptions import InputError
from rmgpy.quantity import ScalarQuantity, ArrayQuantity

from arkane.ess import GaussianLog, MolproLog, OrcaLog, QChemLog, TeraChemLog

################################################################################


def determine_qm_software(fullpath):
    """
    Given a path to the log file of a QM software, determine whether it is
    Gaussian, Molpro, QChem, or TeraChem
    """
    with open(fullpath, 'r') as f:
        software_log = None
        if os.path.splitext(fullpath)[1] in ['.xyz', '.dat', '.geometry']:
            software_log = TeraChemLog(fullpath)
        line = f.readline()
        while software_log is None and line != '':
            if 'gaussian' in line.lower():
                software_log = GaussianLog(fullpath)
                break
            elif 'molpro' in line.lower():
                software_log = MolproLog(fullpath)
                break
            elif 'qchem' in line.lower():
                software_log = QChemLog(fullpath)
                break
            elif 'terachem' in line.lower():
                software_log = TeraChemLog(fullpath)
                break
            elif 'orca' in line.lower():
                f.close()
                software_log = OrcaLog(fullpath)
                break
            line = f.readline()
        if software_log is None:
            f.close()
            raise InputError(f'The file at {fullpath} could not be identified as a '
                             'Gaussian, Molpro, QChem, or TeraChem log file.')
    return software_log


def read_supporting_information(path):
    """
    Read in the data stored in the supporting information file

    Args:
        path (str): Path to 'supporting_information.csv' for the species

    Returns:
        dict: Fields as keys, data as values
    """
    with open(path, 'r') as f:
        reader = csv.reader(f)
        fields = next(reader)
        data = next(reader)

    supporting_info = {key: value for key, value in zip(fields, data)}

    # Convert types
    for field, value in supporting_info.items():
        if value:  # Do not convert empty string
            # int
            if field in ['Symmetry Number', 'Number of optical isomers']:
                try:
                    supporting_info[field] = int(value)
                except ValueError:
                    supporting_info[field] = float(value)
            # float
            elif field in ['T1 diagnostic', 'D1 diagnostic']:
                supporting_info[field] = float(value)

            # ScalarQuantity
            elif field in ['Electronic energy (J/mol)', 'E0 (electronic energy + ZPE, J/mol)',
                           'E0 with atom and bond corrections (J/mol)']:
                supporting_info[field] = ScalarQuantity(float(value), 'J/mol')

            # ArrayQuantity
            elif field in ['Rotational constant (cm-1)',
                           'Calculated Frequencies (unscaled and prior to projection, cm^-1)']:
                supporting_info[field] = ArrayQuantity(np.array([float(x) for x in value.split(',')]), 'cm^-1')

    return supporting_info
