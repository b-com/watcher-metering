================
Watcher Metering
================

Watcher Metering collects system metrics and publishes them to a store.
To do so, it is composed of two elements:

- The ``Agent`` who collects the desired metrics and sends it to a publisher.
  The ``Agent`` is meant to run on each monitored host (container, VM, ...)
- The ``Publisher`` who gathers measurements from one or more agent and pushes
  them to the desired store. The currently supported stores are Riemann
  (for CEP) and Ceilometer.

This project is part of the Watcher_ solution. For more information on Watcher, you can also refer to its OpenStack wiki_
page.

You will another documentation here:
    - `Architecture`_
    - `Installation guide`_
    - `API`_
    - `Development guide`_
 
.. _Watcher: http://factory.b-com.com/www/watcher/
.. _wiki: https://wiki.openstack.org/wiki/Watcher
.. _nanoconfig: https://github.com/nanomsg/nanoconfig
.. _Ceilometer: http://docs.openstack.org/developer/ceilometer/
.. _Riemann: :http://riemann.io/
.. _Architecture: ./doc/source/dev/architecture.rst
.. _Installation guide: ./doc/source/deploy/installation.rst
.. _API: ./doc/source/api/reference.rst
.. _Development guide: ./doc/source/dev/quickstart.rst
