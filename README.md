# Jabber Auto Update Server API

This API is used to manage installers and configuration files for a Jabber Auto Update server.

The following environmental variables are used:

* ```BASE_URL``` - Base URL for installer and xml files.
* ```BASE_DIR``` - Base direcory for installer, metadata, and xml files.
* ```TOKEN``` - Authorization token to interact with API
* ```DOCS``` - Enable FastAPI Docs urls.

The following API endpoints are available:

* ```/clients``` (GET) - List available Jabber Update packages
* ```/newclient``` (POST) - Upload a new Jabber Update package
* ```/xml``` (GET/POST) - List/Create jabber-config XML files
* ```/xml/:filename:``` (DELETE/GET/PUT) - Delete/Get/Update details of XML file


# Development Notes

When running the API as a docker image, set the ```BASE_URL``` to the volume mount point on your filesystem.  
In this example we're mapping ```./jabber/``` to ```/jabber``` in the container.  
```shell
docker run -it -d -p 8000:8000 --enf-file .env --name jas -v ${PWD}/jabber:/jabber ghcr.io/ciscomonkey/jas-api
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