# Prometheus Python Client

A fork of official Python client for [Prometheus](https://prometheus.io).

This fork contains a few bugfixes and enhancements that make client usable inside Debian-based Docker containers:
* process stat reader was fixed to use correct /proc/$pid/stat entries
* process stat reader aggregates child process stats in addition to its own
* system-level cpu/mem metrics were added (ie. `*_system_*` infix)

## Installation

```
pip install prometheus-client
```

This package can be found on [PyPI](https://pypi.python.org/pypi/prometheus_client).

## Documentation

Documentation is available on https://prometheus.github.io/client_python

## Links

* [Releases](https://github.com/prometheus/client_python/releases): The releases page shows the history of the project and acts as a changelog.
* [PyPI](https://pypi.python.org/pypi/prometheus_client)
