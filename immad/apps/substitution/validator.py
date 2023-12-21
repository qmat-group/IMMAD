from aiida.engine import submit
from aiida import orm
from immad.abstract import Validator
from first_principle import DFTWorkChain

class SubstitutionValidator(Validator):
    def __init__(self):
        Validator.__init__(self)

        pw = orm.load_code('pw@phpc')
        dos = orm.load_code('dos@phpc')
        projwfc = orm.load_code('projwfc@phpc')
        ph = orm.load_code('ph@phpc')
        q2r = orm.load_code('q2r@phpc')
        matdyn = orm.load_code('matdyn@phpc')
        self.codes = (pw, dos, projwfc, ph, q2r, matdyn)

        self.options = {
                'resources': {
                    'num_machines': 1,
                    'tot_num_mpiprocs': 8,
                    },
                'max_wallclock_seconds': 18000,
                'withmpi': True,
                }
        self.relax = self.bands = self.dos = self.phonon = False
    
    def set_relax(self, value: bool):
        self.relax = value

    def set_bands(self, value: bool):
        self.bands = value

    def set_dos(self, value: bool):
        self.dos = value

    def set_phonon(self, value: bool):
        self.phonon = value

    def run(self, sample):
        struct = sample['struct']
        builder = DFTWorkChain.get_builder_from_protocol(
                *self.codes, struct, options=self.options)
        builder.want_relax = orm.Bool(self.relax)
        builder.want_bands = orm.Bool(self.bands)
        builder.want_dos = orm.Bool(self.dos)
        builder.want_phonon = orm.Bool(self.phonon)
        node = submit(builder)
        print(f'Calculation: {node.process_class}<{node.pk}>')
        return node
