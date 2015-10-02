=============
API Reference
=============

Terminology
===========

What is a driver?
-----------------

A driver a is a piece of code that can be loaded at runtime by the application.
A driver is an entry point that is loaded specifically (i.e. named) within a
group/section whereas extensions/plugins refer to entry points which are loaded
altogether with the rest of their group/section.

This terminology has been taken from the stevedore_ package, so please refer to
this documentation if you want to better understand this terminology.

This pattern has been extended in the context of this project to provide the
ability to load our entry point using options provided by the user within
the configuration file (via injection).

.. _stevedore: http://docs.openstack.org/developer/stevedore/patterns_loading.html


API
===

Loadable driver interface
-------------------------

.. automodule:: watcher_metering.load.loadable

.. autoclass:: Loadable
    :members:

External opts config container
------------------------------

.. automodule:: watcher_metering.load.loadable

.. autoclass:: ExternalOptConfig
    :members:


Available stores
----------------

.. store-doc::
