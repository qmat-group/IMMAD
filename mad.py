# initial backbone of IMMAD
# specifically for Nd2Fe14B substitution problem
# following Lam's paper

import random


class Materials(object):
    """
    A class characterizing materials under investigation
    Purposes:
        General purposes:
            provides methods and properties for common activity such as 
            export material structures, lattice constant, symmetry ...
            Only implement methods that we needs
            Complicated methods: consider open-source
        Specific purposes: design for specific problem
            Therefore, eventually there will be a parent (abstract) class
            and for each problem, one should develop a child class accordingly
    In this case, we first develop the class for the substitution problem
    """
    def __init__(self, material_structure, rare_earths, transition_metals):
        """
        Initialize the class with input for the substitution problem
            material_structure: the structure of Nd2Fe14B
                TODO: format of the structure
            rare_earths: the set of rare-earth elements for substitution
            transition_metals: the set of transition metals for substitution
        """
        self.structure = material_structure
        self.re_set = rare_earths
        self.tm_set = transition_metals

    # TODO: develop an iterator for proposing new structure for evaluation
    #       this iterator has two methods __iter__ and __next__
    #       they should be abstract in the parent class
    #       and designed specifically for each problem (in the child class)
    def __iter__(self):
        """
        Return the iterator for the materials set
        """
        # TODO: set to the starting point of the list before iterating
        self.re_index = 0
        self.tm_index = 0
        return self

    def __next__(self):
        """
        Return the next item of the materials set
        """
        self.tm_index += 1
        if self.tm_index == len(self.tm_set):
            self.re_index += 1
            self.tm_index = 0
            if self.re_index == len(self.re_set):
                raise StopIteration
        return self.re_set[self.re_index], self.tm_set[self.tm_index]


class Predictor(object):
    """
    A class for predicting new material
    Basically it receives proposed structure, evaluate it,
    then decide whether to take it or not

    It should be an abstract class in the framework
    """
    def __init__(self, model):
        """
        Input: 
            model: pretrained model for structural evaluation
        """
        self.model = model

    def evaluate(self, proposed_structure):
        """
        Evaluate (score) the proposed structure
        Input: 
            proposed_structure: the structured for evaluation
        Return:
            the score of the input structure
        """
        # TODO: should we impose a specific type for the return value?
        score = self.model(proposed_structure)
        return score

    def verify(self, structure_score):
        """
        Justify if the input score (for a given structure) satisfies criteria 
        for being an optimal structure
        Input:
            structure_score: the score of the given structure
                             obtained from evaluate method
        Return:
            True: yes, an optimal structure
            False: no, not an optimal one
        """
        # TODO: require reimplementing
        # at current stage, assume the score ranging from 0 to 1,
        # and the threshold 0.5 for simplicity
        threshold = 0.5
        if structure_score > threshold:
            return True
        else:
            return False


class Validator(object):
    """
    Abstract class for running high-throughput calculations
    (or equivalent activity) to validate predicted result
    """
    def __init__(self):
        """
        Initialize the validator
        """
        pass

    def run(self, sample):
        """
        Call high-throughput calculations given the input structure
        """
        pass


if __name__ == '__main__':
    # INPUT
    rare_earths = ['La', 'Ce', 'Pr', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb',
                   'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']
    transition_metals = ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Co', 'Ni', 'Cu', 'Zn',
                         'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag',
                         'Cd', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au']
    # TODO: provide Nd2Fe14B structure into a variable named "mat_structure"
    mat_structure = None

    materials = Materials(mat_structure, rare_earths, transition_metals)
    model = lambda x: random.random()
    predictor = Predictor(model) # TODO: @Lam: provide me the pretrained model
    validator = Validator()


    # PREDICTION
    optimal_structures = []
    for sample in materials:
        score = predictor.evaluate(sample)
        if predictor.verify(score):
            optimal_structures.append(sample)


    # VALIDATION
    for sample in optimal_structures:
        validator.run(sample)
