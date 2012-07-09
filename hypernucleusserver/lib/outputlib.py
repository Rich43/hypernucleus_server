from ..models import GameDepPage, GameDepType, Architectures, OperatingSystems
from pyracms.models import Files, DBSession
from sqlalchemy.orm.exc import NoResultFound
from xml.etree.ElementTree import Element, SubElement, tostring
import json

class FileNotFound(Exception):
    pass

class FileIterable(object):
    def __init__(self, file_id):
        olib = OutputLib()
        db_file = olib.show_file(file_id)
        self.filename = db_file.name
        self.file_id = file_id
    def __iter__(self):
        return FileIterator(self.file_id)
    
class FileIterator(object):
    def __init__(self, file_id):
        olib = OutputLib()
        self.fileobj = olib.show_file(file_id)
        self.filename = self.fileobj.name
        self.row_id = 0
    def __iter__(self):
        return self
    def next(self):
        try:
            chunk = self.fileobj.data[self.row_id]
        except IndexError:
            raise StopIteration
        self.row_id += 1
        return chunk.data

class OutputLib():
    """
    A library to serialise data from database
    """
    uploadurl = "http://127.0.0.1:6543/outputs/file/"
    
    def show_file(self, file_id):
        """
        Get file object from file id.
        """
        file_id = int(file_id)
        try:
            files = DBSession.query(Files).filter_by(id=file_id).one()
        except NoResultFound:
            raise FileNotFound
        return files
    
    def show_xml(self):
        """
        Serialize gamedep into xml
        """
        root = Element("hypernucleus")
        gametype = DBSession.query(GameDepType).filter_by(name="game").one()
        deptype = DBSession.query(GameDepType).filter_by(name="dep").one()
        game = DBSession.query(GameDepPage).filter_by(
                        gamedeptype_id=gametype.id, deleted=False).all()
        dep = DBSession.query(GameDepPage).filter_by(
                        gamedeptype_id=deptype.id, deleted=False).all()
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
                if not item.revisions.count():
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
                for looppic in item.picture:
                    SubElement(xmlgamedep, "picture"
                                    ).text = self.uploadurl + str(looppic.id)
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
                                            ).text = looprev.moduletype.name
                        if gamedep == game:
                            SubElement(xmlrev, "source"
                                            ).text = self.uploadurl + str(
                                                        looprev.file_obj.id)
                        for loopbin in looprev.binary:
                            xmlbin = SubElement(xmlrev, "binary")
                            SubElement(xmlbin, "binary"
                                            ).text = self.uploadurl + str(
                                                        loopbin.file_obj.id)
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
        gametype = DBSession.query(GameDepType).filter_by(name="game").one()
        deptype = DBSession.query(GameDepType).filter_by(name="dep").one()
        game = DBSession.query(GameDepPage).filter_by(
                        gamedeptype_id=gametype.id, deleted=False).all()
        dep = DBSession.query(GameDepPage).filter_by(
                        gamedeptype_id=deptype.id, deleted=False).all()
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
                if not item.revisions.count():
                    continue
                gamedepdict = {}
                gamedepdict["name"] = item.name
                gamedepdict["display_name"] = item.display_name
                gamedepdict["description"] = item.description
                gamedepdict["created"] = str(item.created)
                gamedepdict["pictures"] = []
                for looppic in item.picture:
                    gamedepdict["pictures"].append(
                                        self.uploadurl + str(looppic.id))
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
                        revdict["moduletype"] = looprev.moduletype.name
                        if gamedep == game:
                            revdict["source"]= self.uploadurl + str(
                                                        looprev.file_obj.id)
                        revdict["binaries"] = []
                        for loopbin in looprev.binary:
                            bindict = {}
                            bindict["binary"] = self.uploadurl + str(
                                                        loopbin.file_obj.id)
                            bindict["operating_system"] = \
                                            loopbin.operatingsystem_obj.name
                            bindict["architecture"] = \
                                            loopbin.architecture_obj.name
                            revdict["binaries"].append(bindict)
                        gamedepdict["revisions"].append(revdict)
                root["gamedep"].append({key: gamedepdict})
        return json.dumps(root, sort_keys=True, indent=4)