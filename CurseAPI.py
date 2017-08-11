import requests
import os
import shelve

from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urlparse
from zipfile import ZipFile
from json import loads
from pathlib import Path
from urllib.parse import unquote
from sys import stdout
from MultiMC import InstanceCfg, ForgePatch
from shutil import move, copytree, rmtree

useUserAgent = "Mozilla/5.0 (Windows NT 10.0; rv:50.0) Gecko/20100101 Firefox/50.0"


class CurseAPI:
    search_types = {
        "mod": "mc-mods",
        "modpack": "modpacks",
        "texturepack": "customization"
    }

    """Curse API"""
    def __init__(self):
        self.baseUrl = "https://mods.curse.com"
        self.forgeUrl = "https://minecraft.curseforge.com"

        # Set User Agent header for extra sneakyness
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": useUserAgent})

        # TODO: Find the MultiMC folder automatically
        self.baseDir = ""
        for dirf in ["~/.local/share/multimc", "~/.local/share/multimc5"]:
            edir = os.path.expanduser(dirf)
            if os.path.exists(edir):
                self.baseDir = edir
                break

        self.db = shelve.open(self.baseDir+"/omm.db")

        if "packs" not in self.db:
            self.db["packs"] = list()

        self.packs = self.db["packs"]


    # SECTION MODS

    def get_mod_list(self, version="", page=0):
        """Get an array of `CurseProject`s"""
        parsed = self.get(params={
            "filter-project-game-version": version,
            "page": page
        }, path="/mc-mods/minecraft")
        projects = parsed.select("#addons-browse")[0].select("ul > li > ul")
        return [CurseProject(i) for i in projects]

    def get_files(self, pid: str):
        """Get an array of `CurseFile`s from a project ID"""
        parsed = self.get(path="/projects/{}/files".format(pid), host=self.forgeUrl, includeUrl=True)
        files = parsed[0].select(".project-file-list-item")
        return [CurseFile(i, parsed[1]) for i in files]

    def get_version_list(self):
        """Get all versions available on Curse"""
        parsed = self.get(path="/mc-mods/minecraft")
        options = parsed.select("#filter-project-game-version > option")
        return [i["value"] for i in options if i["value"] != ""]

    def search(self, query: str, stype="mc-mods"):
        parsed = self.get(params={
            "game-slug": "minecraft",
            "search": query
        }, path="/search")
        results = parsed.select("tr.minecraft")
        results = [SearchResult(i) for i in results]
        return [i for i in results if i.type == stype]

    # END SECTION

    # SECTION MODPACKS

    def get_modpacks(self, version="", page=0):
        parsed = self.get(params={
            "filter-project-game-version": version,
            "page": page
        }, path="/modpacks/minecraft")
        projects = parsed.select("#addons-browse")[0].select("ul > li > ul")
        return [CurseProject(i) for i in projects]

    # END SECTION

    # SECTION UTILS

    def download_file(self, url: str, filepath: str):
        """Download a file from `url` to `filepath/name`"""
        r = self.session.get(url, stream=True)
        fname = unquote(Path(r.url).name)
        with open(filepath+"/"+fname, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return filepath+"/"+fname

    def get(self, params={}, path="", host="", includeUrl=False):
        """HTTP GET with HTML parsing"""
        if not host:
            host = self.baseUrl
        r = self.session.get(host + path, params=params)
        html = r.text
        if includeUrl:
            return [BeautifulSoup(html, "html.parser"), r.url]
        return BeautifulSoup(html, "html.parser")

    # END SECTION


class CurseProject:
    """Class for getting project information"""
    def __init__(self, element: Tag):
        self.el = element

        self.title = self.get_content("h4 > a")
        self.id = self.el.select("h4 > a")[0]["href"].split("/")[-1].split("-")[0]

        self.updated = self.get_content(".updated")[8:]
        self.created = self.get_content(".updated", 1)[8:]

        self.monthly = int(self.get_content(".average-downloads")[:-8].replace(',', ''))
        self.total = int(self.get_content(".download-total")[:-6].replace(',', ''))

        self.likes = int(self.get_content(".grats")[:-6].replace(',', ''))

        self.latestVersion = self.get_content(".version")[10:]

        self.imgUrl = self.get_tag(".content-image > img", "src")

    def get_tag(self, selector, tag, index=0):
        return self.el.select(selector)[index][tag]

    def get_content(self, selector, index=0):
        return self.el.select(selector)[index].contents[0]


class SearchResult:
    def __init__(self, element: Tag):
        self.el = element

        self.name = self.get_content("dt > a")
        self.author = self.get_content("a", 1)

        self.url = self.get_tag("dt > a", "href")
        self.type = self.url.split("/")[1]

    def get_tag(self, selector, tag, index=0):
        return self.el.select(selector)[index][tag]

    def get_content(self, selector, index=0):
        return self.el.select(selector)[index].contents[0]


class CurseFile:
    """Class for getting information from a file element"""
    def __init__(self, element: Tag, baseUrl: str):
        self.el = element

        # FTB Official Packs redirect to a different domain
        dat = urlparse(baseUrl)
        self.host = dat.scheme + "://" + dat.netloc

        self.name = self.get_content(".project-file-name-container > a")

        self.releaseType = self.get_tag(".project-file-release-type > div", "title")
        self.uploaded = self.get_content(".standard-datetime")

        self.url = self.get_tag(".project-file-name-container > a", "href")+"/download"
        self.size = float(self.get_content(".project-file-size")[14:-13])

        self.version = self.get_content(".version-label")

        self.downloads = int(self.get_content(".project-file-downloads")[14:-10].replace(',', ''))

    def get_tag(self, selector, tag, index=0):
        return self.el.select(selector)[index][tag]

    def get_content(self, selector, index=0):
        return self.el.select(selector)[index].contents[0]


class CurseModpack:
    """Get information from a modpack"""
    def __init__(self, project: CurseProject, curse: CurseAPI):
        self.project = project
        self.curse = curse

        self.availableFiles = self.curse.get_files(self.project.id)

        self.installed = False
        self.installLocation = "{}/instances/{}/".format(self.curse.baseDir, self.project.title)

    def install(self, file: CurseFile):
        tempPath = "{}/instances/_MMC_TEMP/{}".format(self.curse.baseDir, self.project.title)

        if os.path.exists(tempPath) and self.curse.baseDir:
            a = input("FOLDER AT {} ALREADY EXISTS! Delete? [Yes/No]".format(tempPath))
            if a != "Yes":
                print("ABORTING INSTALLATION")
                return
            rmtree(tempPath)

        # Create instance temp folder if doesn't exist
        if not os.path.exists(tempPath):
            os.makedirs(tempPath)

        # TODO: Pretty progress bar
        packFile = self.curse.download_file(file.host+file.url, tempPath)

        # Unpack zip file
        zipf = ZipFile(packFile)
        zipf.extractall("{}/raw".format(tempPath))
        zipf.close()

        # Delete ZIP file
        os.remove(packFile)

        # Parse Manifest
        manifest = ModpackManifest("{}/raw/manifest.json".format(tempPath))

        # Overrides
        mcPath = "{}/minecraft".format(tempPath)
        if os.path.exists("{}/raw/overrides".format(tempPath)):
            copytree("{}/raw/overrides".format(tempPath), mcPath)

        # Make mods folder
        modPath = "{}/mods".format(mcPath)
        if not os.path.exists(modPath):
            os.makedirs(modPath)

        # Make Patches Folder
        patchPath = "{}/patches".format(tempPath)
        if not os.path.exists(patchPath):
            os.makedirs(patchPath)

        # Configure Instance
        instanceCfg = InstanceCfg(manifest.mcVersion, manifest.forgeVersion, self.project.title)
        instanceCfg.write("{}/instance.cfg".format(tempPath))

        # Configure Forge
        forgeCfg = ForgePatch(manifest.mcVersion, manifest.forgeVersion)
        forgeCfg.write(patchPath+"/net.minecraftforge.json")

        for x, mod in enumerate(manifest.mods):
            stdout.write("\rDownloading mod {}/{}".format(x+1, len(manifest.mods)))
            self.curse.download_file("{}/projects/{}/files/{}/download".format(self.curse.forgeUrl, mod[0], mod[1]), modPath)

        newPath = "{}/instances/{}".format(self.curse.baseDir, self.project.title)

        if os.path.exists(newPath) and self.curse.baseDir:
            a = input("FOLDER AT {} ALREADY EXISTS! Delete? [Yes/No]".format(newPath))
            if a != "Yes":
                print("ABORTING INSTALLATION")
                return
            rmtree(newPath)
        move(tempPath, "{}/instances".format(self.curse.baseDir))


class ModpackManifest:
    """Parse a modpack's manifest.json"""
    def __init__(self, filename: str):
        self.filename = filename

        self.json = loads(open(self.filename).read())

        self.mcVersion = self.json["minecraft"]["version"]
        self.forgeVersion = self.json["minecraft"]["modLoaders"][0]["id"].replace("forge-", '')

        self.mods = [[i["projectID"], i["fileID"]] for i in self.json["files"]]