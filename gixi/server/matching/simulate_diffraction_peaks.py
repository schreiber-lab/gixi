from typing import Union
from pathlib import Path

from xrayutilities.materials import Crystal
from xrayutilities.utilities import lam2en

import numpy as np

import numpy
from numpy import abs as nabs

from numpy import cos as ncos
from numpy import sin as nsin


def get_diffraction_peaks(
        mat: Union[Crystal, str, Path],
        q_max: float = 4.,
        wavelength: float = 0.6888,
        normalize: bool = True,
):
    if not isinstance(mat, Crystal):
        mat = Crystal.fromCIF(mat)

    k0 = 2 * np.pi / wavelength
    energy = lam2en(wavelength)

    tmp_data = _reflection_strength(mat, q_max, energy)
    hkl, qpos, rs = _merge_lines(tmp_data)
    ang = _q2ang(qpos, k0)
    rs *= _get_correction_factor(ang)

    indices = rs / rs.max() > 1e-8

    miller_indices = np.array(hkl)[indices]
    intensities = rs[indices]
    q_pos = qpos[indices]

    if normalize and intensities.max() > 0:
        intensities = intensities / intensities.max()

    return q_pos, intensities, miller_indices


def _reflection_strength(mat: Crystal, qmax: float, energy: float):
    """
    determine structure factors/reflection strength of all Bragg peaks up
    to tt_cutoff. This function also implements the March-Dollase model for
    preferred orientation in the symmetric reflection mode. Note that
    although this means the sample has anisotropic properties the various
    lines can still be merged together since at the moment no anisotropic
    crystal shape is supported.
    """

    # get allowed Bragg peaks

    hkl = tuple(mat.lattice.get_allowed_hkl(qmax))
    q = mat.Q(hkl)
    qnorm = numpy.linalg.norm(q, axis=1)

    data = numpy.zeros(len(hkl), dtype=[('q', numpy.double),
                                        ('r', numpy.double),
                                        ('hkl', numpy.ndarray)])
    data['q'] = qnorm
    data['r'] = nabs(mat.StructureFactorForQ(q, energy)) ** 2
    data['hkl'] = hkl

    return data


def _merge_lines(data):
    """
    if calculation is isotropic lines at the same q-position can be merged
    to one line to reduce the calculational effort

    Parameters
    ----------
    data :  ndarray
        numpy field array with values of 'hkl' (Miller indices of the
        peaks), 'q' (q-position), and 'r' (reflection strength) as produced
        by the `reflection_strength` method

    Returns
    -------
    hkl, q, ang, r : array-like
        Miller indices, q-position, diffraction angle (Theta), and
        reflection strength of the material
    """
    data.sort(order=['q', 'hkl'])
    qpos = []
    refstrength = []
    hkl = []

    def add_lines(q, ref, chkl):
        for R, m in zip(ref, chkl):
            qpos.append(q)
            refstrength.append(R)
            hkl.append(m)

    currq = -1
    curref = []
    currhkl = []

    for r in data:
        if not numpy.isclose(r[0] - currq, 0):
            add_lines(currq, curref, currhkl)
            currq = r[0]
            curref = [r[1], ]
            currhkl = [r[2], ]
        else:
            curref[-1] += r[1]
            currhkl[-1] = r[2]
    # add remaining lines
    add_lines(currq, curref, currhkl)

    qpos = numpy.array(qpos, dtype=numpy.double)
    refstrength = numpy.array(refstrength, dtype=numpy.double)
    return hkl, qpos, refstrength


def _get_correction_factor(ang):
    """
    calculate the correction factor for the diffracted intensities. This
    contains the polarization effects and the Lorentz factor

    Parameters
    ----------
    ang :   aray-like
        theta diffraction angles for which the correction should be
        calculated

    Returns
    -------
    f :     array-like
        array of the same shape as ang containing the correction factors
    """
    # correct data for polarization and lorentzfactor and unit cell volume
    # see L.S. Zevin : Quantitative X-Ray Diffractometry
    # page 18ff
    polarization_factor = (1 +
                           ncos(numpy.radians(2 * ang)) ** 2) / 2
    lorentz_factor = 1. / (nsin(numpy.radians(ang)) ** 2 *
                           ncos(numpy.radians(ang)))
    return polarization_factor * lorentz_factor


def _q2ang(q_pos, k0: float, deg=True):
    """
    Converts reciprocal space values to theta angles
    """

    th = numpy.arcsin(numpy.divide(q_pos, (2 * k0)))

    if deg:
        th = numpy.degrees(th)

    return th
