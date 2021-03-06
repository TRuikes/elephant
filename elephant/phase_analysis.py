# -*- coding: utf-8 -*-
"""
Methods for performing phase analysis.

.. autosummary::
    :toctree: toctree/phase_analysis

    spike_triggered_phase
    pairwise_phase_consistency

:copyright: Copyright 2014-2018 by the Elephant team, see `doc/authors.rst`.
:license: Modified BSD, see LICENSE.txt for details.
"""

from __future__ import division, print_function, unicode_literals

import numpy as np
import quantities as pq

__all__ = [
    "spike_triggered_phase",
    "pairwise_phase_consistency"
]


def spike_triggered_phase(hilbert_transform, spiketrains, interpolate):
    """
    Calculate the set of spike-triggered phases of a `neo.AnalogSignal`.

    Parameters
    ----------
    hilbert_transform : neo.AnalogSignal or list of neo.AnalogSignal
        `neo.AnalogSignal` of the complex analytic signal (e.g., returned by
        the `elephant.signal_processing.hilbert` function).
        If `hilbert_transform` is only one signal, all spike trains are
        compared to this signal. Otherwise, length of `hilbert_transform` must
        match the length of `spiketrains`.
    spiketrains : neo.SpikeTrain or list of neo.SpikeTrain
        Spike trains on which to trigger `hilbert_transform` extraction.
    interpolate : bool
        If True, the phases and amplitudes of `hilbert_transform` for spikes
        falling between two samples of signal is interpolated.
        If False, the closest sample of `hilbert_transform` is used.

    Returns
    -------
    phases : list of np.ndarray
        Spike-triggered phases. Entries in the list correspond to the
        `neo.SpikeTrain`s in `spiketrains`. Each entry contains an array with
        the spike-triggered angles (in rad) of the signal.
    amp : list of pq.Quantity
        Corresponding spike-triggered amplitudes.
    times : list of pq.Quantity
        A list of times corresponding to the signal. They correspond to the
        times of the `neo.SpikeTrain` referred by the list item.

    Raises
    ------
    ValueError
        If the number of spike trains and number of phase signals don't match,
        and neither of the two are a single signal.

    Examples
    --------
    Create a 20 Hz oscillatory signal sampled at 1 kHz and a random Poisson
    spike train, then calculate spike-triggered phases and amplitudes of the
    oscillation:

    >>> import neo
    >>> import elephant
    >>> import quantities as pq
    >>> import numpy as np
    ...
    >>> f_osc = 20. * pq.Hz
    >>> f_sampling = 1 * pq.ms
    >>> tlen = 100 * pq.s
    ...
    >>> time_axis = np.arange(
    ...     0, tlen.magnitude,
    ...     f_sampling.rescale(pq.s).magnitude) * pq.s
    >>> analogsignal = neo.AnalogSignal(
    ...     np.sin(2 * np.pi * (f_osc * time_axis).simplified.magnitude),
    ...     units=pq.mV, t_start=0*pq.ms, sampling_period=f_sampling)
    >>> spiketrain = (elephant.spike_train_generation.
    ...     homogeneous_poisson_process(
    ...     50 * pq.Hz, t_start=0.0*pq.ms, t_stop=tlen.rescale(pq.ms)))
    ...
    >>> phases, amps, times = elephant.phase_analysis.spike_triggered_phase(
    ...     elephant.signal_processing.hilbert(analogsignal),
    ...     spiketrain,
    ...     interpolate=True)

    """

    # Convert inputs to lists
    if not isinstance(spiketrains, list):
        spiketrains = [spiketrains]

    if not isinstance(hilbert_transform, list):
        hilbert_transform = [hilbert_transform]

    # Number of signals
    num_spiketrains = len(spiketrains)
    num_phase = len(hilbert_transform)

    if num_spiketrains != 1 and num_phase != 1 and \
            num_spiketrains != num_phase:
        raise ValueError(
            "Number of spike trains and number of phase signals"
            "must match, or either of the two must be a single signal.")

    # For each trial, select the first input
    start = [elem.t_start for elem in hilbert_transform]
    stop = [elem.t_stop for elem in hilbert_transform]

    result_phases = []
    result_amps = []
    result_times = []

    # Step through each signal
    for spiketrain_i, spiketrain in enumerate(spiketrains):
        # Check which hilbert_transform AnalogSignal to look at - if there is
        # only one then all spike trains relate to this one, otherwise the two
        # lists of spike trains and phases are matched up
        if num_phase > 1:
            phase_i = spiketrain_i
        else:
            phase_i = 0

        # Take only spikes which lie directly within the signal segment -
        # ignore spikes sitting on the last sample
        sttimeind = np.where(np.logical_and(
            spiketrain >= start[phase_i], spiketrain < stop[phase_i]))[0]

        # Extract times for speed reasons
        times = hilbert_transform[phase_i].times

        # Find index into signal for each spike
        ind_at_spike = (
                (spiketrain[sttimeind] - hilbert_transform[phase_i].t_start) /
                hilbert_transform[phase_i].sampling_period). \
            simplified.magnitude.astype(int)

        # Append new list to the results for this spiketrain
        result_phases.append([])
        result_amps.append([])
        result_times.append([])

        # Step through all spikes
        for spike_i, ind_at_spike_j in enumerate(ind_at_spike):

            if interpolate and ind_at_spike_j + 1 < len(times):
                # Get relative spike occurrence between the two closest signal
                # sample points
                # if z->0 spike is more to the left sample
                # if z->1 more to the right sample
                z = (spiketrain[sttimeind[spike_i]] - times[ind_at_spike_j]) / \
                    hilbert_transform[phase_i].sampling_period

                # Save hilbert_transform (interpolate on circle)
                p1 = np.angle(hilbert_transform[phase_i][ind_at_spike_j])
                p2 = np.angle(hilbert_transform[phase_i][ind_at_spike_j + 1])
                interpolation = (1 - z) * np.exp(np.complex(0, p1)) \
                                + z * np.exp(np.complex(0, p2))
                p12 = np.angle([interpolation])
                result_phases[spiketrain_i].append(p12)

                # Save amplitude
                result_amps[spiketrain_i].append(
                    (1 - z) * np.abs(
                        hilbert_transform[phase_i][ind_at_spike_j]) +
                    z * np.abs(hilbert_transform[phase_i][ind_at_spike_j + 1]))
            else:
                p1 = np.angle(hilbert_transform[phase_i][ind_at_spike_j])
                result_phases[spiketrain_i].append(p1)

                # Save amplitude
                result_amps[spiketrain_i].append(
                    np.abs(hilbert_transform[phase_i][ind_at_spike_j]))

            # Save time
            result_times[spiketrain_i].append(spiketrain[sttimeind[spike_i]])

    # Convert outputs to arrays
    for i, entry in enumerate(result_phases):
        result_phases[i] = np.array(entry).flatten()
    for i, entry in enumerate(result_amps):
        result_amps[i] = pq.Quantity(entry, units=entry[0].units).flatten()
    for i, entry in enumerate(result_times):
        result_times[i] = pq.Quantity(entry, units=entry[0].units).flatten()
    return result_phases, result_amps, result_times


def pairwise_phase_consistency(phases, method='ppc0'):
    r"""
    The Pairwise Phase Consistency (PPC0) :cite:`phase-Vinck2010_51` is an
    improved measure of phase consistency/phase locking value, accounting for
    bias due to low trial counts.

    PPC0 is computed according to Eq. 14 and 15 of the cited paper.

    An improved version of the PPC (PPC1) :cite: `PMID:22187161` computes angular
    difference ony between pairs of spikes within trials.

    PPC1 is not implemented yet


    .. math::
        \text{PPC} = \frac{2}{N(N-1)} \sum_{j=1}^{N-1} \sum_{k=j+1}^N
        f(\theta_j, \theta_k)

    wherein the function :math:`f` computes the dot product between two unit
    vectors and is defined by

    .. math::
        f(\phi, \omega) = \cos(\phi) \cos(\omega) + \sin(\phi) \sin(\omega)

    Parameters
    ----------
    phases : np.ndarray or list of np.ndarray
        Spike-triggered phases (output from :func:`spike_triggered_phase`).
        If phases is a list of arrays, each array is considered a trial

    method : str
        'ppc0' - compute PPC between all pairs of spikes

    Returns
    -------
    result_ppc : list of float
        Pairwise Phase Consistency

    """
    # Convert inputs to lists
    if not isinstance(phases, list):
        phases = [phases]

    # Check if all elements are arrays
    if not isinstance(phases, (list, tuple)):
        raise TypeError("Input must be a list of 1D numpy arrays with phases")
    for phase_array in phases:
        if not isinstance(phase_array, np.ndarray):
            raise TypeError("Each entry of the input list must be an 1D "
                            "numpy array with phases")
        if phase_array.ndim != 1:
            raise ValueError("Phase arrays must be 1D (use .flatten())")

    if method not in ['ppc0']:
        raise ValueError('For method choose out of: ["ppc0"]')

    phase_array = np.hstack(phases)
    n_trials = phase_array.shape[0]  # 'spikes' are 'trials' as in paper

    # Compute the distance between each pair of phases using dot product
    # Optimize computation time using array multiplications instead of for
    # loops
    p_cos_2d = np.broadcast_to(np.cos(phase_array), (n_trials, n_trials))
    p_sin_2d = np.broadcast_to(np.sin(phase_array), (n_trials, n_trials))

    # By doing the element-wise multiplication of this matrix with its
    # transpose, we get the distance between phases for all possible pairs
    # of elements in 'phase'
    dot_prod = np.multiply(p_cos_2d, p_cos_2d.T, dtype=np.float32) + \
               np.multiply(p_sin_2d, p_sin_2d.T, dtype=np.float32)  # TODO: agree on using this precision  or not

    # Now average over all elements in temp_results (the diagonal are 1
    # and should not be included)
    np.fill_diagonal(dot_prod, 0)

    if method == 'ppc0':
        # Note: each pair i,j is computed twice in dot_prod. do not
        # multiply by 2. n_trial * n_trials - n_trials = nr of filled elements
        # in dot_prod
        ppc = np.sum(dot_prod) / (n_trials * n_trials - n_trials)  # TODO: handle nan's
        return ppc

    elif method == 'ppc1':
        # TODO: remove all indices from the same trial
        return
