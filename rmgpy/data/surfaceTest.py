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

import os
from unittest import TestCase, TestLoader, TextTestRunner

from rmgpy import settings
from rmgpy.data.base import Entry
from rmgpy.data.surface import MetalDatabase
from rmgpy.exceptions import InputError

###################################################

class TestMetalDatabase(TestCase):

    def setUp(self):
        self.database = MetalDatabase()
        self.database.load(os.path.join(settings['database.directory'], 'surface'))

    def tearDown(self):
        """
        Reset the database & parameters
        """
        import rmgpy.data.rmg
        rmgpy.data.rmg.database = None

    def test_metal_library(self):
        """Test we can obtain metal parameters from a library"""

        test_entry = Entry(
            index=1,
            label="Pt111",
            binding_energies={
                'H': (-2.75367887E+00, 'eV/molecule'),
                'C': (-7.02515507E+00, 'eV/molecule'),
                'N': (-4.63224568E+00, 'eV/molecule'),
                'O': (-3.81153179E+00, 'eV/molecule'),
            },
            surface_site_density=(2.483E-09, 'mol/cm^2'),
            facet="111",
            metal="Pt",
            short_desc=u"fcc",
            long_desc=u"""
        Calculated by Katrin Blondal and Bjarne Kreitz at Brown University
            """,
        )

        self.assertEqual(self.database.get_binding_energies(test_entry.label), test_entry.binding_energies)
        self.assertEqual(self.database.get_surface_site_density(test_entry.label), test_entry.surface_site_density)


#####################################################


if __name__ == '__main__':
    suite = TestLoader().loadTestsFromTestCase(TestMetalDatabase)
    TextTestRunner(verbosity=2).run(suite)
