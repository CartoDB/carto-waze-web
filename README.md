# Waze Cloud Data Processor (web)

*Upload Waze data from [Waze CCP Processor](https://github.com/LouisvilleMetro/WazeCCPProcessor) to CARTO using a web interface*

## Installation

Clone the repo and install its dependencies with:

```
$ pip install -r requirements
```

Use Flask development web server to start the connector locally:

```
$ env FLASK_ENV=development flask run
```

Or use your favorite production setup to spin up a proper production instance.

## Demo site

The connector can be used live at https://waze-connector.carto.solutions/. This service is provided by CARTO without any kind of Service Level Agreement, and should not be considered production-ready. We also reserve the right to shut it down without prior notice. Please contact sales@carto.com if you need a fully supported and commercially viable solution.
