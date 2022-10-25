# Jabber Auto Update Server API

This API is used to manage installers and configuration files for a Jabber Auto Update server.

The following environmental variables are used:

* ```JAS_BASE_URL``` - Base URL for installer and xml files.
* ```JAS_BASE_DIR``` - Base direcory for installer, metadata, and xml files.
* ```JAS_API_TOKEN``` - Authorization token to interact with API
* ```JAS_DOCS``` - Enable FastAPI Docs urls.

The following API endpoints are available:

* ```/clients``` (GET) - List available Jabber Update packages
* ```/newclient``` (POST) - Upload a new Jabber Update package
* ```/xml``` (GET/POST) - List/Create jabber-config XML files
* ```/xml/:filename:``` (DELETE/GET/PUT) - Delete/Get/Update details of XML file

# Development Notes
