<p align="center">
  <picture>
    <source srcset="res/bigdata-by-ravenpack-logo-dark.png" media="(prefers-color-scheme: dark)">
    <img src="res/bigdata-by-ravenpack-logo.png" alt="Bigdata Logo" width="300">
  </picture>
</p>

# Bigdata Research Tools

[![Python version support](https://img.shields.io/badge/Python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue?logo=python)](https://pypi.org/project/bigdata-research-tools)
[![PyPI version](https://badge.fury.io/py/bigdata-research-tools.svg)](https://badge.fury.io/py/bigdata-research-tools)

**Bigdata.com API High-Efficiency Tools at Scale**

This repository provides efficient toolset to use the Bigdata.com SDK.

---

## Installation

Install the package from PyPI using `pip`:

```bash
pip install bigdata-research-tools
```

---

## Key Features

- **Rate Limiting**: Enforces a configurable query-per-minute (RPM) limit using
  a token bucket algorithm.
- **Concurrency Support**: Executes multiple search queries simultaneously with
  a user-defined maximum number of threads.
- **Thread-Safe**: Ensures safe concurrent access to shared resources with
  built-in thread locks.
- **Flexible Configuration**:
    - Set custom RPM limits and token bucket sizes.
    - Configure search parameters such as date ranges, sorting, and result
      limits.
- **Minimum Dependencies**: Requires only the `bigdata_client` SDK.
- **Ease of Use**: Includes a convenience function for running multiple
  searches with minimal setup.

---

**RavenPack** | **Bigdata.com** \
All rights reserved © 2025

