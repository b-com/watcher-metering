=============================
Watcher metering architecture
=============================

************
Architecture
************
  .. figure:: architecture.png
     :height: 320px
     :width: 670px

     Watcher metering overall architecture

*****
Agent
*****

The Watcher Metering Agent is a easy extensible module used to collect metrics from any resources (physical or virtual     resources, PDUS, ...), thanks to plugged metering drivers. Drivers collects one or more metrics (or Measurement) and notifies the Agent of them. Finally, the Agent sends the metric(s) to a Publisher node. Basically, an Agent is deployed on each OpenStack Compute nodes.

Default drivers are available on `watcher-metering-drivers`_ project.

To implement new a driver, please follow the `quickstart`_ documentation.

*********
Publisher
*********

The Publisher is responsible for gathering metrics from multiple Agent nodes, before channeling them to the right store (with or without some pre-processing). Basically, a Publisher is deployed on a OpenStack Controler node.

The Publisher workflow is the following:

* It loads the configuration which defines the store to use (Riemann_ or Ceilometer_)
* It receives a measurement from an Agent
* The measurement is pre-processed to match the format the store requires
* The formatted metric is then sent to the store

Note: Publisher only supports connections with Riemann or Ceilometer. But you're welcome if you want to add new store :) 

******************************************
Communication between Agent and Publisher
******************************************

We use `nanomsg`_ facility to enable communication between Agent(s) and Publisher. nanomsg is a socket library that provides several common communication patterns (MIT Licenced). This library, implemented in C/C++, is fast and optimized for scalability. Ideal for real time metering.

	
.. _quickstart: ./quickstart.rst
.. _watcher-metering-drivers: https://github.com/b-com/watcher-metering-drivers
.. _Riemann: http://riemann.io
.. _Ceilometer: https://wiki.openstack.org/wiki/Ceilometer
.. _nanomsg: https://github.com/nanomsg/nanomsg
