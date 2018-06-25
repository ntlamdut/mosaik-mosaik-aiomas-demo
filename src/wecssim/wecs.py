"""
Simple simulation of a wind energy coversion system (WECS).

WECS have a nominal power *P_rated* (in kW) that they reach at a wind speed of
*v_rated* m/s.  If the wind speed exceeds *v_max* m/s, they turn off to avoid
damage to their mechanics.  WECS turn off if the wind speed drops below *v_min*
m/s.

We ignore the wind turbines inertia and the smoothing of the power slope as we
reach *v_rated*.  Thus, the model is barely valid for a step size of 15
minutes.

But since this is just for a demo scenario, we don't care. :)

The basic formula for calculating a WECS's active power output for a given wind
velocity v is::

    if v < v_min:
        P = 0
    elif v > v_max:
        P = 0
    elif v >= v_rated:
        P = P_rated
    else:
        P = (v_rated ** -3) * (v ** 3) * P_rated

If *v* is below *v_min* and above *v_max*, the WECS is turned off.  If *v* is
between *v_rated* and *v_max*, the power output is the rated power of the wind
turbine.

If *v* is between *v_min* and *v_rated*, the power output is in qubic relation
to *v* (P = x * v**3).  We standardize *v* with the *v_rated* so that the term
``(v_rated ** -3) * (v ** 3)`` produces a number in [0, 1].  We then multiply
the result with the wind turbines rated power to get its actual active power
output.

In order to speed up computation, we don't represent multiple WECS as multiple
instances of :class:`WECS` but use one NumPy array for each attribute which
contain the values for all simulated instances.

The maximum power output of a WECS can be controlled (by an external party) by
setting the *P_max* attribute.

"""
import numpy as np


HOUR = 60  # An hour has 60 minutes
STEP_MINUTES = 15

P_rated = 5000  # kW
v_min = 3.5  # m/s
v_rated = 13  # m/s
v_max = 25  # m/s


class WECS:
    def __init__(self, P_rated, v_rated, v_min, v_max):
        """Created a number of wind energy conversion systems.

        All four arguments need to be NumPy arrays of the same length.  That
        means, the first WECS is represented by ``P_rated[0]``, ``v_rated[0]``,
        ``v_min[0]`` and ``v_max[0]``.  The second one by ``P_rated[1]``,
        ``v_rated[1]``, ..., and so forth.

        """
        # All input vectors should be of the same length
        self.count = len(P_rated)
        assert len(v_rated) == self.count
        assert len(v_min) == self.count
        assert len(v_max) == self.count

        # P_rated must be > 0
        assert np.all(P_rated > 0)

        # v_min < v_rated < v_max
        assert np.all(v_min < v_rated)
        assert np.all(v_rated < v_max)

        # Store all params:
        self.P_rated = P_rated
        self.v_rated = v_rated
        self.v_min = v_min
        self.v_max = v_max

        # Make prams read-only to prevent accidental change:
        self.P_rated.setflags(write=False)
        self.v_rated.setflags(write=False)
        self.v_min.setflags(write=False)
        self.v_max.setflags(write=False)

        self.P_max = P_rated  # Current power output limit for all WECS

        self.P = None  # Current power output of all WECS
        self.v = None  # Current wind speed for all WECS

    def step(self, v):
        """Update the current power output "self.P" based on the wind velocity
        vector
        *v*.

        *v* must be a NumPy array with the same length as "self.P_rated".

        """
        # Check "v" and store it:
        assert len(v) == self.count
        self.v = v

        # Calculate the theoretical power output:
        P = (self.v_rated ** -3) * (v ** 3) * self.P_rated
        # Set it to 0 if there to little or to much wind:
        P[(v < self.v_min) | (v > self.v_max)] = 0
        # Trim it if it exceeds P_rated or P_max:
        P = np.minimum(P, self.P_rated)
        P = np.minimum(P, self.P_max)

        # Set new state:
        self.P = P

    def set_P_max(self, P_max):
        """Set a vector with new power limits.

        *P_max* must be a NumPy array with the same length as "self.P_rated".
        All values must be in the interval [0, P_rated].

        """
        assert len(P_max) == self.count
        assert np.all(P_max >= 0)
        assert np.all(P_max <= self.P_rated)

        self.P_max = P_max
