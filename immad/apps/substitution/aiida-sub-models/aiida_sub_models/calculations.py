import numpy as np

from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import ArrayData, SinglefileData

class TensorflowCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the prediction process using Tensorflow models
    """
    
    @classmethod
    def define(self, spec):
        """Define the input and output of the calculation

        Args:
            spec (ProcessSpec): specifications required for the calculation
        """

        super().define(spec)
        spec.inputs['metadata']['options']['parser_name'].default = 'sub-models'
        spec.inputs['metadata']['options']['resources'].default = {
            'num_machines' : 1,
            'num_mpiprocs_per_machine' : 1,

            # 'parallel_env' : 'smp',
            # 'tot_num_mpiprocs' : 1,
        }
        spec.input('center', valid_type=SinglefileData,
                   help='x_center_to_replace')
        spec.input('env', valid_type=SinglefileData,
                   help='x_env_for_replace')
        spec.input('metadata.options.result_filename',
                   valid_type=str, default='result.npy')
        spec.input('metadata.options.output_filename',
                   valid_type=str, default='output')
        spec.output('scores', valid_type=ArrayData,
                    help='Scores obtained from prediction')

    def prepare_for_submission(self, folder):
        """Prepare for running the external code (ML model prediction)

        Args:
            folder (_type_): _description_

        Returns:
            _type_: further information of the calculation
        """
        center_fn = self.inputs.center.filename
        env_fn = self.inputs.env.filename
        
        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename
        codeinfo.cmdline_params = [center_fn, env_fn]
        
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [(self.inputs.center.uuid, center_fn, center_fn), 
                                    (self.inputs.env.uuid, env_fn, env_fn)]
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_temporary_list = [self.metadata.options.result_filename]
        return calcinfo