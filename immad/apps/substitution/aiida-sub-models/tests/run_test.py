import numpy as np
import os
from pathlib import Path

from aiida import engine, orm
from aiida.plugins import CalculationFactory

from aiida import load_profile

if __name__ == '__main__':
    load_profile('hung')
    INPUT_DIR = Path(__file__).resolve().parent
    os.chdir(INPUT_DIR)

    computer = orm.load_computer('pias')
    code = orm.load_code('immad.sub@pias')

    builder = code.get_builder()
    builder.center = orm.SinglefileData(file=INPUT_DIR / 'x_center.npy')
    builder.env = orm.SinglefileData(file=INPUT_DIR / 'x_env.npy')
    builder.metadata.description = 'My first AiiDA plugin'

    result = engine.run(builder)
    print(result)