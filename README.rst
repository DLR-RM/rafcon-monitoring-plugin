RAFCON Monitoring Plugin
========================

A RAFCON plugin to remotely monitor and control state machines.
[This is development code. We don't give support for this code yet.]


Features:
*********

* RAFCON can be started as server or as client
* Clients get the information of currently active states, and visualize them by highlighting the active states
* Clients can send execution commands (start, stop, pause, step) to the server
* Communication is done via UDP: thus it can cope with signal delays of several seconds
* Multiple clients can connect to the server (also from different IPs)
* Network Tab shows the ping to other endpoints

Not supported Features:
***********************

* Console Log is currently not forwarded (Console log can be analyzed in ssh shell)
* Execution history is currently not forwarded (use execution_log_viewer by first copying file from remote system via ssh)
* As this is a monitoring plugin, making state machine changes is not possible


Installation on Ubuntu 16.04 - 18.04:
*************************************

Install pygobject (needed for pygtkcompat) by execute commands of "Installing from PyPI with pip" of:
https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-logo-ubuntu-debian-logo-debian

Install twisted via:

.. code-block:: bash

    pip2.7 install --user --upgrade twisted

Clone python_acknowledged_udb and add to PYTHONPATH:

.. code-block:: bash

    git clone https://github.com/DLR-RM/python-acknowledged-udp.git
    export PYTHONPATH=$PYTHONPATH:/path/to/your/clone


Running monitoring plugin:
**************************

See https://rafcon.readthedocs.io/en/latest/tutorials.html#using-the-monitoring-plugin

Before being able to launch the plugin add it to the RAFCON_PLUGIN_PATH environment variable:

export RAFCON_PLUGIN_PATH=/path/to/repo/rafcon_monitoring_plugin/python/monitoring

Information about the configuration can be found on: https://rafcon.readthedocs.io/en/latest/configuration.html#monitoring-plugin-configuration


