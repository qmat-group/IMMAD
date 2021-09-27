from pymatgen.core import Structure

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
    def __init__(self, material_structure_file, candidates):
        """
        Initialize the class with input for the substitution problem
            material_structure_file: the file for the structure of Nd2Fe14B
            candidates: all potential elements for substitution
        """
        self.structure = Structure.from_file(material_structure_file)
        if type(candidates) != list:
            candidates = [candidates]
        self.candidates = candidates

    def __iter__(self):
        """
        Return the iterator for the materials set
        """
        self.candidate_index = 0
        return self

    def __next__(self):
        """
        Return the next item of the materials set
        """
        if self.candidate_index < len(self.candidates):
            ret = self.candidates[self.candidate_index]
            self.candidate_index += 1
            return ret
        else:
            raise StopIteration

    def get_structure(self):
        """
        Getter for self.structure
        """
        return self.structure

    def get_candidates(self):
        """
        Getter for self.candidates
        """
        return self.candidates
