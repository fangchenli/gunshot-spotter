import numpy as np

SOUND_SPEED = 343.2

MIC_DISTANCE_6 = 0.09218
MAX_TDOA_6 = MIC_DISTANCE_6 / SOUND_SPEED

RESPEAKER_RATE = 16000

MIC_GROUP_N = 3
MIC_GROUP = [[0, 3], [1, 4], [2, 5]]


def gcc_phat(sig, refsig, fs=1, max_tau=None, interp=1):
    """
    This function computes the offset between the signal sig and the reference signal refsig
    using the Generalized Cross Correlation - Phase Transform (GCC-PHAT)method.
    """

    # make sure the length for the FFT is larger or equal than len(sig) + len(refsig)
    n = sig.shape[0] + refsig.shape[0]

    # Generalized Cross Correlation Phase Transform
    SIG = np.fft.rfft(sig, n=n)
    REFSIG = np.fft.rfft(refsig, n=n)
    R = SIG * np.conj(REFSIG)

    cc = np.fft.irfft(R / np.abs(R), n=(interp * n))

    max_shift = int(interp * n / 2)
    if max_tau:
        max_shift = np.minimum(int(interp * fs * max_tau), max_shift)

    cc = np.concatenate((cc[-max_shift:], cc[:max_shift + 1]))

    # find max cross correlation index
    shift = np.argmax(np.abs(cc)) - max_shift

    tau = shift / float(interp * fs)

    return tau, cc


def get_direction(buf):

    max_indexes = np.argmax(buf, axis=1)
    max_index = np.amax(max_indexes)
    min_index = np.amin(max_indexes)
    dif = max_index - min_index

    buf = buf[:, np.amax([0, min_index-dif]):np.amin([buf.shape[1], max_index+dif])]

    print(f'max index: {max_index}')
    print(f'peek diff: {dif}')
    tau = np.zeros((MIC_GROUP_N,))
    theta = np.zeros((MIC_GROUP_N,))

    for i, v in enumerate(MIC_GROUP):
        tau[i], _ = gcc_phat(buf[v[0], :], buf[v[1], :], fs=RESPEAKER_RATE, max_tau=MAX_TDOA_6, interp=1)
        theta[i] = np.arcsin(tau[i] / MAX_TDOA_6) * 180 / np.pi

    min_index = np.argmin(np.abs(tau))
    if (min_index != 0 and theta[min_index - 1] >= 0) or (min_index == 0 and theta[MIC_GROUP_N - 1] < 0):
        best_guess = (theta[min_index] + 360) % 360
    else:
        best_guess = (180 - theta[min_index])

    best_guess = (best_guess + 30 + min_index * 60) % 360

    return best_guess
