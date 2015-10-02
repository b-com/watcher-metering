Installation procedures
=======================

******************
libnano libraries
******************
Communication channels between ``Agent`` and ``Publisher`` modules are supported by `nanomsg`_ library.

We integrated also the `nanoconfig`_ library to automatically configure communication channels between Agents and Publishers. It is mainly useful if you deploy several Agents and Publishers, but it is optional.

You can install these libraries from packages (Debian only) or re-build them.

Install libnano packages
^^^^^^^^^^^^^^^^^^^^^^^^
Debian packages are available on B<>COM Factory.

1. Install the libnanomsg library: 
    
  .. code:: shell

     $ cd tmp
     $ wget http://factory.b-com.com/www/watcher/download/watcher-metering/libnanomsg_0.6.0_all.deb
     $ sudo dpkg -i libnanomsg_0.6.0_all.deb

2. Install the libnanoconfig library: 
    
  .. code:: shell

      $ cd tmp
      $ wget http://factory.b-com.com/www/watcher/download/watcher-metering/libnanoconfig_0.0.1-beta_all.deb
      $ sudo dpkg -i libnanoconfig_0.0.1-beta_all.deb

Build libraries
^^^^^^^^^^^^^^^^
You can compile the `nanomsg`_ and `nanoconfig`_ libraries from the source code. Here is on way to do it:

1. Install requirements for Ubuntu or similar distribution:

  .. code:: shell

      $ sudo apt-get update
      $ sudo apt-get install build-essential python-dev autoconf libtool unzip wget
 
2. Build and install nanomsg library:

  .. code:: shell

      $ wget https://github.com/nanomsg/nanomsg/archive/0.6-beta.zip
      $ unzip 0.6-beta.zip
      $ cd nanomsg-0.6-beta
      $ ./autogen.sh
      $ ./configure
      $ make -j8
      $ sudo make install
      $ sudo ldconfig /usr/local/lib

Please also refer the instructions available on their ``README`` files.


3. Build and install nanoconfig library:

  .. code:: shell

      $ wget https://github.com/nanomsg/nanoconfig/archive/master.zip
      $ unzip master.zip
      $ cd nanomsg-master
      $ cmake .
      $ make
      $ sudo make install
      $ sudo ldconfig /usr/local/lib

Please also refer the instructions available on their ``README`` files.

**********************
Watcher Metering Agent
**********************

Install the agent
^^^^^^^^^^^^^^^^^

As ``root`` user:

1. Create the user ``watcher-metering``:

  .. code-block:: shell
 
      # groupadd watcher_metering
      # useradd -g watcher_metering watcher_metering

2. Install the Watcher Metering Agent:

  .. code-block:: shell

      # apt-get install python-pip python-dev
      # pip install python-watcher_metering

3. Create the configuration file:

  .. code-block:: shell

      # mkdir /etc/watcher-metering
      # chmod 755 /etc/watcher-metering
      # touch /etc/watcher-metering/agent.conf


  You can copy the file ``etc/watcher-metering/agent.conf.sample`` from the GIT repository and update it.


Configuration
^^^^^^^^^^^^^

The Watcher Metering Agent configuration file is self-documented. Please refer to these notes to fully understand the role of each one of them.

By default, the Watcher Metering Agent does not use ``nanoconfig`` server to get parameters to communicate with Watcher Metering Publisher(s). So, you have to set manually the ``publisher_endpoint`` URI. 

To enable ``nanoconfig`` function, set the parameter named ``use_nanoconfig_service`` to ``true`` and complete also nanoconfig URI endpoints (``nanoconfig_service_endpoint`` and ``nanoconfig_update_endpoint``).


Install the agent's drivers
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The Watcher Metering Agent uses drivers to collect metering data on the host:
 
 
1. Follow installation procedure provided with the metering driver. 

2. Edit the Watcher Metering Agent configuration file, and update the parameter ``driver_names`` by adding the new driver name in the list.

3. Restart the Watcher Metering Agent to take into account drivers updates.

Note: you can use the default Watcher Metering Agent driver available on `Github`_.

Command
-------

To run the agent you can use the following command:

.. code-block:: shell

    $ watcher-metering-agent --config-file=/etc/watcher-metering/agent.conf \ 
                             --config-file=/path/to/drivers.conf

Or even:

.. code-block:: shell

    $ watcher-metering-agent --config-dir=/etc/watcher-metering

This alternative will automatically take into account any other file containing
some configuration related to the agent (useful for dynamically including
third-party driver configuration).

But if you want to learn more about all the options this command provides you
can still use the following to access its documentation:

.. code-block:: shell

    $ watcher-metering-agent --help


**************************
Watcher Metering Publisher
**************************

Install the publisher
^^^^^^^^^^^^^^^^^^^^^

As ``root`` user:

1. Create the user ``watcher-metering``:

  .. code-block:: shell
 
      # groupadd watcher_metering
      # useradd -g watcher_metering watcher_metering

2. Install the Watcher Metering Agent:

  .. code-block:: shell

      # apt-get install python-pip python-dev
      # pip install python-watcher_metering

3. Create the configuration file:

  .. code-block:: shell

      # mkdir /etc/watcher-metering
      # chmod 755 /etc/watcher-metering
      # touch /etc/watcher-metering/publisher.conf
     
  You can copy the file ``etc/watcher-metering/publisher.conf.sample`` from the GIT repository and update it.


Configuration
-------------

The Watcher Metering Publisher configuration file is self-documented. Please refer to these notes to fully understand the role of each one of them.

By default, the Watcher Metering Publisher does not use ``nanoconfig`` server to get parameters to communicate with Watcher Metering Agent(s). So, you have to set manually the listening endpoint URI ``publisher_endpoint``. 

To enable ``nanoconfig`` function, set the parameter named ``use_nanoconfig_service`` to ``true`` and complete also nanoconfig URI endpoints (``nanoconfig_service_endpoint`` and ``nanoconfig_update_endpoint``).

The Watcher Metering Publisher can push metering data either to a `Riemann`_ CEP module (default configuration) or directly into `Ceilometer`_, according to the parameter named ``metrics_store``. 

The section ``[metrics_store.riemann]`` groups all parameters useful to interact with a Riemann CEP. If you use a CEP Riemann service, complete at least the  Riemann endpoint URI ``store_endpoint``.

If you want to use Ceilometer as storage backend, don't forget to complete the section ``[keystone_authtoken]``, in order to allow the Watcher Metering Publisher to query the Identity Service for token, before to push metering data into Ceilometer.

Command
-------

To run the publisher you can use the following command:

.. code-block:: shell

    $ watcher-metering-publisher \
        --config-file=/etc/watcher-metering/publisher.conf

Or even:

.. code-block:: shell

    $ watcher-metering-publisher --config-dir=/etc/watcher-metering

This alternative will automatically take into account any other file containing
some configuration related to the publisher (useful for dynamically including
third-party driver configuration).

But if you want to learn more about all the options this command provides you
can still use the following to access its documentation:

.. code-block:: shell

    $ watcher-metering-publisher --help
    

.. _nanomsg: https://github.com/nanomsg/nanomsg
.. _nanoconfig: https://github.com/nanomsg/nanoconfig
.. _Ceilometer: http://docs.openstack.org/developer/ceilometer/
.. _Github: http://todfiine
.. _Riemann: :http://riemann.io/
