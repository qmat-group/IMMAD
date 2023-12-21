# initial backbone of IMMAD
# specifically for substitution problem
# following Lam's paper

from pathlib import Path

from immad.abstract import Materials
from immad.apps.substitution import run_immad

from aiida import load_profile
load_profile()


if __name__ == '__main__':
    candidates = ['La']
    base_dir = Path(__file__).parent.absolute() / 'test/substitution'
    material_structure_file = base_dir / 'SrRuO3_Acta_Cryst_C45_365.vasp'
    
    run_immad(material_structure_file, candidates, [0, 1, 3])