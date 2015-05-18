from ..models import GameDepPage, Architectures, OperatingSystems
from pyracms.models import DBSession
from pyracms.lib.filelib import FileLib
from .dicttoxml import dicttoxml
import json

class OutputLib():
    """
    A library to serialise data from database
    """
    def __init__(self, request):
        self.uploadurl = '%s/static/%s/' % (request.host_url, 
                                            FileLib(request).UPLOAD_DIR)

    def show_xml(self):
        """
        Serialize gamedep into xml
        """
        return dicttoxml(json.loads(self.show_json()), 
                         custom_root="hypernucleus", attr_type=False)
    
    def show_json(self):
        """
        Serialise gamedep into json
        """
        root = {"operatingsystems": [], 
                "architectures": [],
                "gamedep": []}
        key = None
        gametype = "game"
        deptype = "dep"
        game = DBSession.query(GameDepPage).filter_by(
                        gamedeptype=gametype, deleted=False).all()
        dep = DBSession.query(GameDepPage).filter_by(
                        gamedeptype=deptype, deleted=False).all()
        oslist = DBSession.query(OperatingSystems)
        archlist = DBSession.query(Architectures)
        for os in oslist:
            osdict = {}
            osdict["name"] = os.name
            osdict["display_name"] = os.display_name
            root["operatingsystems"].append(osdict)
        for arch in archlist:
            archdict = {}
            archdict["name"] = arch.name
            archdict["display_name"] = arch.display_name
            root["architectures"].append(archdict)
        for gamedep in [game, dep]:
            if gamedep == game:
                key = "game"
            else:
                key = "dependency"
            for item in gamedep:
                if item.revisions.count() == 0:
                    continue
                gamedepdict = {}
                gamedepdict["name"] = item.name
                gamedepdict["display_name"] = item.display_name
                gamedepdict["description"] = item.description
                gamedepdict["created"] = str(item.created)
                gamedepdict["dependencies"] = []
                for loopdep in item.dependencies:
                    depdict = {}
                    if loopdep.page.revisions.count() == 0:
                        continue
                    depdict['dependency'] = loopdep.page.name
                    if loopdep:
                        depdict['version'] = str(loopdep.version)
                    else:
                        depdict['version'] = str(loopdep.page.\
                                                 revisions[0].version)
                    gamedepdict["dependencies"].append(depdict)
                gamedepdict["tags"] = []
                for looptag in item.tags:
                    gamedepdict["tags"].append(looptag.name)
                gamedepdict["revisions"] = []
                for looprev in item.revisions:
                    if looprev.published:
                        revdict = {}
                        revdict["version"] = str(looprev.version)
                        revdict["created"] = str(looprev.created)
                        revdict["moduletype"] = looprev.moduletype
                        if gamedep == game:
                            revdict["source"]=  self.uploadurl + \
                                                looprev.file_obj.uuid \
                                                + "/" + looprev.file_obj.name
                        revdict["binaries"] = []
                        for loopbin in looprev.binary:
                            bindict = {}
                            bindict["binary"] = self.uploadurl + \
                                                loopbin.file_obj.uuid \
                                                + "/" + loopbin.file_obj.name
                            bindict["operating_system"] = \
                                            loopbin.operatingsystem_obj.name
                            bindict["architecture"] = \
                                            loopbin.architecture_obj.name
                            revdict["binaries"].append(bindict)
                        gamedepdict["revisions"].append(revdict)
                root["gamedep"].append({key: gamedepdict})
        return json.dumps(root, sort_keys=True, indent=4)
