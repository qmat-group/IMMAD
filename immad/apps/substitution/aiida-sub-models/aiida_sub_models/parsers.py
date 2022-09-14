from unittest import result
import numpy as np

from aiida.common import datastructures, exceptions
from aiida.orm import ArrayData
from aiida.parsers import Parser
from aiida.engine import ExitCode

from .calculations import TensorflowCalculation

class TensorflowParser(Parser):
    def __init__(self, node):
        """Initialize the Parser instance

        Args:
            node (ProcessNode): the process node of the calculation
        """
        super().__init__(node)
        if not issubclass(node.process_class, TensorflowCalculation):
            raise exceptions.ParsingError('It can only parse TensorflowCalculation')

    def parse(self, **kwargs):
        retrieved_temporary_folder = kwargs['retrieved_temporary_folder']
        result_filename = self.node.get_option('result_filename')
        arr = np.load(f'{retrieved_temporary_folder}/{result_filename}')
        output_node = ArrayData()
        output_node.set_array('matrix', arr)
        self.out('scores', output_node)
        return ExitCode(0)