# -*- coding: utf-8 -*-
# import logging
# from itertools import product
# from typing import Tuple, Union
# from pathlib import Path
#
# import cmath
# import numpy as np
#
# from crystals import Crystal
# from periodictable import cromermann as cr_ff
#
# MillerIndices = Tuple[int, int, int]
#
# logger = logging.getLogger(__name__)
#
#
# # TODO: implement vectorized solution!
#
#
# def get_sorted_q(crystal: Crystal or Path, q_max: float, decimals: int = 3, **kwargs):
#     ring_dict = get_crystal_rings(crystal, q_max, **kwargs)
#     qs = [v['q'] for v in ring_dict.values() if v]
#     return sorted(list(set([round(q, decimals) for q in qs if q < q_max])))
#
#
# def get_powder_profile(q: np.ndarray, crystal: Crystal or Path, width: float = None, **kwargs):
#     width = width or q.max() / 200
#     ws = (width ** 2) * 2
#     ring_dict = get_crystal_rings(crystal, q.max(), **kwargs)
#     profile = np.zeros_like(q)
#     for ring in ring_dict.values():
#         if ring:
#             profile += ring['intensity'] * np.exp(- (q - ring['q']) ** 2 / ws)
#     return profile / profile.max()
#
#
# def get_crystal_rings(crystal: Crystal or Path,
#                       q_max: float,
#                       min_sf: float = 0.01,
#                       max_num: int = 10,
#                       ) -> dict:
#     if not isinstance(crystal, Crystal):
#         crystal = Crystal.from_cif(crystal)
#
#     miller_indices: MillerIndices
#     ring_dict = {}
#
#     max_num = min(
#         _check_parallel_indices(ring_dict, crystal, 0, q_max, max_num, min_sf),
#         _check_parallel_indices(ring_dict, crystal, 1, q_max, max_num, min_sf),
#         _check_parallel_indices(ring_dict, crystal, 2, q_max, max_num, min_sf),
#     )
#
#     for i, miller_indices in enumerate(product(list(range(max_num)), repeat=3)):
#         if miller_indices not in ring_dict:
#             ring_dict[miller_indices] = _get_ring(crystal, miller_indices, min_sf)
#
#     return ring_dict
#
#
# def _check_parallel_indices(ring_dict: dict, crystal: Crystal, idx: int, q_max,
#                             max_num: int = 10, min_sf: float = 0.01) -> int:
#     miller_indices = [0, 0, 0]
#
#     for h in range(max_num):
#         miller_indices[idx] = h
#         ring = _get_ring(crystal, tuple(miller_indices), min_sf)
#
#         if ring and ring['q'] > q_max:
#             return h
#
#         ring_dict[tuple(miller_indices)] = ring
#     return max_num
#
#
# def _get_ring(crystal: Crystal, miller_indices: MillerIndices, min_sf: float) -> Union[dict, None]:
#     scattering_vector = crystal.scattering_vector(miller_indices)
#     q = np.linalg.norm(scattering_vector)
#     sf = _calc_structure_factor(q, miller_indices, crystal) * _structure_factor_coef(miller_indices)
#     if sf >= min_sf:
#         return dict(q=q, miller_indices=miller_indices, intensity=sf)
#
#
# def _structure_factor_coef(miller_indices: MillerIndices) -> int:
#     return 2 ** sum(map(bool, miller_indices))
#
#
# def _calc_structure_factor(q: float, miller_indices: MillerIndices, crystal: Crystal) -> float:
#     return abs(sum(
#         cr_ff.fxrayatq(atom.element, q, charge=None) * cmath.exp(
#             2 * np.pi * 1j * np.dot(miller_indices, atom.coords_fractional)
#         )
#         for atom in crystal
#     ))
#
#
