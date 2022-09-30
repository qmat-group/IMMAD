import re
import numpy as np

from pymatgen.analysis.local_env import VoronoiNN
import pymatgen as pm

__all__ = ['get_element_representation', 'local_structure_query']

def get_element_representation(name='Si'):
    """
    generate one-hot representation for a element, e.g, si = [0.0, 1.0, 0.0, 0.0, ...]
    :param name: element symbol
    """
    element = pm.core.Element(name)
    general_element_electronic = {'s1': 0.0, 's2': 0.0, 'p1': 0.0, 'p2': 0.0, 'p3': 0.0,
                                  'p4': 0.0, 'p5': 0.0, 'p6': 0.0,
                                  'd1': 0.0, 'd2': 0.0, 'd3': 0.0, 'd4': 0.0, 'd5': 0.0,
                                  'd6': 0.0, 'd7': 0.0, 'd8': 0.0, 'd9': 0.0, 'd10': 0.0,
                                  'f1': 0.0, 'f2': 0.0, 'f3': 0.0, 'f4': 0.0, 'f5': 0.0, 'f6': 0.0, 'f7': 0.0,
                                  'f8': 0.0, 'f9': 0.0, 'f10': 0.0, 'f11': 0.0, 'f12': 0.0, 'f13': 0.0, 'f14': 0.0}

    general_electron_subshells = ['s1', 's2', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6',
                                  'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'd10',
                                  'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7',
                                  'f8', 'f9', 'f10', 'f11', 'f12', 'f13', 'f14']

    if name == 'H':
        element_electronic_structure = ['s1']
    elif name == 'He':
        element_electronic_structure = ['s2']
    else:
        element_electronic_structure = [
                ''.join(pair) for pair in re.findall('\.\d(\w+)(\d+)',
                                                     element.electronic_structure)
                                        ]
    for eletron_subshell in element_electronic_structure:
        general_element_electronic[eletron_subshell] = 1.0
    return np.array([general_element_electronic[key] for key in general_electron_subshells])


def local_structure_query(struct):
    """
    Calculate descriptor  for a pymatgen structure object
    """

    atoms = np.array([site.species_string for site in struct])

    local_xyz = []
    pairs = []

    for i_atom, atom in enumerate(atoms):

        coordinator_finder = VoronoiNN(cutoff=10.0)
        neighbors = coordinator_finder.get_nn_info(structure=struct, n=i_atom)

        site = struct[i_atom]
        center_vector = get_element_representation(atom)
        env_vector_1 = np.zeros(32)
        env_vector_0 = np.zeros(32)

        atom_xyz = [atom]
        coords_xyz = [site.coords]

        for nn in neighbors:
            site_x = nn['site']
            w = nn['weight']
            site_x_label = site_x.species_string
            atom_xyz += [site_x_label]
            coords_xyz += [site_x.coords]
            neigh_vector = get_element_representation(site_x_label)
            d = np.sqrt(np.sum((site.coords - site_x.coords) ** 2))
            env_vector_1 += neigh_vector * w / d
            env_vector_0 += neigh_vector * w
        pairs.append({'center': center_vector,
                      'env0': env_vector_0,
                      'env1': env_vector_1})
        local_xyz.append({"atoms": np.array(atom_xyz),
                          "coords": np.array(coords_xyz)})

    return {'local': pairs,
            "local_xyz": local_xyz,
            'atoms': atoms,
            'cif': struct.to(fmt='cif', filename=None)}
