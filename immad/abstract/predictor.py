class Predictor(object):
    """
    A class for predicting new material
    Basically it receives proposed structure, evaluate it,
    then decide whether to take it or not

    It should be an abstract class in the framework
    """
    def __init__(self):
        """
        Abstract class for constructor
        """

    def evaluate(self, proposed_sample):
        """
        Abstract class
        Evaluate (score) the proposed structure
        Input: 
            proposed_structure: the structured for evaluation
        Return:
            the score of the input structure
        """
        return 0.

    def verify(self, structure_score):
        """
        Abstract class
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


