# initial backbone of IMMAD
# specifically for Nd2Fe14B substitution problem
# following Lam's paper

import os

from immad.abstract import Materials
from immad.apps.substitution import run_immad

from aiida import load_profile
load_profile()


if __name__ == '__main__':
    candidates = ['La']
    base_dir = os.path.dirname(os.path.abspath(__file__)) + '/test/substitution'
    material_structure_file = f'{base_dir}/Nd2Fe14B_mp-5182_conventional_standard.cif'
    materials = Materials(material_structure_file, candidates)
    
    run_immad(materials, candidates, [1, 10, 20])