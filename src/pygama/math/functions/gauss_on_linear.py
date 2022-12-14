import sys

import numba as nb
import numpy as np

from scipy.stats import rv_continuous
from pygama.math.functions.sum_dists import sum_dists

from pygama.math.functions.gauss import gaussian
from pygama.math.functions.linear import linear



class gauss_on_linear_gen(sum_dists):
    r"""
    Provide a convenience function for a Gaussian on top of a linear distribution. 

    Parameters 
    ----------
    area1 
        The area of the Gaussian distribution
    mu, sigma
        The location and scale of the first Gaussian
    area2 
        The area of the linear distributions respectively
    m 
        The slope of the linear distribution 
    b 
        The y intercept of the linear distribution

    Returns 
    -------
    gauss_on_linear
        A subclass of sum_dists and rv_continuous, has methods of pdf, cdf, etc.
        
    Notes 
    -----
    link_pars automatically makes sure that the linear distribution is only evaluated on the range of the x array eventually passed 
    Parameters must be in the order (area1, mu, sigma, area2, m, b) 
    """

    def __init__(self):
        
        (area1, mu, sigma, area2, m, b) = range(6)

        args = [gaussian, [mu, sigma, area1], linear, [area2, area2, m, b, area2]]
        
        super().__init__(*args, frac_flag = "areas")

    def _link_pars(self, shape_par_idx, area_idx, frac_idx, total_area_idx, params, areas, fracs, total_area):
        shape_pars, cum_len, areas, fracs, total_area = super()._link_pars(shape_par_idx, area_idx, frac_idx, total_area_idx, params, areas, fracs, total_area)
    
        # Set x_lower and x_upper to np.inf so the linear function uses the maximum and minimum of x to normalize   
        shape_pars[2] = np.inf
        shape_pars[3] = np.inf 

        return shape_pars, cum_len, areas, fracs, total_area 

    def get_req_args(self) -> tuple[str, str, str, str, str, str]:
        r"""
        Return the required args for this instance
        """ 

        return "n_sig", "mu", "sigma", "n_bkg", "m", "b"

        
gauss_on_linear = gauss_on_linear_gen()