# initial backbone of IMMAD
# specifically for Nd2Fe14B substitution problem
# following Lam's paper

import os

from immad.abstract import Materials
from immad.apps.substitution import SubstitutionPredictor as Predictor
from immad.apps.substitution import SubstitutionValidator as Validator

from aiida import load_profile
load_profile('hung')

if __name__ == '__main__':

    # INITIALIZATION
    candidates = ['La'] 
    base_dir = os.path.dirname(os.path.abspath(__file__)) + '/test/substitution'
    material_structure_file = f'{base_dir}/Nd2Fe14B_mp-5182_conventional_standard.cif'
    materials = Materials(material_structure_file, candidates)

    model_directory = f'{base_dir}/models'
    predictor = Predictor(materials, model_directory)

    validator = Validator()
    
    materials.set_selected_atoms([10, 20, 5])

    # PREDICTION
    optimal_structures = []
    for samples in materials:
        print(samples)
        sample_scores, sample_info = predictor.evaluate(samples)
        if predictor.verify(sample_scores, sample_info):
            optimal_structures += predictor.generate_proposed_structures()

    # VALIDATION
#    for sample in optimal_structures:
#        validator.run(sample)
