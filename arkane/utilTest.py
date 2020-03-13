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
This module contains unit tests of the :mod:`arkane.util` module.
"""

import os
import unittest

from rmgpy.exceptions import InputError
from rmgpy.quantity import ScalarQuantity, ArrayQuantity

from arkane.ess import GaussianLog, MolproLog, QChemLog, TeraChemLog
from arkane.util import determine_qm_software, read_supporting_information

################################################################################


class TestThermo(unittest.TestCase):
    """
    Contains unit tests of the util module.
    """
    @classmethod
    def setUpClass(cls):
        """
        A method that is run before all unit tests in this class.
        """
        cls.data_path = os.path.join(os.path.dirname(__file__), 'data')

    def test_determine_qm_software(self):
        """Test identifying the electronic structure software from the log file"""
        gaussian_log_path1 = os.path.join(self.data_path, 'gaussian', 'ethylene_G3.log')
        gaussian_log_path2 = os.path.join(self.data_path, 'gaussian', 'oxygen.log')
        molpro_log_path1 = os.path.join(self.data_path, 'molpro', 'HOSI_ccsd_t1.out')
        molpro_log_path2 = os.path.join(self.data_path, 'molpro', 'molpro_mrci+q.out')
        qchem_log_path1 = os.path.join(self.data_path, 'qchem', 'CH4_sp.out')
        qchem_log_path2 = os.path.join(self.data_path, 'qchem', 'co.out')
        terachem_log_path_1 = os.path.join(self.data_path, 'terachem', 'ethane_minimize_output.out')
        terachem_log_path_2 = os.path.join(self.data_path, 'terachem', 'formaldehyde_sp_terachem_output.out')
        terachem_log_path_3 = os.path.join(self.data_path, 'terachem', 'formaldehyde_sp_terachem_results.dat')
        terachem_log_path_4 = os.path.join(self.data_path, 'terachem', 'formaldehyde_coords.xyz')
        terachem_log_path_5 = os.path.join(self.data_path, 'terachem', 'formaldehyde_output.geometry')
        non_ess_log_path = os.path.join(os.path.dirname(__file__), 'data', 'methoxy.py')

        self.assertIsInstance(determine_qm_software(gaussian_log_path1), GaussianLog)
        self.assertIsInstance(determine_qm_software(gaussian_log_path2), GaussianLog)
        self.assertIsInstance(determine_qm_software(molpro_log_path1), MolproLog)
        self.assertIsInstance(determine_qm_software(molpro_log_path2), MolproLog)
        self.assertIsInstance(determine_qm_software(qchem_log_path1), QChemLog)
        self.assertIsInstance(determine_qm_software(qchem_log_path2), QChemLog)
        self.assertIsInstance(determine_qm_software(terachem_log_path_1), TeraChemLog)
        self.assertIsInstance(determine_qm_software(terachem_log_path_2), TeraChemLog)
        self.assertIsInstance(determine_qm_software(terachem_log_path_3), TeraChemLog)
        self.assertIsInstance(determine_qm_software(terachem_log_path_4), TeraChemLog)
        self.assertIsInstance(determine_qm_software(terachem_log_path_5), TeraChemLog)

        with self.assertRaises(InputError):
            determine_qm_software(non_ess_log_path)

    def test_read_supporting_information(self):
        """Test that we can read in the supporting information file"""
        path = os.path.join(self.data_path, 'species', 'supporting_information.csv')
        supporting_info = read_supporting_information(path)

        self.assertEqual(supporting_info['Label'], 'C2H6')
        self.assertEqual(supporting_info['Symmetry Number'], 6)
        self.assertIsInstance(supporting_info['Rotational constant (cm-1)'], ArrayQuantity)
        self.assertIsInstance(supporting_info['Electronic energy (J/mol)'], ScalarQuantity)
        self.assertAlmostEqual(supporting_info['T1 diagnostic'], 0.101)
        self.assertEqual(supporting_info['D1 diagnostic'], '')

################################################################################


if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
