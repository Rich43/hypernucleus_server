from ..models import GameDepPage, Architectures, OperatingSystems
from pyracms.models import DBSession
from pyracms.lib.filelib import FileLib
from xml.etree.ElementTree import Element, SubElement, tostring
import json

class OutputLib():
    """
    A library to serialise data from database
    """
    def __init__(self, request):
        self.uploadurl = '%s/static/%s/' % (request.host_url, FileLib(request).UPLOAD_DIR)

    def show_xml(self):
        """
        Serialize gamedep into xml
        """
        root = Element("hypernucleus")
        gametype = "game"
        deptype = "dep"
        game = DBSession.query(GameDepPage).filter_by(
                        gamedeptype=gametype, deleted=False).all()
        dep = DBSession.query(GameDepPage).filter_by(
                        gamedeptype=deptype, deleted=False).all()
        oslist = DBSession.query(OperatingSystems)
        archlist = DBSession.query(Architectures)
        for os in oslist:
            xmlos = SubElement(root, "operatingsystem")
            SubElement(xmlos, "name").text = os.name
            SubElement(xmlos, "display_name").text = os.display_name
        for arch in archlist:
            xmlarch = SubElement(root, "architecture")
            SubElement(xmlarch, "name").text = arch.name
            SubElement(xmlarch, "display_name").text = arch.display_name
        for gamedep in [game, dep]:
            for item in gamedep:
                if item.revisions.count() == 0:
                    continue
                if gamedep == game:
                    xmlgamedep = SubElement(root, "game")
                else:
                    xmlgamedep = SubElement(root, "dependency")
                SubElement(xmlgamedep, "name").text = item.name
                SubElement(xmlgamedep, "display_name"
                                                ).text = item.display_name
                SubElement(xmlgamedep, "description").text = item.description
                SubElement(xmlgamedep, "created").text = str(item.created)
                for loopdep in item.dependencies:
                    xmldep = SubElement(xmlgamedep, "dependency")
                    if loopdep.page_obj.revisions.count() == 0:
                        continue
                    SubElement(xmldep, "name").text = loopdep.page_obj.name
                    if loopdep.rev_obj:
                        SubElement(xmldep, "version").text = \
                                    str(loopdep.rev_obj.version)
                    else:
                        SubElement(xmldep, "version").text = \
                                    str(loopdep.page_obj.revisions[0].version)
                for looptag in item.tags:
                    SubElement(xmlgamedep, "tag").text = looptag.name
                for looprev in item.revisions:
                    if looprev.published:
                        xmlrev = SubElement(xmlgamedep, "revision")
                        SubElement(xmlrev, "version"
                                                ).text = str(looprev.version)
                        SubElement(xmlrev, "created"
                                                ).text = str(looprev.created)
                        SubElement(xmlrev, "moduletype"
                                            ).text = looprev.moduletype
                        if gamedep == game:
                            SubElement(xmlrev, "source"
                                       ).text = self.uploadurl + \
                                                looprev.file_obj.uuid \
                                                + "/" + looprev.file_obj.name
                        for loopbin in looprev.binary:
                            xmlbin = SubElement(xmlrev, "binary")
                            SubElement(xmlbin, "binary"
                                       ).text = self.uploadurl + \
                                                loopbin.file_obj.uuid \
                                                + "/" + loopbin.file_obj.name
                            SubElement(xmlbin, "operating_system"
                                    ).text = loopbin.operatingsystem_obj.name
                            SubElement(xmlbin, "architecture"
                                    ).text = loopbin.architecture_obj.name
        return tostring(root)
    
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
                    if loopdep.page_obj.revisions.count() == 0:
                        continue
                    depdict['dependency'] = loopdep.page_obj.name
                    if loopdep.rev_obj:
                        depdict['version'] = str(loopdep.rev_obj.version)
                    else:
                        depdict['version'] = str(loopdep.page_obj.\
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
