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


