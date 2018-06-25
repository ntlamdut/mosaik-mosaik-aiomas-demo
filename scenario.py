"""
This file contains the mosaik scenario.  To start the simulation, just run this
script from the command line::

    $ python scenario.py

Since neither the simulator in ``src/wecssim`` nor the MAS in ``src/mas`` are
installed correctly, we add the ``src/`` directory to the PYTHONPATH so that
Python will find these modules.


"""
import sys

import mosaik

# Add the "src/" dir to the PYTHONPATH to make its packages available for
# import:
sys.path.insert(0, 'src/')


# We have the WECS simulator, a multi-agent system, and a database:
SIM_CONFIG = {
    'WecsSim': {
        # The WECS sim can be run in-process.  Parallelization is not required
        # here and data-exchange with in-process simulators is a lot faster:
        'python': 'wecssim.mosaik:WecsSim',
    },
    'MAS': {
        # The MAS needs to be run as separate process to allow the agents to
        # continue with background calculations and planning while mosaik is
        # doing other stuff.
        #
        # The "python" placehold will be replaced by mosaik with the path to
        # the same interpreter that is used to run THIS script.  The "addr"
        # placeholder will be replaced with mosaik's network address.
        #
        # Again, we need to extend the PYTHONPATH so that Python can find our
        # packages:
        'cmd': '%(python)s -m mas.mosaik -l debug %(addr)s',
        'env': {
            'PYTHONPATH': 'src/',
        },
        # Newer versions of mosaik might favor this new-style formatting:
        # 'cmd': '{python} -m mas.mosaik -l debug {addr}',
        # 'env': {
        #     'PYTHONPATH': 'src/',
        # },
    },
    'DB': {
        # The HDF5 db should also be run as a separate process:
        'cmd': 'mosaik-hdf5 %(addr)s',
        # 'cmd': 'mosaik-hdf5 {addr}',
    },
}

# We now define some constants with configuration for the simulator and the
# MAS.  This way, we can easily see and edit the config values without touching
# the actual scenario:

# Simulation duration:
DURATION = 3600 * 24 * 1  # 1 day

# File with wind data *v* in *m/s* with 15min resolution:
WIND_FILE = 'data/wind_speed_m-s_15min.csv'

# WecsSim config grouped by type.  Each entry is a tuple "(n_wecs, params)":
WECS_CONFIG = [
    # Two smaller WECS:
    (2, {'P_rated': 2000, 'v_rated': 12, 'v_min': 2.0, 'v_max': 25}),
    # One big WECS:
    (1, {'P_rated': 5000, 'v_rated': 13, 'v_min': 3.5, 'v_max': 25}),
]

# MAS config
START_DATE = '2016-01-01T00:00:00+01:00'  # CET
CONTROLLER_CONFIG = {
    'max_windpark_feedin': 7000,  # Maximum power output of all WECS in kW
    'check_interval': 60 * 15,  # How often check the current feed-in
}

# Database config
DB_PATH = 'data/mosaik_results.hdf5'


def main():
    """Compose the mosaik scenario and run the simulation."""
    # We first create a World instance with our SIM_CONFIG:
    world = mosaik.World(SIM_CONFIG)

    # We then start the WECS simulator and our MAS and pass the "init()" params
    # to them:
    wecssim = world.start('WecsSim', wind_file=WIND_FILE)
    mas = world.start('MAS',
                      start_date=START_DATE,
                      controller_config=CONTROLLER_CONFIG)

    # Create WECS and agent instances/entities.
    #
    # We will create one (WECS, agent) pair at a time and immediately connect
    # them.  This way, we can easily make sure they both have the same config
    # values and thus represent the same WECS.
    #
    # It would also be possible to create multiple WECS/agent and the same time
    # via "wecssim.WECS.create(n_wecs, **params)" but it would make connecting
    # the right WECS to right agent a bit more complicated and error prone:
    wecs = []
    for n_wecs, params in WECS_CONFIG:  # Iterate over the config sets
        for _ in range(n_wecs):
            w = wecssim.WECS(**params)
            a = mas.WecsAgent(**params)
            # Connect "w.P" to "a.P" and allow "a" to do async. requests to "w"
            # (e.g., set_data() to set new P_max to "w"):
            world.connect(w, a, 'P', async_requests=True)

            # Remember the WECS entity for connecting it to the DB later:
            wecs.append(w)

    # Start the database process and connect all WECS entities to it:
    db = world.start('DB', step_size=60*15, duration=DURATION)
    hdf5 = db.Database(filename=DB_PATH)
    mosaik.util.connect_many_to_one(world, wecs, hdf5, 'v', 'P', 'P_max')

    # Run the simulation
    world.run(DURATION)


if __name__ == '__main__':
    main()
