"""
Exponentially modified Gaussian distributions for pygama
"""

import sys
from typing import Union

import numba as nb
import numpy as np
from math import erfc
from pygama.math.functions.pygama_continuous import pygama_continuous 

from pygama.math.functions.error_function import nb_erf, nb_erfc
from pygama.math.functions.gauss import nb_gauss_cdf, nb_gauss_pdf

limit = np.log(sys.float_info.max)/10
kwd = {"parallel": False, "fastmath": True}
kwd_2 = {"parallel": True, "fastmath": True}


@nb.njit(**kwd)
def nb_gauss_tail_exact(x: float, mu: float, sigma: float, tau: float, tmp: float) -> float:
    r"""
    Exact form of a normalized exponentially modified Gaussian PDF. 
    It computes the following PDF:


    .. math::
        pdf(x, \tau,\mu,\sigma) = \frac{1}{2|\tau|}e^{\frac{x-\mu}{\tau}+\frac{\sigma^2}{2\tau^2}}\text{erfc}\left(\frac{\tau(\frac{x-\mu}{\sigma})+\sigma}{|\tau|\sqrt{2}}\right)


    Where :math:`tmp = \frac{x-\mu}{\tau}+\frac{\sigma^2}{2\tau^2}` is precomputed in :func:`nb_exgauss_pdf` to save computational time.


    As a Numba JIT function, it runs slightly faster than
    'out of the box' functions.


    Parameters
    ----------
    x
        Input data
    mu
        The centroid of the Gaussian
    sigma
        The standard deviation of the Gaussian
    tau
        The characteristic scale of the Gaussian tail
    tmp
        The scaled version of the exponential argument


    See Also 
    --------
    :func:`nb_exgauss_pdf`
    """

    abstau = np.absolute(tau)
    if tmp < limit: tmp = tmp
    else: tmp = limit
    z = (x-mu)/sigma
    tail_f = (1/(2*abstau)) * np.exp(tmp) * erfc( (tau*z + sigma)/(np.sqrt(2)*abstau))
    return tail_f


@nb.njit(**kwd)
def nb_gauss_tail_approx(x: np.ndarray, mu: float, sigma: float, tau: float) -> np.ndarray:
    r"""
    Approximate form of a normalized exponentially modified Gaussian PDF
    As a Numba JIT function, it runs slightly faster than
    'out of the box' functions.

    Parameters
    ----------
    x
        Input data
    mu
        The centroid of the Gaussian
    sigma
        The standard deviation of the Gaussian
    tau
        The characteristic scale of the Gaussian tail


    See Also 
    --------
    :func:`nb_exgauss_pdf`
    """

    den = 1/(sigma + tau*(x-mu)/sigma)
    tail_f = sigma * nb_gauss_pdf(x, mu, sigma) * den * (1.-tau*tau*den*den)
    return tail_f


@nb.njit(**kwd_2)
def nb_exgauss_pdf(x: np.ndarray, mu: float, sigma: float, tau: float) -> np.ndarray:
    r"""
    Normalized PDF of an exponentially modified Gaussian distribution. Its range of support is :math:`x\in(-\infty,\infty)`, :math:`\tau\in(-\infty,\infty)`
    Calls either :func:`nb_gauss_tail_exact` or :func:`nb_gauss_tail_approx` depending on which is computationally cheaper


    As a Numba JIT function, it runs slightly faster than
    'out of the box' functions.


    Parameters
    ----------
    x
        Input data
    mu
        The centroid of the Gaussian
    sigma
        The standard deviation of the Gaussian
    tau
        The characteristic scale of the Gaussian tail


    See Also 
    --------
    :func:`nb_gauss_tail_exact`, :func:`nb_gauss_tail_approx`
    """

    x = np.asarray(x)
    tail_f = np.empty_like(x, dtype=np.float64)
    for i in nb.prange(x.shape[0]):
        tmp = ((x[i]-mu)/tau) + ((sigma**2)/(2*tau**2))
        if tmp < limit:
            tail_f[i] = nb_gauss_tail_exact(x[i], mu, sigma, tau, tmp)
        else:
            tail_f[i] = nb_gauss_tail_approx(x[i], mu, sigma, tau)
    return tail_f


@nb.njit(**kwd)
def nb_exgauss_cdf(x: np.ndarray, mu: float, sigma: float, tau: float, lower_range: float=np.inf, upper_range: float=np.inf) -> np.ndarray:
    r"""
    The CDF for a normalized exponentially modified Gaussian.  Its range of support is :math:`x\in(-\infty,\infty)`, :math:`\tau\in(-\infty,\infty)`
    It computes the following CDF: 


    .. math::
        cdf(x,\tau,\mu,\sigma) = \tau\,pdf(x,\tau,\mu,\sigma)+ \frac{\tau}{2|\tau|}\text{erf}\left(\frac{\tau}{|\tau|\sqrt{2}}(\frac{x-\mu}{\sigma})\right) + \frac{1}{2}


    As a Numba JIT function, it runs slightly faster than
    'out of the box' functions.


    Parameters
    ----------
    x
        Input data
    mu
        The centroid of the Gaussian
    sigma
        The standard deviation of the Gaussian
    tau
        The characteristic scale of the Gaussian tail
    lower_range
        Lower bound of the Gaussian with tail
    upper_range
        Upper bound of the Gaussian with tail
    """

    abstau = np.abs(tau)
    part1 = (tau/(2*abstau)) * nb_erf((tau*(x-mu) )/(np.sqrt(2)*sigma*abstau))
    part2 = tau * nb_exgauss_pdf(x, mu, sigma, tau)
    return part1+part2+0.5


@nb.njit(**kwd_2)
def nb_exgauss_scaled_pdf(x: np.ndarray, mu: float, sigma: float, tau: float, area: float) -> np.ndarray:
    r"""
    Scaled PDF of an exponentially modified Gaussian distribution
    Can be used as a component of other fit functions w/args mu,sigma,tau
    As a Numba JIT function, it runs slightly faster than
    'out of the box' functions.

    Parameters
    ----------
    x
        Input data
    mu
        The centroid of the Gaussian
    sigma
        The standard deviation of the Gaussian
    tau
        The characteristic scale of the Gaussian tail
    area
        The number of counts in the signal
    """

    return area * nb_exgauss_pdf(x, mu, sigma, tau)


@nb.njit(**kwd)
def nb_exgauss_scaled_cdf(x: np.ndarray, mu: float, sigma: float, tau: float, area: float) -> np.ndarray:
    r"""
    Scaled CDF of an exponentially modified Gaussian distribution
    As a Numba JIT function, it runs slightly faster than
    'out of the box' functions.

    Parameters
    ----------
    x
        Input data
    mu
        The centroid of the Gaussian
    sigma
        The standard deviation of the Gaussian
    tau
        The characteristic scale of the Gaussian tail
    area
        The number of counts in the signal
    """
    
    return area * nb_exgauss_cdf(x, mu, sigma, tau)


class exgauss_gen(pygama_continuous):

    def _pdf(self, x: np.ndarray, tau: float, sigma: float) -> np.ndarray:
        x.flags.writeable = True
        return nb_exgauss_pdf(x, 0, 1, tau[0]/sigma[0]) # the scipy parameter k = tau/sigma 
    def _cdf(self, x: np.ndarray, tau: float, sigma: float) -> np.ndarray:
        x.flags.writeable = True
        return nb_exgauss_cdf(x, 0, 1, tau[0]/sigma[0])

    def get_pdf(self, x: np.ndarray, tau: float, mu: float, sigma: float) -> np.ndarray:
        return nb_exgauss_pdf(x, mu, sigma, tau) 
    def get_cdf(self, x: np.ndarray, tau: float, mu: float, sigma: float) -> np.ndarray:
        return nb_exgauss_cdf(x, mu, sigma, tau)

    def norm_pdf(self, x: np.ndarray, x_lower: float, x_upper: float, tau: float, mu: float, sigma: float) -> np.ndarray:
        return self._norm_pdf(x, x_lower, x_upper, tau, mu, sigma)
    def norm_cdf(self, x: np.ndarray,  x_lower: float, x_upper: float, tau: float, mu: float, sigma: float) -> np.ndarray:
        return self._norm_cdf(x, x_lower, x_upper, tau, mu, sigma)

    def pdf_ext(self, x: np.ndarray, area: float, x_lo: float, x_hi: float, tau: float, mu: float, sigma: float) -> np.ndarray:
        return np.abs(nb_exgauss_scaled_cdf(np.array([x_hi]), mu, sigma, tau, area)[0]-nb_exgauss_scaled_cdf(np.array([x_lo]), mu, sigma, tau, area)[0]), nb_exgauss_scaled_pdf(x, mu, sigma, tau, area)
    def cdf_ext(self, x: np.ndarray, area: float, tau: float, mu: float, sigma: float) -> np.ndarray:
        return nb_exgauss_scaled_cdf(x, mu, sigma, tau, area)

    def required_args(self) -> tuple[str, str, str]:
        return "tau", "mu", "sigma"

exgauss = exgauss_gen(name='exgauss')