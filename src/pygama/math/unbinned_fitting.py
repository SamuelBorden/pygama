"""
pygama convenience functions for fitting ubinned data
"""
import logging

from iminuit import Minuit, cost

log = logging.getLogger(__name__)


def fit_unbinned(func, data, guess=None,
             Extended=True, cost_func = 'LL', simplex=False,
             bounds=None, fixed=None):
    """Do a unbinned fit to data.
    Default is Extended Log Likelihood fit, with option for other cost functions.

    Parameters
    ----------
    func : function
        the function to fit
    data : ndarray
        the data values to be fit
    guess : ndarray
        initial guess parameters
    Extended : bool
        run extended or non extended fit
    cost_func : str or None
        cost function to use. LL is ExtendedUnbinnedNLL, None is for just UnbinnedNLL
    simplex : bool
        whether to include a round of simpson minimisation before main minimisation
    bounds : list of tuples
        Each tuple is (min, max) for the corresponding parameters.
        Bounds can be None, e.g. [(0,None), (0,10)]
    fixed : list of bools
        list of parameter indices to fix

    Returns
    -------
    pars, errs, cov : tuple of ndarrays
        the best-fit parameters and their errors / covariance
    """
    if guess is None:
        raise NotImplementedError("auto-guessing not yet implemented, you must supply a guess.")

    if cost_func =='LL':
        if Extended ==True:
            cost_func = cost.ExtendedUnbinnedNLL(data, func)

        else:
            cost_func = cost.UnbinnedNLL(data, func)

    m = Minuit(cost_func, *guess)
    if bounds is not None:
        m.limits = bounds
    if fixed is not None:
        for fix in fixed:
            m.fixed[fix] = True
    if simplex == True:
        m.simplex().migrad()
    else:
        m.migrad()
    m.hesse()
    return m.values, m.errors, m.covariance