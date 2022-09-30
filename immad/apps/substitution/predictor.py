from pathlib import Path
import numpy as np
from itertools import product

from . import ofm
from immad.abstract import Predictor

from aiida.plugins import DataFactory
from aiida import engine
from aiida import orm

class SubstitutionPredictor(Predictor):
    def __init__(self, host_material, model_dir):
        """
        Input: 
            model_dir: directory containing pretrained models
        """
        Predictor.__init__(self)

        self.host = host_material
        
        # verification parameters
        self.prob_threshold = 0.6
        self.max_optimal_choices = 2
        
        # AiiDA code
        self.computer = orm.load_computer('pias')
        self.code = orm.load_code('immad.sub@pias')
        self.builder = self.code.get_builder()

    def evaluate(self, proposed_sample):
        x_center_fn = 'x_center.npy'
        x_env_fn = 'x_env.npy'
        
        self.candidate = proposed_sample[0]
        self.substituted_atoms = proposed_sample[1]
        
        candidate_rep = ofm.get_element_representation(self.candidate)
        # look up from get_structure to get the list of atoms
        # read ofm.py line 46 
        data = ofm.local_structure_query(struct=self.host.get_structure())
        x_env = []
        for pair in data['local']:
            x_env.append(pair['env1'])
        x_env = np.array(x_env)

        # select appropriate rows for substitution
        #pair_idx = np.array(np.arange(x_env.shape[0]))
        if len(self.substituted_atoms) == 0:
            self.substituted_atoms = np.array(np.arange(x_env.shape[0]))
        x_center_to_replace_arr = []
        x_env_for_replace_arr = []
        #for idx in pair_idx:
        for idx in self.substituted_atoms:
            x_center_to_replace_arr.append(candidate_rep)
            x_env_for_replace_arr.append(x_env[idx])
        np.save(x_center_fn, x_center_to_replace_arr)
        np.save(x_env_fn, x_env_for_replace_arr)

        # AiIDA remote process
        path_to_file = Path(x_center_fn).parent.absolute()
        self.builder.center = orm.SinglefileData(file=path_to_file/x_center_fn)
        self.builder.env = orm.SinglefileData(file=path_to_file/x_env_fn)
        result = engine.run(self.builder)
        p = result['scores'].get_array('matrix')
        
        return p, (self.candidate, self.substituted_atoms)

    def verify(self, sample_scores, sample_info):
        # TODO: Hung: one may consider lattice symmetry to further remove
        # symmetrically equivalent substitutions
        chosen_ind = np.argsort(sample_scores)[::-1][:self.max_optimal_choices]
        chosen_ind = chosen_ind[sample_scores[chosen_ind] > self.prob_threshold]
        final_choices = []
        host_struct = self.host.get_structure()
        for ind in chosen_ind:
            i_source = sample_info[1][ind]
            if str(host_struct[i_source].species_string) != self.candidate:
                final_choices.append(ind)
        if len(final_choices) > 0:
            self.optimal_choices = np.array(sample_info[1])[final_choices]
            self.optimal_scores = sample_scores[final_choices]
            return True
        else:
            return False

    def generate_proposed_structures(self):
        StructureData = DataFactory('structure')
        substitutions = []
        host_struct = self.host.get_structure()
        for n, i_src in enumerate(self.optimal_choices):
            i_src = int(i_src)
            a = host_struct.copy()
            a[i_src] = self.candidate
            substitutions.append({
                    'struct': StructureData(pymatgen=a),
                    'proba': self.optimal_scores[n],
                    })
        return substitutions
