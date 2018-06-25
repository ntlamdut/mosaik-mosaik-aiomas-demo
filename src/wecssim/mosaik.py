"""
Implementation of the `mosaik API`_ for the WECS sim.

.. _mosaik API:
   https://mosaik.readthedocs.org/en/latest/mosaik-api/high-level.html

"""
from collections import namedtuple
import io
import lzma

import mosaik_api
import numpy as np

from .wecs import WECS


# The meta data that the "init()" call will return.
META = {
    'models': {
        # We only expose the WECS agent as model to mosaik:
        'WECS': {
            'public': True,
            'params': [
                # See "sim.WECS.__init__()" for descriptions of the params:
                'P_rated',
                'v_rated',
                'v_min',
                'v_max',
            ],
            'attrs': [
                'P_max',  # output / input, can be set by an agent
                'P',  # output
                'v',  # output
            ],
        },
    },
}
STEP_SIZE = 15  # minutes

# Used to store a single WECS' config parameters
WecsConfig = namedtuple('WecsConfig', 'P_rated, v_rated, v_min, v_max')


class WecsSim(mosaik_api.Simulator):
    """This class implements the mosaik API."""
    def __init__(self):
        # We need to pass the META data to the parent class which will extend
        # it and store it as "self.meta":
        super().__init__(META)

        self.wind_file = None  # File handle for wind velocities
        self.wecs = {}  # Maps EIDs to wecs index
        self.wecs_config = []  # List of WecsConfig tuples
        self.sim = None  # WECS sim instance

    def init(self, sid, wind_file):
        """*wind_file* is a CSV file containing one or more time series for
        wind velocities.

        If the file extension is *.xz*, it is assumed that file file is LZMA
        compressed.  Else, it must be pure, uncompressed CSV data.

        The time series must be columnar data in 15 minute resolution.
        Multiple series must be separated by comma.  Here is an example with
        three 1h time series:

            3.5, 0.0, 2.3
            3.5, 0.1, 2.2
            3.6, 0.3, 2.3
            3.9, 0.5, 2.5

        If there are more WECS than time series in the file, a time series is
        reused multiple times using modulo (``ts_idx = wecs_idx % ts_count``).

        """
        open = lzma.open if wind_file.endswith('.xz') else io.open
        self.wind_file = open(wind_file, 'rt')

        # Return our simulator's meta data to mosaik:
        return self.meta

    def create(self, num, model, **wecs_params):
        """Create *num* instances of *model*.

        Mosaik makes sure that we get valid values for *num* and *model*.
        Since we only exposed one model, we know that *model* is "WECS".

        There might be multiple "create()" calls, but we only need one
        wecssim.sim.WECS() instance.  So we just collect all param sets and
        create the WECS() instance in later "setup_done()":

        """
        n_wecs = len(self.wecs_config)  # Number of WECS so far
        entities = []  # This will hold the entity data for mosaik
        for wecs_idx in range(n_wecs, n_wecs + num):
            # The entity ID for mosaik:
            eid = 'wecs-%s' % wecs_idx
            # Remember the index of the current entity in "self.wecs_config"
            # and store the config for the current entity:
            self.wecs[eid] = wecs_idx
            self.wecs_config.append(WecsConfig(**wecs_params))

            # Add entity data for mosaik
            entities.append({'eid': eid, 'type': model})

        # Return the list of entities to mosaik:
        return entities

    def setup_done(self):
        """Called once the scenario creation is done and just before the
        simulation starts.

        We now have the configuration for all WECS and can instantiate the
        simulator with it.

        """
        # Create a NumPy array with one row for each WECS.  This works because
        # "self.wecs_config" is just a list of tuples that contain only float
        # numbers:
        config = np.array(self.wecs_config, dtype=float)

        # Config stores the data row-wise, but the sim needs the data
        # column-wise, so we just transpose the array and expand it into the
        # four columns "P_rated", "v_rated", "v_min", "v_max".
        self.sim = WECS(*config.T)
        # The upper code is equivalent to this:
        #
        #   P_rated, v_rated, v_min, v_max = config.T
        #   self.sim = WECS(P_rated, v_rated, v_min, v_max)

        # This method has no return value

    def step(self, time, inputs):
        """Step the simulator ahead in time.  The current simulation time is
        *time*.

        *inputs* may contain *P_Max* values set by the MAS.  It is a dict
        like::

            {
                'wecs-0': {
                    'P_max': {'agent-0': 42},
                },
                ...
            }

        """
        # Generate a new vector with P_Max values.  Use P_rated as default and
        # override the default value if necessary:
        P_max = self.sim.P_rated.copy()
        for eid, wecs_inputs in inputs.items():
            idx = self.wecs[eid]
            if 'P_max' in wecs_inputs:
                # "wecs_inputs" must be a dict with only one entry, because
                # there is a 1:1 relation between WECS and agent:
                # wecs_inputs == {'P_max': {'src_eid': p_max_i}}
                assert len(wecs_inputs['P_max']) == 1
                # Pop the single value from the dict:
                _, p_max_i = wecs_inputs['P_max'].popitem()
                P_max[idx] = p_max_i

        # Set the P_max vector to the simulator:
        self.sim.set_P_max(P_max)

        # Get current wind velocities from the file and step the sim:
        data = next(self.wind_file).strip().split(',')
        data = [float(val) for val in data]
        data_len = len(data)
        wecs_count = len(self.wecs)
        # "data_len" may be smaller than "wecs_count" (see "init()"),
        # so we need to expand it:
        data = np.array([data[i % data_len] for i in range(wecs_count)])
        self.sim.step(data)

        # We want to do our next step in STEP_SIZE minutes:
        return time + (STEP_SIZE * 60)

    def get_data(self, outputs):
        """Return the data requested by mosaik.  *outputs* is a dict like::

            {
                'wecs-0': ['v', 'P'],
                ...
            }

        Return a dict with the requested data::

            {
                'wecs-0': {
                    'v': 23,
                    'P': 42,
                },
                ...
            }

        """
        data = {}
        for eid, attrs in outputs.items():
            if eid not in self.wecs:
                raise ValueError('Unknown entity ID "%s"' % eid)

            idx = self.wecs[eid]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['WECS']['attrs']:
                    raise AttributeError('Attribute "%s" not available' % attr)
                data[eid][attr] = float(getattr(self.sim, attr)[idx])

        return data


def main():
    """Run our simulator and expose the "WecsSim"."""
    return mosaik_api.start_simulation(WecsSim(), 'WECS simulator')


if __name__ == '__main__':
    main()
