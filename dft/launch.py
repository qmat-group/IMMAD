from aiida import engine, orm

from first_principle import DFTWorkChain

if __name__ == '__main__':
    pw = orm.load_code('pw@phpc')
    dos = orm.load_code('dos@phpc')
    projwfc = orm.load_code('projwfc@phpc')
    ph = orm.load_code('ph@phpc')
    q2r = orm.load_code('q2r@phpc')
    matdyn = orm.load_code('matdyn@phpc')

    options = {
            'resources': {
                'num_machines': 1,
                'tot_num_mpiprocs': 16,
                },
            'max_wallclock_seconds': 18000,
            'withmpi': True,
            }

    structure = orm.load_node(pk=339)
    structure = orm.load_node(pk=4408)
    builder = DFTWorkChain.get_builder_from_protocol(
        pw, dos, projwfc, ph, q2r, matdyn, structure,
        options=options
        )

    builder.want_relax = orm.Bool(False)
    builder.want_bands = orm.Bool(True)
    builder.want_dos = orm.Bool(True)
    builder.want_phonon = orm.Bool(False)

    node = engine.run(builder)
    print(node)
