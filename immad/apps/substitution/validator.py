from aiida.engine import submit
from aiida.plugins import WorkflowFactory
from immad.abstract import Validator

class SubstitutionValidator(Validator):
    def __init__(self):
        Validator.__init__(self)
#        RelaxWorkChain = WorkflowFactory('common_workflows.relax.quantum_espresso')
#        self.input_generator = RelaxWorkChain.get_input_generator()

    def run(self, sample):
        structure = sample['struct']
        engines = {
                'relax' : {
                    # FIXME: Hung: hard-coded
                    'code' : 'qe-6.5-pw@pias',
                    'options' : {
                        'resources' : {
                            'tot_num_mpiprocs' : 12,
                            'parallel_env' : 'mpi'
                            },
                        'max_wallclock_seconds' : 100
                        }
                    }
                }
        builder = self.input_generator.get_builder(
                structure=structure, protocol='fast',
                engines=engines, relax_type='none')

        # FIXME: Hung: aiida-common-workflow assumes the scheduler is
        # either PBS or SLURM with parameter "num_machines" always exist
        # The two lines below is for SGE cluster by deleting "num_machines"
        # If you are using PBS or SLURM, please comment these two lines
        del builder.base_final_scf.pw.metadata.options.resources['num_machines']
        del builder.base.pw.metadata.options.resources['num_machines']

        submit(builder)
