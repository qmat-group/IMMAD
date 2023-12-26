from aiida.plugins import WorkflowFactory
from aiida.common import AttributeDict
from aiida.engine import submit, ToContext, WorkChain, if_
from aiida import orm
from aiida_quantumespresso.workflows.protocols.utils import ProtocolMixin
from .phonon import PhononWorkChain

PwBaseWorkChain = WorkflowFactory('quantumespresso.pw.base')
PwRelaxWorkChain = WorkflowFactory('quantumespresso.pw.relax')
PwBandsWorkChain = WorkflowFactory('quantumespresso.pw.bands')
PdosWorkChain = WorkflowFactory('quantumespresso.pdos')

class DFTWorkChain(ProtocolMixin, WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)

        # input parameters
        spec.expose_inputs(PwBaseWorkChain, namespace='scf')
        spec.expose_inputs(PwRelaxWorkChain, namespace='relax')
        spec.expose_inputs(PwBandsWorkChain, namespace='bands')
        spec.expose_inputs(PdosWorkChain, namespace='dos')
        spec.expose_inputs(PhononWorkChain, namespace='phonon')

        spec.expose_outputs(PwBaseWorkChain, namespace='scf')
        spec.expose_outputs(PwRelaxWorkChain, namespace='relax')
        spec.expose_outputs(PwBandsWorkChain, namespace='bands')
        spec.expose_outputs(PdosWorkChain, namespace='dos')
        spec.expose_outputs(PhononWorkChain, namespace='phonon')

        spec.input('structure', required=True, valid_type=orm.StructureData,
                   help='The inputs structure.')
        spec.input('want_relax', default=lambda: orm.Bool(False),
                   valid_type=orm.Bool, help='Enable relaxation calculation')
        spec.input('want_bands', default=lambda: orm.Bool(False),
                   valid_type=orm.Bool, help='Enable band calculation')
        spec.input('want_dos', default=lambda: orm.Bool(False),
                   valid_type=orm.Bool, help='Enable PDOS calculation')
        spec.input('want_phonon', default=lambda: orm.Bool(False),
                   valid_type=orm.Bool, help='Enable phonon calculation')

        spec.output('structure', valid_type=orm.StructureData, required=True,
                    help='The output crystal structure.')
        spec.output('scf_parameters', valid_type=orm.Dict, required=True,
                    help='Output parameters for the pwSCF calculation.')

        # outline
        spec.outline(
            cls.setup,
            if_(cls.is_relax_enabled)(
                cls.run_relax,
                cls.inspect_relax
            ),
            cls.run_scf,
            cls.inspect_scf,
            if_(cls.is_bands_enabled)(
                cls.run_bands,
                cls.inspect_bands
            ),
            if_(cls.is_dos_enabled)(
                cls.run_dos,
                cls.inspect_dos
            ),
            if_(cls.is_phonon_enabled)(
                cls.run_phonon,
                cls.inspect_phonon
            ),
            cls.finalize
        )

        spec.exit_code(400, 'ERROR_DFT_PROCESS_FAILED_SCF',
                       message='the PwBaseWorkChain sub process failed')
        spec.exit_code(401, 'ERROR_DFT_PROCESS_FAILED_RELAX',
                       message='the PwRelaxWorkChain sub process failed')
        spec.exit_code(402, 'ERROR_DFT_PROCESS_FAILED_BANDS',
                       message='the PwBandsWorkChain sub process failed')
        spec.exit_code(403, 'ERROR_DFT_PROCESS_FAILED_DOS',
                       message='the PdosWorkChain sub process failed')
        spec.exit_code(404, 'ERROR_DFT_PROCESS_FAILED_PHONON',
                       message='the PhononWorkChain sub process failed')

    @classmethod
    def get_builder_from_protocol(cls, pw_code, dos_code, projwfc_code,
                                  ph_code, q2r_code, matdyn_code,
                                  structure, overrides: dict={}, options=None,
                                  protocol=None, **kwargs):
        relax_overrides = bands_overrides = None
        dos_overrides = phonon_overrides = None
        scf_overrides = None
        if 'scf' in overrides:
            scf_overrides = overrides['scf']
        if 'relax' in overrides:
            relax_overrides = overrides['relax']
        if 'bands' in overrides:
            bands_overrides = overrides['bands']
        if 'dos' in overrides:
            dos_overrides = overrides['dos']
        if 'phonon' in overrides:
            phonon_overrides = overrides['phonon']

        scf = PwBaseWorkChain.get_builder_from_protocol(
                pw_code, structure, protocol, overrides=scf_overrides,
                options=options, **kwargs)
        relax = PwRelaxWorkChain.get_builder_from_protocol(
                pw_code, structure, protocol, overrides=relax_overrides,
                options=options, **kwargs)
        bands = PwBandsWorkChain.get_builder_from_protocol(
                pw_code, structure, protocol, overrides=bands_overrides,
                options=options, **kwargs)
        dos_options = options.copy()
        num_machines = 1
        tot_num_mpiprocs = min(8, dos_options['resources']['tot_num_mpiprocs'])
        dos_options['resources'] = {
                'num_machines': num_machines,
                'tot_num_mpiprocs': tot_num_mpiprocs
                }
        dos = PdosWorkChain.get_builder_from_protocol(
                pw_code, dos_code, projwfc_code,
                structure, protocol, overrides=dos_overrides,
                options=dos_options, **kwargs)
        phonon = PhononWorkChain.get_builder_from_protocol(
                pw_code, ph_code, q2r_code, matdyn_code,
                structure,
                protocol, phonon_overrides, options, **kwargs)

        relax.pop('base_final_scf', None)
        bands.pop('relax', None)
        dos.pop('scf', None)
        dos['nscf']['pw']['parent_folder'] = None #orm.Data()
        phonon.pop('scf', None)
        phonon.run_scf = orm.Bool(False)

        builder = cls.get_builder()
        builder.relax = relax
        builder.scf = scf
        builder.bands = bands
        builder.dos = dos
        builder.phonon = phonon
        builder.structure = structure

        return builder

    def setup(self):
        self.ctx.current_structure = self.inputs.structure

    def is_relax_enabled(self):
        return self.inputs['want_relax']
   
    def run_relax(self):
        inputs = AttributeDict(self.exposed_inputs(PwRelaxWorkChain,
                                                   namespace='relax'))
        inputs.structure = self.ctx.current_structure
        inputs.metadata.call_link_label = 'relax'
        future = self.submit(PwRelaxWorkChain, **inputs)
        self.report(f'launching PwRelaxWorkChain<{future.pk}>')
        return ToContext(relax=future)

    def inspect_relax(self):
        """Inspect the process of relax calculation."""
        if not self.ctx.relax.is_finished_ok:
            self.report('PwRelaxWorkChain failed with exit status '
                        f'{self.ctx.relax.exit_status}')
            return self.exit_codes.ERROR_DFT_PROCESS_FAILED_RELAX
        relaxed_structure = self.ctx.relax.outputs.output_structure
        self.ctx.current_structure = relaxed_structure

    def run_scf(self):
        inputs = AttributeDict(self.exposed_inputs(PwBaseWorkChain,
                                                   namespace='scf'))
        inputs.pw.structure = self.ctx.current_structure
        inputs.metadata.call_link_label = 'scf'
        future = self.submit(PwBaseWorkChain, **inputs)
        self.report(f'launching PwBaseWorkChain<{future.pk}>')
        return ToContext(scf=future)

    def inspect_scf(self):
        """Inspect the process of bands calculation."""
        if not self.ctx.scf.is_finished_ok:
            self.report('PwBaseWorkChain failed with exit status '
                        f'{self.ctx.scf.exit_status}')
            return self.exit_codes.ERROR_DFT_PROCESS_FAILED_SCF
        self.ctx.scf_folder = self.ctx.scf.outputs.remote_folder
 
    def is_bands_enabled(self):
        return self.inputs['want_bands']
    
    def run_bands(self):
        inputs = AttributeDict(self.exposed_inputs(PwBandsWorkChain,
                                                   namespace='bands'))
        inputs.structure = self.ctx.current_structure
        inputs.metadata.call_link_label = 'bands'
        future = self.submit(PwBandsWorkChain, **inputs)
        self.report(f'launching PwBandsWorkChain<{future.pk}>')
        return ToContext(bands=future)

    def inspect_bands(self):
        """Inspect the process of bands calculation."""
        if not self.ctx.bands.is_finished_ok:
            self.report('PwBandsWorkChain failed with exit status '
                        f'{self.ctx.bands.exit_status}')
            return self.exit_codes.ERROR_DFT_PROCESS_FAILED_BANDS
   
    def is_dos_enabled(self):
        return self.inputs['want_dos']
    
    def run_dos(self):
        inputs = AttributeDict(self.exposed_inputs(PdosWorkChain, namespace='dos'))
        inputs.structure = self.ctx.current_structure
        inputs.nscf.pw.parent_folder = self.ctx.scf_folder
        inputs.metadata.call_link_label = 'dos'
        future = self.submit(PdosWorkChain, **inputs)
        self.report(f'launching PdosWorkChain<{future.pk}>')
        return ToContext(dos=future)

    def inspect_dos(self):
        """Inspect the process of DOS calculation."""
        if not self.ctx.dos.is_finished_ok:
            self.report('PdosWorkChain failed with exit status '
                        f'{self.ctx.dos.exit_status}')
            return self.exit_codes.ERROR_DFT_PROCESS_FAILED_DOS

    def is_phonon_enabled(self):
        return self.inputs['want_phonon']

    def run_phonon(self):
        inputs = AttributeDict(self.exposed_inputs(PhononWorkChain,
                                                   namespace='phonon'))
        inputs.structure = self.ctx.current_structure
        inputs.scf_folder = self.ctx.scf_folder
        inputs.metadata.call_link_label = 'phonon'
        future = self.submit(PhononWorkChain, **inputs)
        self.report(f'launching PhononWorkChain<{future.pk}>')
        return ToContext(phonon=future)

    def inspect_phonon(self):
        """Inspect the process of phonon calculation."""
        if not self.ctx.phonon.is_finished_ok:
            self.report('PhononWorkChain failed with exit status '
                        f'{self.ctx.phonon.exit_status}')
            return self.exit_codes.ERROR_DFT_PROCESS_FAILED_PHONON

    def finalize(self):
        if self.is_relax_enabled():
            self.out_many(self.exposed_outputs(self.ctx.relax,
                                               PwRelaxWorkChain,
                                               namespace='relax'))
        if self.is_bands_enabled():
            self.out_many(self.exposed_outputs(self.ctx.bands,
                                               PwBandsWorkChain,
                                               namespace='bands'))
        if self.is_dos_enabled():
            self.out_many(self.exposed_outputs(self.ctx.dos,
                                               PdosWorkChain,
                                               namespace='dos'))
        if self.is_phonon_enabled():
            self.out_many(self.exposed_outputs(self.ctx.phonon,
                                               PhononWorkChain,
                                               namespace='phonon'))
        self.out_many(self.exposed_outputs(self.ctx.scf,
                                           PwBaseWorkChain,
                                           namespace='scf'))

        self.out('structure', self.ctx.current_structure)
        self.out('scf_parameters', self.ctx.scf.outputs.output_parameters)

    def on_terminated(self):
        super().on_terminated()
