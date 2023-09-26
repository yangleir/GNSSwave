"""Calculate the Significant Wave Height (SWH) from Sea Surface Height (SSH).
"""
import numpy as np
from scipy import signal


def ssh2sse(ssh: list, order: int, smooth: int, sample: int, coef: float = 1.0
            ) -> list:
    """Calculate Sea Surface Elevations (SSE) from SSH.

    Input arguments:
        ssh: the sea surface height;
        order: order of the butterworth filter;
        smooth: the smoothing period;
        sample: the sample period;
        coef: the scale coefficient for ssh.

    Return:
        the sea surface elevations.
    """
    # Remove the linear trend from input ssh
    ssh_nl = signal.detrend(ssh * coef)
    # Apply Butterworth high pass filter to ssh
    b, a = signal.butter(order, (2/smooth)*sample, 'high')
    sse = signal.filtfilt(b, a, ssh_nl, padlen=3*(max(len(a), len(b))-1))

    return sse


def sse2swh(sse: list, step: int) -> list:
    """Calculate the Significant Wave Height (SWH) from Sea Surface
    Elevations (SSE).

    Input arguments:
        sse: the sea surface elevations;
        step: step when calculate swh.

    Return:
        the significant wave height.
    """
    swhs, nsse = [], len(sse)
    if nsse < step:
        raise ValueError('Length of the sse should be bigger than step.')
    for ms in range(step, nsse, step):
        swhs.append(np.std(sse[ms-step:ms], ddof=1))

    return np.array(swhs) * 4


def ssh2wp(data: list, fs: float) -> float:
    """Calculate wave period using zeroth and first moments from PSD.

    Input arguments:
        data: the sea surface heights;
        fs: the sampling frequency (Hz).

    Return:
        the wave period.
    """
    # Compute the PSD
    freqs, Pxx = signal.welch(data, fs, window='hann', nperseg=len(data)//6,
                              noverlap=len(data)//8)
    # Compute the zeroth and first moments of the wave spectrum
    m0 = np.sum(Pxx)
    m1 = np.sum(freqs * Pxx)

    return m0 / m1


def sse2wl(sse: list, step: int = 256) -> float:
    """Calculate wavelength from Sea Surface Elevation (SSE).

    Input arguments:
        sse: the sea surface elevations;
        step: step when calculate swh.

    Return:
        the wavelength.
    """
    freq, ps = signal.welch(sse, 1, nperseg=step)
    index = np.argmax(ps)
    return 1 / freq[index]


def iqr_detect(seq: list, step: int, zmax=3, fill='zero') -> list:
    """IQR outlier data detection function.

    Input arguments:
        - `seq`: the input sequence data;
        - `step`: step for detection;
        - `zmax`: the threshold of z;
        - `fill`: method of outlier filling, one of (zero, median, delete).

    Example:
        >>> seq = [1, 2, 3, 1, 2, 9, 1, 2, 3]
        >>> cleaned = iqr_detect(seq, 5)
        >>> list(cleaned)
        [1, 2, 3, 1, 2, 0, 1, 2, 3]
    """
    if len(seq) < step:
        raise ValueError('The seq is too short: less than step.')
    if fill not in ('zero', 'median', 'delete'):
        raise ValueError('fill should be one of (zero, median, delete).')

    clean, hstep = [], step // 2
    for ix, ele in np.ndenumerate(seq):
        li = 0 if ix[0] - hstep < 0 else ix[0] - hstep
        ui = len(seq) if ix[0] + hstep > len(seq) else ix[0] + hstep
        median = np.median(seq[li:ui])
        iqr = np.subtract(*np.percentile(seq[li:ui], [75, 25]))
        if np.abs((ele - median) / (0.7413 * iqr)) < zmax:
            clean.append(ele)
        elif fill == 'median':
            clean.append(median)
        elif fill == 'zero':
            clean.append(0)

    return np.array(clean)
