Given a YAML files with Kubernetes Custom Resource Definitions (CRDs),
extract the embedded OpenAPI v3 schema and write it to JSON files.

The files are named as expected by Kubeval_.
Existing files won't be overwritten.

Usage
=====

::

    crd2jsonschema crd.yaml --output-directory=schemas/
    kubeval my-resource.yaml --directories=schemas/

Development
===========

You'll need Poetry_ installed.
::

    poetry install --develop=crd2jsonschema
    poetry run pytest


.. _Poetry: https://poetry.eustace.io/docs/#installation
.. _Kubeval: https://kubeval.instrumenta.dev
