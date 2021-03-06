# -*- coding: utf-8 -*-
"""
Unit tests for the phase analysis module.

:copyright: Copyright 2016 by the Elephant team, see `doc/authors.rst`.
:license: Modified BSD, see LICENSE.txt for details.
"""
from __future__ import division, print_function

import unittest

from neo import SpikeTrain, AnalogSignal
import numpy as np
import quantities as pq

import elephant.phase_analysis

from numpy.ma.testutils import assert_allclose


class SpikeTriggeredPhaseTestCase(unittest.TestCase):

    def setUp(self):
        tlen0 = 100 * pq.s
        f0 = 20. * pq.Hz
        fs0 = 1 * pq.ms
        t0 = np.arange(
            0, tlen0.rescale(pq.s).magnitude,
            fs0.rescale(pq.s).magnitude) * pq.s
        self.anasig0 = AnalogSignal(
            np.sin(2 * np.pi * (f0 * t0).simplified.magnitude),
            units=pq.mV, t_start=0 * pq.ms, sampling_period=fs0)
        self.st0 = SpikeTrain(
            np.arange(50, tlen0.rescale(pq.ms).magnitude - 50, 50) * pq.ms,
            t_start=0 * pq.ms, t_stop=tlen0)
        self.st1 = SpikeTrain(
            [100., 100.1, 100.2, 100.3, 100.9, 101.] * pq.ms,
            t_start=0 * pq.ms, t_stop=tlen0)

    def test_perfect_locking_one_spiketrain_one_signal(self):
        phases, amps, times = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            self.st0,
            interpolate=True)

        assert_allclose(phases[0], - np.pi / 2.)
        assert_allclose(amps[0], 1, atol=0.1)
        assert_allclose(times[0].magnitude, self.st0.magnitude)
        self.assertEqual(len(phases[0]), len(self.st0))
        self.assertEqual(len(amps[0]), len(self.st0))
        self.assertEqual(len(times[0]), len(self.st0))

    def test_perfect_locking_many_spiketrains_many_signals(self):
        phases, amps, times = elephant.phase_analysis.spike_triggered_phase(
            [
                elephant.signal_processing.hilbert(self.anasig0),
                elephant.signal_processing.hilbert(self.anasig0)],
            [self.st0, self.st0],
            interpolate=True)

        assert_allclose(phases[0], -np.pi / 2.)
        assert_allclose(amps[0], 1, atol=0.1)
        assert_allclose(times[0].magnitude, self.st0.magnitude)
        self.assertEqual(len(phases[0]), len(self.st0))
        self.assertEqual(len(amps[0]), len(self.st0))
        self.assertEqual(len(times[0]), len(self.st0))

    def test_perfect_locking_one_spiketrains_many_signals(self):
        phases, amps, times = elephant.phase_analysis.spike_triggered_phase(
            [
                elephant.signal_processing.hilbert(self.anasig0),
                elephant.signal_processing.hilbert(self.anasig0)],
            [self.st0],
            interpolate=True)

        assert_allclose(phases[0], -np.pi / 2.)
        assert_allclose(amps[0], 1, atol=0.1)
        assert_allclose(times[0].magnitude, self.st0.magnitude)
        self.assertEqual(len(phases[0]), len(self.st0))
        self.assertEqual(len(amps[0]), len(self.st0))
        self.assertEqual(len(times[0]), len(self.st0))

    def test_perfect_locking_many_spiketrains_one_signal(self):
        phases, amps, times = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            [self.st0, self.st0],
            interpolate=True)

        assert_allclose(phases[0], -np.pi / 2.)
        assert_allclose(amps[0], 1, atol=0.1)
        assert_allclose(times[0].magnitude, self.st0.magnitude)
        self.assertEqual(len(phases[0]), len(self.st0))
        self.assertEqual(len(amps[0]), len(self.st0))
        self.assertEqual(len(times[0]), len(self.st0))

    def test_interpolate(self):
        phases_int, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            self.st1,
            interpolate=True)

        self.assertLess(phases_int[0][0], phases_int[0][1])
        self.assertLess(phases_int[0][1], phases_int[0][2])
        self.assertLess(phases_int[0][2], phases_int[0][3])
        self.assertLess(phases_int[0][3], phases_int[0][4])
        self.assertLess(phases_int[0][4], phases_int[0][5])

        phases_noint, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            self.st1,
            interpolate=False)

        self.assertEqual(phases_noint[0][0], phases_noint[0][1])
        self.assertEqual(phases_noint[0][1], phases_noint[0][2])
        self.assertEqual(phases_noint[0][2], phases_noint[0][3])
        self.assertEqual(phases_noint[0][3], phases_noint[0][4])
        self.assertNotEqual(phases_noint[0][4], phases_noint[0][5])

        # Verify that when using interpolation and the spike sits on the sample
        # of the Hilbert transform, this is the same result as when not using
        # interpolation with a spike slightly to the right
        self.assertEqual(phases_noint[0][2], phases_int[0][0])
        self.assertEqual(phases_noint[0][4], phases_int[0][0])

    def test_inconsistent_numbers_spiketrains_hilbert(self):
        self.assertRaises(
            ValueError, elephant.phase_analysis.spike_triggered_phase,
            [
                elephant.signal_processing.hilbert(self.anasig0),
                elephant.signal_processing.hilbert(self.anasig0)],
            [self.st0, self.st0, self.st0], False)

        self.assertRaises(
            ValueError, elephant.phase_analysis.spike_triggered_phase,
            [
                elephant.signal_processing.hilbert(self.anasig0),
                elephant.signal_processing.hilbert(self.anasig0)],
            [self.st0, self.st0, self.st0], False)

    def test_spike_earlier_than_hilbert(self):
        # This is a spike clearly outside the bounds
        st = SpikeTrain(
            [-50, 50],
            units='s', t_start=-100 * pq.s, t_stop=100 * pq.s)
        phases_noint, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            st,
            interpolate=False)
        self.assertEqual(len(phases_noint[0]), 1)

        # This is a spike right on the border (start of the signal is at 0s,
        # spike sits at t=0s). By definition of intervals in
        # Elephant (left borders inclusive, right borders exclusive), this
        # spike is to be considered.
        st = SpikeTrain(
            [0, 50],
            units='s', t_start=-100 * pq.s, t_stop=100 * pq.s)
        phases_noint, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            st,
            interpolate=False)
        self.assertEqual(len(phases_noint[0]), 2)

    def test_spike_later_than_hilbert(self):
        # This is a spike clearly outside the bounds
        st = SpikeTrain(
            [1, 250],
            units='s', t_start=-1 * pq.s, t_stop=300 * pq.s)
        phases_noint, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            st,
            interpolate=False)
        self.assertEqual(len(phases_noint[0]), 1)

        # This is a spike right on the border (length of the signal is 100s,
        # spike sits at t=100s). However, by definition of intervals in
        # Elephant (left borders inclusive, right borders exclusive), this
        # spike is not to be considered.
        st = SpikeTrain(
            [1, 100],
            units='s', t_start=-1 * pq.s, t_stop=200 * pq.s)
        phases_noint, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            st,
            interpolate=False)
        self.assertEqual(len(phases_noint[0]), 1)

    # This test handles the correct dealing with input signals that have
    # different time units, including a CompoundUnit
    def test_regression_269(self):
        # This is a spike train on a 30KHz sampling, one spike at 1s, one just
        # before the end of the signal
        cu = pq.CompoundUnit("1/30000.*s")
        st = SpikeTrain(
            [30000., (self.anasig0.t_stop - 1 * pq.s).rescale(cu).magnitude],
            units=pq.CompoundUnit("1/30000.*s"),
            t_start=-1 * pq.s, t_stop=300 * pq.s)
        phases_noint, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            st,
            interpolate=False)
        self.assertEqual(len(phases_noint[0]), 2)


class PairwisePhaseConsistencyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):  # Note: using setUp makes the class call this
        # function per test, while this way the function is called only
        # 1 time per TestCase, slightly more efficient (0.5s tough)

        # Same setup as SpikeTriggerePhaseTestCase
        tlen0 = 100 * pq.s
        f0 = 20. * pq.Hz
        fs0 = 1 * pq.ms
        t0 = np.arange(
            0, tlen0.rescale(pq.s).magnitude,
            fs0.rescale(pq.s).magnitude) * pq.s
        cls.anasig0 = AnalogSignal(
            np.sin(2 * np.pi * (f0 * t0).simplified.magnitude),
            units=pq.mV, t_start=0 * pq.ms, sampling_period=fs0)

        # Spiketrain with perfect locking
        cls.st_perfect = SpikeTrain(
            np.arange(50, tlen0.rescale(pq.ms).magnitude - 50, 50) * pq.ms,
            t_start=0 * pq.ms, t_stop=tlen0)

        # Spiketrain with inperfect locking
        cls.st_inperfect = SpikeTrain(
            [100., 100.1, 100.2, 100.3, 100.9, 101.] * pq.ms,
            t_start=0 * pq.ms, t_stop=tlen0)

        # Generate 2 'bursting' spiketrains, both locking on sinus period,
        # but with different strengths
        n_spikes = 3  # n spikes per burst
        burst_interval = (1 / f0.magnitude) * pq.s
        burst_start_times = np.arange(
            0,
            tlen0.rescale('ms').magnitude,
            burst_interval.rescale('ms').magnitude
        )

        # Spiketrain with strong locking
        burst_freq_strong = 200. * pq.Hz  # strongly locking unit
        burst_spike_interval = (1 / burst_freq_strong.magnitude) * pq.s
        st_in_burst = np.arange(
            0,
            burst_spike_interval.rescale('ms').magnitude * n_spikes,
            burst_spike_interval.rescale('ms').magnitude
        )
        st = [st_in_burst + t_offset for t_offset in burst_start_times]
        st = np.hstack(st) * pq.ms
        cls.st_bursting_strong = SpikeTrain(st,
                                            t_start=0 * pq.ms,
                                            t_stop=tlen0
                                            )

        # Spiketrain with weak locking
        burst_freq_weak = 100. * pq.Hz  # weak locking unit
        burst_spike_interval = (1 / burst_freq_weak.magnitude) * pq.s
        st_in_burst = np.arange(
            0,
            burst_spike_interval.rescale('ms').magnitude * n_spikes,
            burst_spike_interval.rescale('ms').magnitude
        )
        st = [st_in_burst + t_offset for t_offset in burst_start_times]
        st = np.hstack(st) * pq.ms
        cls.st_bursting_weak = SpikeTrain(st,
                                          t_start=0 * pq.ms,
                                          t_stop=tlen0
                                          )

    def test_perfect_locking(self):
        phases, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            self.st_perfect,
            interpolate=True
        )
        # Pass input as single array
        ppc0 = elephant.phase_analysis.pairwise_phase_consistency(
            phases[0], method='ppc0'
        )
        self.assertEqual(ppc0, 1)
        self.assertIsInstance(ppc0, float)

        # Pass input as list of arrays
        n_phases = int(phases[0].shape[0] / 2)
        phases_cut = [phases[0][i * 2:i * 2 + 2] for i in range(n_phases)]
        ppc0 = elephant.phase_analysis.pairwise_phase_consistency(
            phases_cut, method='ppc0'
        )
        self.assertEqual(ppc0, 1)
        self.assertIsInstance(ppc0, float)

    def test_inperfect_locking(self):
        phases, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            self.st_inperfect,
            interpolate=True
        )
        # Pass input as single array
        ppc0 = elephant.phase_analysis.pairwise_phase_consistency(
            phases[0], method='ppc0'
        )
        self.assertLess(ppc0, 1)
        self.assertIsInstance(ppc0, float)

    def test_strong_vs_weak_locking(self):
        phases_weak, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            self.st_bursting_weak,
            interpolate=True
        )
        # Pass input as single array
        ppc0_weak = elephant.phase_analysis.pairwise_phase_consistency(
            phases_weak[0], method='ppc0'
        )
        phases_strong, _, _ = elephant.phase_analysis.spike_triggered_phase(
            elephant.signal_processing.hilbert(self.anasig0),
            self.st_bursting_strong,
            interpolate=True
        )
        # Pass input as single array
        ppc0_strong = elephant.phase_analysis.pairwise_phase_consistency(
            phases_strong[0], method='ppc0'
        )

        self.assertLess(ppc0_weak, ppc0_strong)


if __name__ == '__main__':
    unittest.main()
