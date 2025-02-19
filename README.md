<p align="center">
  <picture>
    <source srcset="https://sdk.bigdata.com/en/latest/_static/bigdata_dark.svg" media="(prefers-color-scheme: dark)">
    <img src="https://sdk.bigdata.com/en/latest/_static/bigdata_light.svg" alt="Bigdata Logo" width="250">
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

## Usage

The following example demonstrates the convenient way to run multiple searches
in a concurrent and rate-limited manner:

```python 
from bigdata_research_tools import run_search
from bigdata_client import Bigdata

bigdata = Bigdata()

results = run_search(bigdata=bigdata,
                     queries=YOUR_LIST_OF_QUERIES,
                     limit=1000)
```

## 1. Return Values

### 1.1. Return only the results list

By default, setting `only_results=True` will return a list of all results from
all queries.

```python
results = run_search(bigdata=bigdata,
                     queries=YOUR_LIST_OF_QUERIES,
                     limit=1000,
                     only_results=True)
```

```shell
>>> results
[
    [results1, results2, ...],
    [results1, results2, ...],
    [results1, results2, ...],
]
```

### 1.2. Return queries with their corresponding results

Setting `only_results=False` will return a dictionary mapping each (query,
date_range) combination pair to their respective search results list.

```python
query_results = run_search(bigdata=bigdata,
                           queries=YOUR_LIST_OF_QUERIES,
                           limit=1000,
                           only_results=False)
```

```shell
>>> query_results
{
    '(query1, date_range1)': [results1, results2, ...],
    '(query1, date_range2)': [results1, results2, ...],
    '(query2, date_range1)': [results1, results2, ...],
    '(query2, date_range2)': [results1, results2, ...],
    ...
}
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

## License

This software is licensed for use solely under the terms agreed upon in the
applicable Master Agreement and Order Schedule between the parties.
For trials, the applicable legal documents are the Mutual Non-Disclosure
Agreement, or if applicable the Trial Agreement.
No other rights or licenses are granted by implication, estoppel, or otherwise.
For further details, please refer to your specific Master Agreement and Order
Schedule or contact us at legal@ravenpack.com.

---

**RavenPack** | **Bigdata.com** \
All rights reserved © 2025

