# Jabber Auto Update Server API

This API is used to manage installers and configuration files for a Jabber Auto Update server.

The following environmental variables are used:

* ```BASE_DIR``` - Base direcory for installer, metadata, and xml files.
* ```BASE_URL``` - Base URL for installer and xml files.
* ```OPENAPI_URL``` - Leave blank to disable FastAPI Docs urls.
* ```ROOT_PATH``` - Passed to FastAPI for Docs urls.
* ```TOKEN``` - Authorization token to interact with API

The following API endpoints are available:

* ```/clients``` (GET) - List available Jabber Update packages
* ```/newclient``` (POST) - Upload a new Jabber Update package
* ```/xml``` (GET/POST) - List/Create jabber-config XML files
* ```/xml/:filename:``` (DELETE/GET/PUT) - Delete/Get/Update details of XML file


# Development Notes

This project uses [poetry](https://python-poetry.org/) to manage python dependencies.  In order to support
using ```.env``` files install the [poetry-dotenv-plugin](https://github.com/mpeteuil/poetry-dotenv-plugin) as well.

To get started:
```shell
git clone https://github.com/ciscomonkey/jas-api .
poetry install
```

Populate a ```.env``` file with the environment variables listed above, then:

```shell
poetry run uvicorn app.main:app --reload --host localhost --port 8000
```

API Documentation will be available at ```http://localhost:8000/docs```

# Docker Notes

When running the API as a docker image, set the ```BASE_URL``` to the volume mount point on your filesystem.  
In this example we're mapping ```./jabber/``` to ```/jabber``` in the container.  
```shell
docker run -it -d -p 8000:8000 --env-file .env --name jas -v ${PWD}/jabber:/jabber ghcr.io/ciscomonkey/jas-api
```

The directory you use for the mountpoint should have 3 directories in it:

```shell
jabber
├── .meta
├── installers
└── xml
```

The installers and xml directories should be served up by the web server.

Building Docker image:

```shell
docker build --tag jas .
```
