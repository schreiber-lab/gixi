from scipy.optimize import linear_sum_assignment
import numpy as np

from gixi.server.matching.simulate_diffraction_peaks import get_diffraction_peaks
from gixi.server.app_config import AppConfig


class MatchDiffractionPatterns(object):
    def __init__(self, config: AppConfig):
        self.config = config
        self.max_distance = self.config.match_config.max_distance
        self.q_max = self.config.q_space.q_max
        self.folder = self.config.match_config.cif_folder

        if self.config.match_config.perform_matching:
            self.sim_results = self._simulate_peaks()
        else:
            self.sim_results = None

    def __call__(self, data_dict: dict):
        if not self.sim_results:
            return data_dict

        boxes = data_dict['boxes']
        qs = (boxes[:, 0] + boxes[:, 2]) / 2 * self.q_max

        matching_results = {}

        for name, path, q_pos, intensities, miller_indices in self.sim_results:
            matched_sf, sim_idx, exp_idx = get_match_metrics(q_pos, qs, intensities, self.max_distance)

            matching_results[name] = dict(
                path=str(path),
                metric=np.array(matched_sf),
                sim_idx=sim_idx,
                exp_idx=exp_idx,
            )

        data_dict['matching_results'] = matching_results

        return data_dict

    def _simulate_peaks(self):
        sim_results = []
        for path in self.folder.glob('*.cif'):
            name = path.stem
            q_pos, intensities, miller_indices = get_diffraction_peaks(
                path,
                q_max=self.q_max,
                wavelength=self.config.q_space.wavelength,
            )
            sim_results.append((name, path, q_pos, intensities, miller_indices))

        return sim_results


def get_match_metrics(
        sim_qs: np.ndarray,
        exp_qs: np.ndarray,
        sim_intensities: np.ndarray,
        max_distance: float = 0.1,
):
    distance_mtx = np.abs(exp_qs[None] - sim_qs[..., None])
    sim_idx, exp_idx = linear_sum_assignment(distance_mtx)
    distances = distance_mtx[sim_idx, exp_idx]
    indices = distances < max_distance
    sim_idx, exp_idx = sim_idx[indices], exp_idx[indices]
    matched_sf = sim_intensities[sim_idx].sum() / sim_intensities.sum()
    return matched_sf, sim_idx, exp_idx
