from bottle import get, view, run, abort, static_file, redirect, request
from CurseAPI import CurseAPI, CurseProject, CurseModpack, SearchType
from MultiMC import MultiMC
from threading import Thread
from easygui import ynbox

curse = CurseAPI()

mmc = MultiMC(curse.baseDir)


def packdlThread(pack: CurseModpack):
    global mmc
    file = curse.get_files(pack.project.id)[0]
    pack.install(file)
    mmc.metaDb.close()
    mmc = MultiMC(curse.baseDir)
    print("Installed Pack!")


@get("/static/:filename")
def serve_static(filename):
    return static_file(filename, root="static")


@get("/")
@view("index")
def index():
    return {"name": "OpenMineMods", "version": CurseAPI.version, "packs": mmc.instances, "q": request.query}


@get("/edit/<uuid>")
@view("edit")
def edit(uuid):
    if uuid not in mmc.instanceMap:
        abort(404, "Instance Not Found")
    return {"version": CurseAPI.version, "instance": mmc.instanceMap[uuid], "q": request.query}


@get("/edit/<uuid>/browse-mods")
@view("modbrowse")
def modbrowse(uuid):
    if uuid not in mmc.instanceMap:
        abort(404, "Instance Not Found")
    instance = mmc.instanceMap[uuid]
    if "q" in request.query:
        mods = curse.search(request.query["q"])
    else:
        mods = curse.get_mod_list(instance.version)
    return {"version": CurseAPI.version, "instance": mmc.instanceMap[uuid], "mods": mods}


@get("/browse-packs")
@view("packbrowse")
def modbrowse():
    if "q" in request.query:
        packs = curse.search(request.query["q"], SearchType.Modpack)
    else:
        packs = curse.get_modpacks()
    return {"version": CurseAPI.version, "packs": packs}


@get("/install/<packid>")
def installpack(packid):
    project = CurseProject(curse.get(path="/projects/{}".format(packid), host=curse.forgeUrl), detailed=True)
    pack = CurseModpack(project, curse, mmc)
    Thread(target=packdlThread, args=(pack,)).start()
    redirect("/?installing=1")


@get("/uninstall/<uuid>")
def uninstall(uuid):
    if uuid not in mmc.instanceMap:
        abort(404, "Instance Not Found")
    instance = mmc.instanceMap[uuid]
    if not ynbox("Really delete {}?".format(instance.name), "OpenMineMods v"+CurseAPI.version, ('Yes', 'No')):
        abort(401, "Canceled From UI")
    mmc.delete_instance(instance)
    redirect("/?removed=1")


@get("/edit/<uuid>/add/<modid>")
def addmodd(uuid, modid):
    if uuid not in mmc.instanceMap:
        abort(404, "Instance Not Found")
    instance = mmc.instanceMap[uuid]
    files = [i for i in curse.get_files(modid)]
    if len(files) < 1:
        abort(404, "No file for {} found".format(instance.version))
    file = files[0]
    instance.install_mod(file, curse)
    redirect("/edit/{}?installed=1".format(instance.uuid))


@get("/edit/<uuid>/remove/<modid>")
def delmod(uuid, modid):
    if uuid not in mmc.instanceMap:
        abort(404, "Instance Not Found")
    instance = mmc.instanceMap[uuid]
    mod = False
    for imod in instance.mods:
        if imod.name == modid:
            mod = imod
    if not mod:
        abort(404, "Mod not found")
    instance.uninstall_mod(mod.filename)
    redirect("/edit/{}?removed=1".format(instance.uuid))

run(port=8096)