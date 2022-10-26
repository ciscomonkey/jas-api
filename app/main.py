"""
Jabber Auto Update Server API
"""

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from lxml import etree
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import os
import re
import shutil
import yaml
import zipfile


load_dotenv()

BASE_DIR = os.getenv("BASE_DIR")
BASE_URL = os.getenv("BASE_URL")
TOKEN = os.getenv("TOKEN")
DOCS = os.getenv("DOCS")
ROOT_PATH = os.getenv("ROOT_PATH", None)

if DOCS:
    docs_url = "/docs"
    redoc_url = "/redoc"
else:
    docs_url = None
    redoc_url = None

app = FastAPI(
    title="Jabber Auto Update Server API",
    description="This API is used to manage installers and configuration files for a Jabber Auto Update server.",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    root_path=ROOT_PATH
)


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


async def verify_token(x_api_token: str = Header()):
    if x_api_token != TOKEN:
        raise HTTPException(status_code=401, detail="Missing Auth Token")


def load_meta():
    metadir = Path(BASE_DIR) / ".meta/"
    print(f"{metadir=}")
    mac = {}
    win = {}
    for path in metadir.glob(f"*.yaml"):
        with open(path, "r") as stream:
            data = yaml.safe_load(stream)
        if path.name.startswith("mac"):
            mac[data["LatestVersion"]] = data
        else:
            win[data["LatestVersion"]] = data

    # Sort our dictionaries
    mac = dict(sorted(mac.items(), reverse=True))
    win = dict(sorted(win.items(), reverse=True))

    return {"mac": mac, "win": win}


@app.get("/clients", dependencies=[Depends(verify_token)])
def list_clients(platform: str = None):

    if platform is None:
        platform = ""
    else:
        if platform not in ["mac", "win"]:
            return JSONResponse(
                status_code=400,
                content={"message": "Valid platform options are 'mac' or 'win'"},
            )

    meta = load_meta()

    if platform == "mac":
        return meta["mac"]

    if platform == "win":
        return meta["win"]

    return meta


@app.post("/newclient", dependencies=[Depends(verify_token)])
def add_client(
    downloadURL: Optional[str] = Form(None),
    file: UploadFile = File(...),
    message: str = Form(...),
):
    metadir = Path(BASE_DIR) / ".meta/"
    installerdir = Path(BASE_DIR) / "installers/"
    xmldir = Path(BASE_DIR) / "xml/"
    try:
        if file.filename.startswith("CiscoJabberMac") and file.filename.endswith(
            "-AutoUpdate.zip"
        ):
            version_info = file.filename.split("-")[1]
            version, build = version_info.rsplit(".", 1)
            if downloadURL is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": f"The 'downloadURL' is required when adding Mac clients."
                    },
                )

            newfile = installerdir.joinpath(version_info, downloadURL)
            if not newfile.parent.is_dir():
                os.makedirs(newfile.parent, exist_ok=True)

            if newfile.exists():
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": f"Installer for {version_info} already exists."
                    },
                )

            with open(newfile, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            metafile = metadir / f"mac-{version_info}.yaml"
            url = f"{BASE_URL}/Installers/{version_info}/{newfile.name}"
            meta = {
                "LatestBuildNum": build,
                "LatestVersion": version,
                "DownloadURL": url,
                "Message": message,
            }

        elif file.filename.startswith("CiscoJabber-Install"):
            tmp_filename = Path(f"/tmp/{file.filename}")
            tmp_path = Path(f"/tmp/{'.'.join(file.filename.split('.')[:-1])}")
            with open(tmp_filename, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            with zipfile.ZipFile(tmp_filename, "r") as zip_ref:
                zip_ref.extractall("/tmp")

            readme = open(tmp_path.joinpath("README_install.txt")).read()
            if not readme:
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": f"Could no find README_install.txt in the zip file."
                    },
                )

            version_info = re.search("Build Number ([\d.]+)", readme).group(1)
            version, build = version_info.rsplit(".", 1)

            newfile = installerdir.joinpath(version_info, "CiscoJabberSetup.msi")
            if not newfile.parent.is_dir():
                os.makedirs(newfile.parent, exist_ok=True)
            if newfile.exists():
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": f"Installer for {version_info} already exists."
                    },
                )
            shutil.move(tmp_path.joinpath("CiscoJabberSetup.msi"), newfile)

            metafile = metadir / f"win-{version_info}.yaml"
            url = f"{BASE_URL}/Installers/{version_info}/{newfile.name}"
            meta = {
                "LatestBuildNum": build,
                "LatestVersion": version,
                "DownloadURL": url,
                "Message": message,
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"{file.filename} does not appear to be a Jabber package."
                },
            )

        # File was uploaded now update .meta yaml file
        with open(metafile, "w") as mfile:
            yaml.dump(meta, mfile)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"There was an issue uploading the file: {e}"},
        )

    return {"message": f"Successfully uploaded {file.filename}"}


def getCurrentVersions(filename):
    parser = etree.XMLParser(strip_cdata=False)
    tree = etree.parse(f"{filename}", parser)
    doc = tree.getroot()
    result = {}
    for app in doc:
        name = app.get("name")
        ver = app.findtext("LatestVersion")
        build = app.findtext("LatestBuildNum")
        if name == "JabberMac":
            result["mac"] = f"{ver}.{build}"
        if name == "JabberWin":
            result["win"] = f"{ver}.{build}"
    return result


@app.get("/xml", dependencies=[Depends(verify_token)])
def list_xml(details: bool = True):
    xmldir = Path(BASE_DIR) / "xml/"
    xmls = {}
    for path in xmldir.glob(f"*.xml"):
        xmls[path.name] = getCurrentVersions(path)

    if details:
        return xmls

    return list(xmls.keys())


@app.get("/xml/{filename}", dependencies=[Depends(verify_token)])
def get_xml(filename):
    filename = Path(BASE_DIR) / "xml/" / filename
    if not filename.exists():
        raise Exception(f"{filename} was not found")
    data = getCurrentVersions(filename)
    return data


def get_client_meta_data(platform: str, version: str):
    metafile = Path(BASE_DIR) / f".meta/{platform}-{version}.yaml"
    if not metafile.exists():
        return False
    with open(metafile, "r") as stream:
        data = yaml.safe_load(stream)
    return data


@app.post("/xml", dependencies=[Depends(verify_token)])
def add_xml(filename: str = Form(...), mac: str = Form(...), win: str = Form(...)):
    xmldir = Path(BASE_DIR) / "xml/"
    newfile = xmldir / filename
    if newfile.exists():
        return JSONResponse(
            status_code=400,
            content={"message": f"{filename} already exists."},
        )

    macdata = get_client_meta_data("mac", mac)
    if not macdata:
        return JSONResponse(
            status_code=400, content={"message", f"{mac} is not a valid version"}
        )

    windata = get_client_meta_data("win", win)
    if not windata:
        return JSONResponse(
            status_code=400, content={"message", f"{win} is not a valid version"}
        )

    template = f"""<?xml version='1.0' encoding='utf-8'?>
<JabberUpdate><App name="JabberMac">
     <LatestBuildNum>{macdata['LatestBuildNum']}</LatestBuildNum>
     <LatestVersion>{macdata['LatestVersion']}</LatestVersion>
     <Message><![CDATA[{macdata['Message']}]]></Message>
     <DownloadURL>{macdata['DownloadURL']}</DownloadURL>
  </App>
  <App name="JabberWin">
     <LatestBuildNum>{windata['LatestBuildNum']}</LatestBuildNum>
     <LatestVersion>{windata['LatestVersion']}</LatestVersion>
     <Message><![CDATA[{windata['Message']}]]></Message>
     <DownloadURL>{windata['DownloadURL']}</DownloadURL>
  </App>
</JabberUpdate>"""

    with open(newfile, "w") as stream:
        stream.write(template)

    return {"message": f"Created {filename}."}


@app.put("/xml/{filename}", dependencies=[Depends(verify_token)])
def update_xml(
    filename: str,
    mac: Optional[str] = Form(None),
    win: Optional[str] = Form(None),
):
    if mac is None and win is None:
        return JSONResponse(
            status_code=400,
            content={
                "message": f"You must specify at least one platform version to update"
            },
        )

    if mac is not None:
        macdata = get_client_meta_data("mac", mac)
    if win is not None:
        windata = get_client_meta_data("win", win)

    fname = Path(BASE_DIR) / f"xml/{filename}"
    parser = etree.XMLParser(strip_cdata=False)
    tree = etree.parse(f"{fname}", parser)

    root = tree.getroot()
    for elem in root.iter("App"):
        if mac and elem.get("name") == "JabberMac":
            for key in list(macdata.keys()):
                if key == "Message":
                    elem.find(key).text = etree.CDATA(macdata[key])
                else:
                    elem.find(key).text = macdata[key]

        if win and elem.get("name") == "JabberWin":
            for key in list(windata.keys()):
                if key == "Message":
                    elem.find(key).text = etree.CDATA(windata[key])
                else:
                    elem.find(key).text = windata[key]

    tree.write(f"{fname}", encoding="utf-8", xml_declaration=True)
    return {"message": f"Updated {filename}"}


@app.delete("/xml/{filename}", dependencies=[Depends(verify_token)])
def delete_xml(filename: str):
    xmlfile = Path(BASE_DIR) / f"xml/{filename}"
    if not xmlfile.exists():
        return JSONResponse(
            status_code=404,
            content={"message": f"{filename} was not found."},
        )
    xmlfile.unlink(missing_ok=True)
    return {"message": f"Deleted {filename}"}
