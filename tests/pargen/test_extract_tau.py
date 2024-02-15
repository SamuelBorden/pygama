import numpy as np
import pytest
from lgdo import Array, ArrayOfEqualSizedArrays, Table, WaveformTable

from pygama.pargen import extract_tau


def test_tp100_align():
    """
    Generate synthetic waveforms with random tp100s, then ensure that this function aligns all tp100s at the same sample
    """
    np.random.seed(42)
    tp100_known = np.random.randint(3000, 3200, 1000)

    tau = 30000
    wf_len = 8192

    test_wfs = []
    for i in range(len(tp100_known)):
        xs = np.arange(0, wf_len - tp100_known[i])
        ys = extract_tau.one_exp(xs, tau, 1)
        test_wfs.append(np.insert(ys, 0, np.zeros(tp100_known[i])))

    superpulse_window_width = 13

    time_aligned_wfs = extract_tau.tp100_align(
        test_wfs, superpulse_window_width, tp100_known
    )
    tp100s = []
    for wf in time_aligned_wfs:
        tp100s.append(np.argmax(wf))
    assert np.array_equal(
        np.array(tp100s), np.full(len(tp100s), np.median(tp100_known) - 13)
    )
    assert len(time_aligned_wfs[0]) == 8192 - 2 * 13


def test_dpz_model_fit():
    tau2 = 30000
    tau1 = 1100
    frac = 0.98
    wf_len = 8192
    tp0 = 3200

    xs = np.arange(0, wf_len - tp0)
    ys = extract_tau.dpz_model(xs, 100, tau1, tau2, frac)
    test_wf = np.insert(ys, 0, np.zeros(tp0))
    tau1_fit, tau2_fit, frac_fit, plot_dict_out = extract_tau.dpz_model_fit(
        test_wf, percent_tau1_fit=0.1, percent_tau2_fit=0.2, idx_shift=2, plot=0
    )

    assert np.allclose(tau1, tau1_fit, rtol=1e-2)
    assert np.allclose(tau2, tau2_fit, rtol=1e-2)
    assert np.allclose(frac, frac_fit, rtol=1e-2)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_get_dpz_decay_constants():
    """
    First, generate a fake HPGe energy spectrum and associated waveforms. Then extract the time constants from the waveforms associated with the 2615 peak
    """
    np.random.seed(42)
    tau2 = 30000
    tau1 = 1100
    frac = 0.98
    wf_len = 8192
    tp0 = 3200
    num_wfs_per_peak = 1000

    # Make the waveforms and then the lgdo table
    peaks = np.array([238.632, 583.191, 727.330, 860.564, 1620.5, 2103.53, 2614.553])
    daq_energies = []
    for peak in peaks:
        daq_energies.extend(np.random.normal(peak, 10, num_wfs_per_peak).astype(int))

    wfs = []
    for amplitude in daq_energies:
        xs = np.arange(0, wf_len - tp0)
        ys = extract_tau.dpz_model(xs, amplitude, tau1, tau2, frac)
        test_wf = np.insert(ys, 0, np.zeros(tp0))
        wfs.append(test_wf)

    wf_tb = WaveformTable(
        dt=np.full(len(wfs), 16),
        dt_units="ns",
        t0=np.full(len(wfs), 0),
        t0_units="ns",
        values=ArrayOfEqualSizedArrays(nda=np.array(wfs)),
        values_units="ADC",
    )
    tb_data = Table(size=len(wfs))
    tb_data.add_column(name="daqenergy", obj=Array(daq_energies))
    tb_data.add_column(name="waveform", obj=wf_tb)

    assert isinstance(tb_data["waveform"]["values"], ArrayOfEqualSizedArrays)

    dpz_opt_dsp_dict = dict(
        {
            "outputs": ["tau1", "tau2", "frac"],
            "processors": {
                "bl_mean , bl_std, bl_slope, bl_intercept": {
                    "function": "linear_slope_fit",
                    "module": "dspeed.processors",
                    "args": [
                        "waveform[0:200]",
                        "bl_mean",
                        "bl_std",
                        "bl_slope",
                        "bl_intercept",
                    ],
                    "unit": ["ADC", "ADC", "ADC", "ADC"],
                },
                "wf_bl": {
                    "function": "bl_subtract",
                    "module": "dspeed.processors",
                    "args": ["waveform", "bl_mean", "wf_bl"],
                    "unit": "ADC",
                },
                "tau1, tau2, frac": {
                    "function": "optimize_2pz",
                    "module": "dspeed.processors",
                    "args": [
                        "waveform",
                        "bl_mean",
                        "round(52*us/waveform.period)",
                        "len(waveform)",
                        "db.dpz.tau1",
                        "db.dpz.tau2",
                        "db.dpz.frac",
                        "tau1",
                        "tau2",
                        "frac",
                    ],
                    "defaults": {
                        "db.dpz.tau1": 900,
                        "db.dpz.tau2": 28000,
                        "db.dpz.frac": 0.9855024553225362,
                    },
                },
            },
        }
    )
    cut_idxs = None
    wf_field = "waveform"
    percent_tau1_fit = 0.1
    percent_tau2_fit = 0.2
    offset_from_wf_max = 2
    superpulse_bl_idx = 25
    superpulse_window_width = 13
    display = 0

    tau_out_dict, _ = extract_tau.get_dpz_decay_constants(
        tb_data,
        cut_idxs,
        wf_field,
        dpz_opt_dsp_dict,
        percent_tau1_fit,
        percent_tau2_fit,
        offset_from_wf_max,
        superpulse_bl_idx,
        superpulse_window_width,
        display,
    )
    assert np.allclose(
        float(tau_out_dict["dpz"]["tau1"].split("*")[0]) / 16, tau1, rtol=1e-2
    )
    assert np.allclose(
        float(tau_out_dict["dpz"]["tau2"].split("*")[0]) / 16, tau2, rtol=1e-2
    )
    assert np.allclose(float(tau_out_dict["dpz"]["frac"]), frac, rtol=1e-2)
