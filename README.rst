====================================
How to couple *aiomas* with *mosaik*
====================================

This example project demonstrates how you can couple a multi-agent system (MAS)
written in aiomas_ to a mosaik_ simulation.

What gets covered here?

- Writing a simple, controllable simulator and coupling it with mosaik using
  the mosaik-api_ package

- Writing a *simple* MAS with aiomas and couple it *without* using the
  *mosaik-api* package, including:

  - Distributing agents over multiple CPU cores

  - Managing agents and time in remote containers

  - Forward data from mosaik to your agents

  - Collecting set-points/schedules from agents and send them to mosaik as
    input for the controlled simulator.

And what not?

- Packaging and Deployment of your system

- Testing (neither unit nor system/integration testing)

- Fancy distributed algorithms

- Fancy agent architecture that makes it easy to change the planning algorithm
  or lets agents communicate with simulated models or real resources.

.. _aiomas: https://aiomas.readthedocs.io/
.. _mosaik: https://mosaik.readthedocs.io/
.. _mosaik-api: https://mosaik.readthedocs.io/en/latest/mosaik-api/high-level.html

This document explains how to install and run the example project.  It also
gives you a rough idea how the scenario looks like and discusses the basic
ideas behind the controlled simulator and the controlling multi-agent system.
In-depth comments and discussions are within the source code itself, because
you have to read it anyways if you want to learn something.  :)


Contents
========

- `Scenario`_

- `Installation and execution`_

- `The WECS simulator explained`_

- `The MAS explained`_

- `The mosaik scenario explained`_


.. _scenario:

Scenario
========

The simulation consists of three components:

- A wind energy conversion system (WECS) simulator

- A multi-agent system with on agent for each simulated WECS and one central
  controller agent

- An HDF database “simulator” that collects some data from the WECS simulator

In this scenario, the WECS form a small wind farm.  The agents observe the
power output of their WECS.  A controlling agent regularly collects the current
feed-in from the WECS agents and checks if it is above a certain *maximum power
feed-in* for the wind farm.  If the combined power output of the WECS is above
the limit, the controller calculates the maximum allowed power output for each
WECS and sends it to the WECS agents which forward it to the actual WECS.

A database collects the wind speed, active power output and the power limit
for each simulated WECS.

This scenario is actually very dumb, bit it has all the data-flows that you are
gonna have in a “real” project.


.. _installation-and-execution:

Installation and execution
==========================

This example projects requires Python 3.  In order to install some of the
required packages (like NumPy or h5py), you may need a compiler (or Download
a Windows binary from `Christoph Gohlke’s site`_).

If you have a compiler and everything (if not, more details follow below),
create a Python 3.5 virtualenv_ and install all dependencies:

.. code-block:: console

   $ pip install -r requirements-setup.txt

You can then run the simulation by executing:

.. code-block:: console

   $ python scenario.py
   Starting "WecsSim" as "WecsSim-0" ...
   Starting "MAS" as "MAS-0" ...
   Starting "DB" as "DB-0" ...
   INFO:mosaik_api:Starting MosaikHdf5 ...
   Starting simulation.
   Simulation finished successfully.

If this doesn’t work, try to re-install all dependencies from
``requirements.txt`` which contains a complete list of all packages with pinned
version numbers:

.. code-block:: console

   $ pip install requirements.txt

.. _Christoph Gohlke’s site: http://www.lfd.uci.edu/~gohlke/pythonlibs/
.. _virtualenv: https://www.dabapps.com/blog/introduction-to-pip-and-virtualenv-python/


Detailed instructions
---------------------

The following sub-sections provide detailed installation instructions for
Linux, OS X and Windows.

Linux
^^^^^

The following instructions were mainly tested on Ubuntu 16.04.  For older
releases or other distributions, the set of dependencies that you need to
install may vary:

.. code-block:: console

   $ sudo apt install python3 python3-dev python3-pip build-essential libhdf5-dev libmsgpack-dev

.. hint::

   If you have an older version of Ubuntu, you need to install Python 3.5 from
   a PPA.  `This answer on Askubuntu`_ explains how to do this (don’t forget to
   also install ``python3.5-dev``.  You should also install
   ``libatlas-base-dev`` prior to compiling NumPy.

   .. _This answer on Askubuntu: https://askubuntu.com/questions/682869/install-python-3-5-on-vivid-using-apt-get/682875#682875

Furthermore, we need virtualenv which can create isolated Python environments
for different projects.  We'll also install *virtualenvwrapper* which
simplifies your life with virtualenvs:

.. code-block:: console

   $ sudo python3 -m pip install -U pip virtualenv virtualenvwrapper
   $ # Update your bashrc to load venv. wrapper automatically:
   $ echo "# Virtualenvwrapper" >> ~/.bashrc
   $ echo "export VIRTUALENVWRAPPER_PYTHON=`which python3`" >> ~/.bashrc
   $ echo ". $(which virtualenvwrapper.sh)" >> ~/.bashrc
   $ . ~/.bashrc

Now you can create a new virtualenv, ``cd`` into the project directory (the one
containing *this* file), and install all requirements:

.. code-block:: console

   $ mkvirtualenv --python=python3.5 mosaik-aiomas-demo
   (mosaik-aiomas-demo)$ export HDF5_DIR=/usr/lib/x86_64-linux-gnu/hdf5/serial/
   (mosaik-aiomas-demo)$ cd mosaik-aiomas-demo/
   (mosaik-aiomas-demo)$ pip install -r requirements-setup.txt

.. note::

   Exporting the environment variable *HDF5_DIR* may not be necessary in all
   cases (e.g., if you use Ubuntu 14.04), but it also does not hurt.

Now you should be able to run the mosaik scenario:

.. code-block:: console

   (mosaik-aiomas-demo)$ python scenario.py


OS X
^^^^

OS X ships with an outdated version of Python.  The best/easiest way to install
Python 3.5 and other dependencies is to use Homebrew_.  Open a terminal window
and run the following command:

.. _Homebrew: http://brew.sh/

.. code-block:: console

   $ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Once the installation is successful, you can install Python 3 and the build
dependencies:

.. code-block:: console

   $ brew install python3 hdf5 msgpack

Furthermore, we need virtualenv which can create isolated Python environments
for different projects.  We'll also install *virtualenvwrapper* which
simplifies your life with virtualenvs:

.. code-block:: console

   $ python3 -m pip install -U virtualenv virtualenvwrapper
   $ # Update your bashrc to load venv. wrapper automatically:
   $ echo "# Virtualenvwrapper" >> ~/.bashrc
   $ echo "export VIRTUALENVWRAPPER_PYTHON=`which python3`" >> ~/.bashrc
   $ echo ". $(which virtualenvwrapper.sh)" >> ~/.bashrc
   $ . ~/.bashrc

Now you can create a new virtualenv, ``cd`` into the project directory (the one
containing *this* file), and install all requirements:

.. code-block:: console

   $ mkvirtualenv -p python3.5 mosaik-aiomas-demo
   (mosaik-aiomas-demo)$ cd mosaik-aiomas-demo/
   (mosaik-aiomas-demo)$ pip install -r requirements-setup.txt

Now you should be able to run the mosaik scenario:

.. code-block:: console

   (mosaik-aiomas-demo)$ python scenario.py


Windows
^^^^^^^

Download the latest Python (>= 3.5) Windows installer (preferably, 64bit) from
python.org_ and run it.  Check the checkbox *Add Python 3.5 to PATH*.
Remember whether you installed the 32bit or 64bit version.

Then go to Christoph Gohlke’s website and download the latest version of
blosc_, msgpack_, numpy_, and h5py_.  Select a version matching your Python
version and bit-ness (e.g. ``*-cp35-cp35m-win_amd64.whl``).

Then start a windows command prompt.

We need virtualenv which can create isolated Python environments
for different projects.  We'll also install *virtualenvwrapper-win* which
simplifies your life with virtualenvs:

.. code-block:: doscon

   C:\Users\monty> python -m pip install -U virtualenv virtualenvwrapper-win

Now you can create a new virtualenv, ``cd`` into the project directory (the one
containing *this* file), and install all requirements:

.. code-block:: doscon

   C:\Users\monty> mkvirtualenv -p python3.5 mosaik-aiomas-demo
   C:\Users\monty> cd mosaik-aiomas-demo
   (mosaik-aiomas-demo)C:\Users\monty\mosaik-aiomas-demo> pip install -f C:\Users\monty\Downloads -r requirements-setup.txt

.. _Homebrew: http://brew.sh/

Now you should be able to run the mosaik scenario:

.. code-block:: doscon

   (mosaik-aiomas-demo)C:\Users\monty\mosaik-aiomas-demo> python scenario.py

.. _python.org: https://www.python.org/downloads/
.. _blosc: http://www.lfd.uci.edu/~gohlke/pythonlibs/#blosc
.. _msgpack: http://www.lfd.uci.edu/~gohlke/pythonlibs/#msgpack
.. _numpy: http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
.. _h5py: http://www.lfd.uci.edu/~gohlke/pythonlibs/#h5py


.. _the-wecs-simulator-explained:

The WECS simulator explained
----------------------------

You can find the wind energy conversion system (WECS) simulator in
``src/wecssim/``.

The simulation model itself is define in ``src/wecssim/wecs.py``.  It only
contains the class ``wecssim.sim.WECS`` with the simulation model.

The module ``src/wecssim/mosaik.py`` implements the mosaik API for the
simulator and also serves as an entry point: If you execute ``PYTHONPATH=src/
python -m wecssim.mosaik``, the function is ``wecssim.mosaik.main()`` is
called.

The mosaik documentation provides a `detailed description`_ of how all that
works.

.. _detailed description: https://mosaik.readthedocs.io/en/latest/mosaik-api/index.html

There are also some tests for the WECS simulator.  They are located in the
``tests/`` directory and can be run via pytest:

.. code-block:: console

   (mosaik-aiomas-demo)$ PYTHONPATH=src py.test


.. _the-mas-explained:

The MAS explained
-----------------

The MAS package in ``src/mas/`` is a little more complex.

The file ``mosaik.py`` contains the entry point for starting the MAS.  It also
implements the `low-level mosaik API`_ (the aiomas RPC layer in conjunction
with the JSON codec uses the same network protocol as mosaik and so it is
easier to directly implement the low-level API as an aiomas RPC service than
using the high-level API).  Click_ is used to parse the command lines passed to
``mas.mosaik.main()``.  Apart from the class ``MosaikAPI`` which, as its name
suggests, implements the mosaik API, there is also a ``MosaikAgent``.  That is
an aiomas agent acting as a gateway between the mosaik API and the actual
multi-agent system.

The multi-agent system consists of multiple WECS agents (one for each simulated
WECS) and a central controller agent.

The ``MosaikAgent`` and ``Controller`` (found in ``controller.py``) run in the
same container within the master process (the one that also serves the mosaik
API).  For each CPU core on your machine, there will also be one sub-process
with an agent container.  The ``WECS`` agents will be evenly distributed over
these remote containers.  This does not make a lot of sense in this scenario,
but once your agents will actually perform more complicated (e.g., machine
learning) tasks, this helps you to fully utilize all the computational power
your CPU provides.  The container sub-processes are implemented in
``container.py``.

All containers use the aiomas *ExternalClock* which is synchronized to the time
of the mosaik simulation.  The MAS receive the current simulation time with
each ``step()`` call from mosaik.

.. _low-level mosaik API: https://mosaik.readthedocs.org/en/latest/mosaik-api/low-level.html
.. _Click: http://click.pocoo.org/6/


.. _the-mosaik-scenario-explained:

The mosaik scenario explained
-----------------------------

The scenario defined in ``scenario.py`` is a standard mosaik scenario.  It
defines a ``main()`` that is executed when you run the script from the command
line.

It starts the three components involved in our simulation: the WECS simulator,
the multi-agent system and an HDF5 database to collect some data.

The wind data for the WECS simulator can be found in the CSV file in the
``data/`` directory.  This is also the place where the HDF5 database will be
created.
