from immad.abstract import Materials

from .predictor import SubstitutionPredictor as Predictor
from .validator import SubstitutionValidator as Validator

__all__ = [
        'Validator', 'Predictor', 'run_immad'
        ]

def run_immad(input_structure, candidates, atoms_for_substituted,
              validate=False):
    """
    Run the IMMAD workflow for prediction and validation of
    optimal structures obtained by atomic substitutions.

    Args:
        input_structure: Original crystal structure
        candidates (list): Chemical elements used for substitution
        atoms_for_substituted (list): List of atomic indices (integer)
            of atoms for substitution

    Returns:
        list: Each element is a tuple of optimal structure,
            its ML score and the actual substitution
    """
    # INITIALIZATION
    materials = Materials(input_structure, candidates)
    
    predictor = Predictor(materials)

    materials.set_selected_atoms(atoms_for_substituted)

    # PREDICTION
    optimal_structures = []
    for samples in materials:
        sample_scores, sample_info = predictor.evaluate(samples)
        if predictor.verify(sample_scores, sample_info):
            optimal_structures += predictor.generate_proposed_structures()
            
    # VALIDATION
    if validate:
        validator = Validator()
        for sample in optimal_structures:
            validator.run(sample)

    return optimal_structures
