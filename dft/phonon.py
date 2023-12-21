from aiida import orm
from aiida.common import AttributeDict, exceptions
from aiida.engine import ToContext, WorkChain, append_, if_, while_
from aiida.plugins import WorkflowFactory, DataFactory
from aiida.tools.data.array.kpoints import get_explicit_kpoints_path
from aiida_quantumespresso.workflows.protocols.utils import ProtocolMixin

PwBaseWorkChain = WorkflowFactory('quantumespresso.pw.base')
PhBaseWorkChain = WorkflowFactory('quantumespresso.ph.base')
Q2rBaseWorkChain = WorkflowFactory('quantumespresso.q2r.base')
MatdynBaseWorkChain = WorkflowFactory('quantumespresso.matdyn.base')

class PhononWorkChain(ProtocolMixin, WorkChain):
    """Workchain for phonon calculation using Quantum ESPRESSO."""

    @classmethod
    def define(cls, spec):
        """Define the process specification.

        In this workchain, four sub-workchain are included:
        PwBaseWorkChain, PhBaseWorkChain, Q2rBaseWorkChain, and
        MatdynBaseWorkChain.
        In the definition, inputs of these four sub-workchains are exposed
        to the inputs of this workchain.

        Args:
            cls (PhononWorkChain): the class itself
            spec (ProcessSpec): specifications
        """
        super().define(spec)

        spec.expose_inputs(PwBaseWorkChain, namespace='scf',
            namespace_options={'required': False, 'populate_defaults': False,
                'help': 'Inputs for the `PwBaseWorkChain` for the scf.'})
        spec.expose_inputs(PhBaseWorkChain, namespace='ph',
            exclude=['ph.parent_folder'],
            namespace_options={'required': False, 'populate_defaults': False,
                'help': 'Inputs for the `PhBaseWorkChain`.'})
        spec.expose_inputs(Q2rBaseWorkChain, namespace='q2r',
            exclude=['q2r.parent_folder'],
            namespace_options={'required': False, 'populate_defaults': False,
                'help': 'Inputs for the `Q2rBaseWorkChain`.'})
        spec.expose_inputs(MatdynBaseWorkChain, namespace='matdyn',
            exclude=['matdyn.force_constants'], 
            namespace_options={'required': False, 'populate_defaults': False,
                'help': 'Inputs for the `MatdynBaseWorkChain`.'})

        spec.input('structure', valid_type=orm.StructureData,
                   help='The inputs structure.')
        spec.input('run_scf', valid_type=orm.Bool,
                   default=lambda: orm.Bool(True),
                   help='A flag for running SCF calculation')
        spec.input('scf_folder', valid_type=orm.RemoteData, required=False,
                   help='Remote directory for pwSCF calculation')

        spec.expose_outputs(PwBaseWorkChain, namespace='scf')
        spec.expose_outputs(PhBaseWorkChain, namespace='ph')
        spec.expose_outputs(Q2rBaseWorkChain, namespace='q2r')
        spec.expose_outputs(MatdynBaseWorkChain, namespace='matdyn')

        spec.outline(
            if_(cls.should_run_scf)(
                cls.run_scf,
                cls.inspect_scf,
            ),
            cls.run_ph,
            cls.inspect_ph,
            cls.run_q2r,
            cls.inspect_q2r,
            cls.run_matdyn,
            cls.inspect_matdyn,
            cls.results,
        )
        spec.exit_code(401, 'ERROR_SUB_PROCESS_FAILED_SCF',
                       message='the scf PwBaseWorkChain sub process failed')
        spec.exit_code(402, 'ERROR_SUB_PROCESS_FAILED_PH',
                       message='the PhBaseWorkChain sub process failed')
        spec.exit_code(403, 'ERROR_SUB_PROCESS_FAILED_Q2R',
                       message='the Q2rBaseWorkChain sub process failed')
        spec.exit_code(404, 'ERROR_SUB_PROCESS_FAILED_MATDYN',
                       message='the MatdynBaseWorkChain sub process failed')

    @classmethod
    def get_builder_from_protocol(cls,
                                  pw_code, ph_code, q2r_code, matdyn_code,
                                  structure,
                                  protocol=None, overrides=None, options=None,
                                  **kwargs):
        """Obtain builder based on input protocols

        Construct the builder given protocols corresponding to PwBaseWorkChain
        and PhBaseWorkChain. However, Q2rBaseWorkChain and MatdynBaseWorkChain
        have no predefined protocol, thus the corresponding builders are
        constructed based on required input ports.

        Args:
            cls (PhononWorkChain): the class itself
            pw_code (InstalledCode): installed code for pw.x
            ph_code (InstalledCode): installed code for ph.x
            q2r_code (InstallledCode): installed code for q2r.x
            matdyn_code (InstalledCode): installed code for matdyn.x
            structure (StructureData): input crystal structure
            kmesh (list): k-mesh for SCF pw.x calculation
            qmesh (list): q-mesh for phonon ph.x calculation
            protocol (dict): a dictionary with keys 'scf' for PwBaseWorkChain protocol
                             and 'ph' for PhBaseWorkChain protocol
            overrides (dict): a dictionary with keys 'scf' for PwBaseWorkChain overrides
                              and 'ph' for PhBaseWorkChain overrides
            options (dict): predefined options for calculations

        Returns: the builder for running PhononWorkChain
        """
        if protocol is None:
            protocol = { 'scf': None, 'ph': None }
        if overrides is None:
            overrides = { 'scf': None, 'ph': None }

        builder = cls.get_builder()
        builder.structure = structure

        scf = PwBaseWorkChain.get_builder_from_protocol(
                pw_code, structure, protocol=protocol['scf'],
                overrides=overrides['scf'], options=options, **kwargs)
        scf.pw.parameters['CONTROL']['calculation'] = 'scf'
        builder.scf = scf

        ph = PhBaseWorkChain.get_builder_from_protocol(
                ph_code, protocol=protocol['ph'], overrides=overrides['ph'],
                options=options, **kwargs)
        builder.ph = ph

        builder.q2r.q2r.code = q2r_code
        if options:
            builder.q2r.q2r.metadata.options = options

        builder.matdyn.matdyn.code = matdyn_code
        if options:
            builder.matdyn.matdyn.metadata.options = options
        kpoints = get_explicit_kpoints_path(structure)['explicit_kpoints']
        builder.matdyn.matdyn.kpoints = kpoints

        return builder

    def should_run_scf(self):
        """Check if one needs to run SCF calculation

        Check if SCF calculation via PwBaseWorkChain is necessary.

        Returns: boolean for running SCF or not.
        """
        if not self.inputs.run_scf.value:
            if 'scf_folder' not in self.inputs:
                self.report('Need scf_folder as input for ignoring SCF calculation. '
                            'We still run SCF calculation')
                self.ctx.run_scf = True
                return self.ctx.run_scf
            else:
                self.report('Ignore running SCF calculation')
        self.ctx.run_scf = self.inputs.run_scf.value
        return self.ctx.run_scf

    def run_scf(self):
        """Run SCF calculation using pw.x (via PwBaseWorkChain)."""
        inputs = AttributeDict(self.exposed_inputs(PwBaseWorkChain,
                                                   namespace='scf'))
        running = self.submit(PwBaseWorkChain, **inputs)

        self.report(f'launching PwBaseWorkChain<{running.pk}> for scf')
        return ToContext(workchain_scf=running)

    def inspect_scf(self):
        """Inspect if the SCF calculation is successful."""
        if not self.ctx.workchain_scf.is_finished_ok:
            self.report('scf PwBaseWorkChain failed with exit status '
                        f'{self.ctx.workchain_scf.exit_status}')
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_SCF

    def run_ph(self):
        """Run phonon calculation using ph.x (via PhBaseWorkChain)."""
        inputs = AttributeDict(self.exposed_inputs(PhBaseWorkChain,
                                                   namespace='ph'))
        if not self.ctx.run_scf:
            inputs.ph.parent_folder = self.inputs.scf_folder
        else:
            inputs.ph.parent_folder = self.ctx.workchain_scf.outputs.remote_folder
        running = self.submit(PhBaseWorkChain, **inputs)
        self.report(f'launching PhBaseWorkChain<{running.pk}> '
                    'for ph.x calculation')
        return ToContext(workchain_ph=running)

    def inspect_ph(self):
        """Inspect if the phonon calculation is successful."""
        if not self.ctx.workchain_ph.is_finished_ok:
            self.report('PhBaseWorkChain failed with exit status '
                        f'{self.ctx.workchain_ph.exit_status}')
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_PH

    def run_q2r(self):
        """q -> r transformation using q2r.x (via Q2rBaseWorkChain)."""
        inputs = AttributeDict(self.exposed_inputs(Q2rBaseWorkChain,
                                                   namespace='q2r'))
        inputs.q2r.parent_folder = self.ctx.workchain_ph.outputs.remote_folder
        running = self.submit(Q2rBaseWorkChain, **inputs)
        self.report(f'launching Q2rBaseWorkChain<{running.pk}> '
                    'for q2r.x calculation')
        return ToContext(workchain_q2r=running)

    def inspect_q2r(self):
        """Inspect if the q -> r transformation is successful."""
        if not self.ctx.workchain_q2r.is_finished_ok:
            self.report('PhBaseWorkChain failed with exit status '
                        f'{self.ctx.workchain_ph.exit_status}')
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_Q2R

    def run_matdyn(self):
        """Construct the dynamical matrix using matdyn.x (via MatdynBaseWorkChain)."""
        inputs = AttributeDict(self.exposed_inputs(MatdynBaseWorkChain,
                                                   namespace='matdyn'))
        force_constants = self.ctx.workchain_q2r.outputs.force_constants
        inputs.matdyn.force_constants = force_constants
        running = self.submit(MatdynBaseWorkChain, **inputs)
        self.report(f'launching MatdynBaseWorkChain<{running.pk}> '
                    'for matdyn.x calculation')
        return ToContext(workchain_matdyn=running)

    def inspect_matdyn(self):
        """Inspect the process of constructing the dynamical matrix."""
        if not self.ctx.workchain_ph.is_finished_ok:
            self.report('MatdynBaseWorkChain failed with exit status '
                        f'{self.ctx.workchain_matdyn.exit_status}')
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_MATDYN

    def results(self):
        """The results by exposing outputs of each of the four sub-workchains."""
        if self.ctx.run_scf:
            self.out_many(self.exposed_outputs(self.ctx.workchain_scf,
                                               PwBaseWorkChain,
                                               namespace='scf'))
        self.out_many(self.exposed_outputs(self.ctx.workchain_ph,
                                           PhBaseWorkChain,
                                           namespace='ph'))
        self.out_many(self.exposed_outputs(self.ctx.workchain_q2r,
                                           Q2rBaseWorkChain,
                                           namespace='q2r'))
        self.out_many(self.exposed_outputs(self.ctx.workchain_matdyn,
                                           MatdynBaseWorkChain,
                                           namespace='matdyn'))

    def on_terminated(self):
        """Overloaded method for terminating the workchain."""
        super().on_terminated()
