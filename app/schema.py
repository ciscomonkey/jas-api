from pydantic import BaseModel

tags_metadata = [
    {"name": "Clients", "description": "Manage Jabber upgrade packages"},
    {"name": "XML", "description": "Manage autoupdate XML files."},
]


class JabberClient(BaseModel):
    build: str
    downloadURL: str = None
    name: str
    message: str = None
    platform: str
    version: str


class JabberXML(BaseModel):
    name: str
    mac: JabberClient
    win: JabberClient
