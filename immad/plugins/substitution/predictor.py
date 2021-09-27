import numpy as np
from itertools import product
from tensorflow.keras.models import load_model

from . import ofm
from immad.abstract import Predictor
from aiida.plugins import DataFactory

class SubstitutionPredictor(Predictor):
    def __init__(self, host_material, model_dir):
        """
        Input: 
            model_dir: directory containing pretrained models
        """
        Predictor.__init__(self)

        number_neurons = [4, 8, 16, 32]
        neural_activations = ['relu', 'sigmoid', 'tanh']
        self.models = [load_model(f'{model_dir}/{nn}_{act}_ofm0_rand_neg.h5')
                for nn, act in product(number_neurons, neural_activations)]
        self.host = host_material
        
        # verification parameters
        self.prob_threshold = 0.6
        self.max_optimal_choices = 2

    def evaluate(self, proposed_sample):
        self.candidate = proposed_sample
        candidate_rep = ofm.get_element_representation(proposed_sample)
        data = ofm.local_structure_query(struct=self.host.get_structure())
        x_env = []
        for pair in data['local']:
            x_env.append(pair['env1'])
        x_env = np.array(x_env)

        pair_idx = np.array(np.arange(x_env.shape[0]))
        x_center_to_replace = []
        x_env_for_replace = []
        for idx in pair_idx:
            x_center_to_replace.append(candidate_rep)
            x_env_for_replace.append(x_env[idx])
        x_center_to_replace = np.array(x_center_to_replace)
        x_env_for_replace = np.array(x_env_for_replace)

        p = [model.predict([x_center_to_replace, x_env_for_replace]).ravel()
                for model in self.models]
        p = np.mean(p, axis=0)
        return p, pair_idx

    def verify(self, sample_scores, sample_info):
        # TODO: Hung: one may consider lattice symmetry to further remove
        # symmetrically equivalent substitutions
        chosen_ind = np.argsort(sample_scores)[::-1][:self.max_optimal_choices]
        chosen_ind = chosen_ind[sample_scores[chosen_ind] > self.prob_threshold]
        final_choices = []
        host_struct = self.host.get_structure()
        for ind in chosen_ind:
            i_source = sample_info[ind]
            if str(host_struct[i_source].species_string) != self.candidate:
                final_choices.append(ind)
        if len(final_choices) > 0:
            self.optimal_choices = np.array(sample_info)[final_choices]
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
