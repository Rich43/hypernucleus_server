from ..models import (GameDepModuleType, OperatingSystems, Architectures, 
    GameDepBinary, GameDepPage, GameDepRevision, GameDepType, GameDepDependency)
from pyracms.lib.filelib import AlchemyIO
from pyracms.lib.taglib import TagLib, GAMEDEP
from pyracms.models import DBSession
from sqlalchemy.orm.exc import NoResultFound

class GameDepNotFound(Exception):
    pass

class ModuleTypeNotFound(Exception):
    pass

class SourceCodeNotFound(Exception):
    pass

class BinaryNotFound(Exception):
    pass

class GameDepFound(Exception):
    pass

class InvalidGameDepType(Exception):
    pass

GAME = "games"
DEP = "dependencies"

class GameDepLib():
    """
    A library to manage the Games and Dependencies database.
    Usage examples:
    from hypernucleusserver.controllerlib.gamedeplib import ArticleLib
    # Make instance of class for Games
    gd = GameDepLib(GAME)
    # or
    # Make instance of class for Dependencies
    gd = GameDepLib(DEP)                 
    gd.list()                            # To list games/deps
    gd.show("Front_Page")                # Get the database row of Front_Page
    gd.exists("NotThere")                # Check to see if page exists
    gd.exists("Front_Page")
    
    # Get user needed for create, update, delete
    from hypernucleusserver.controllerlib.userlib import UserLib
    u = UserLib()                       # Make instance of class
    admin = u.show("admin")             # Get the database row of admin
    
    # methods for create, update, delete
    gd.create("TestPage", 
                "Testing",
                "Creating Testing",
                admin)         # To create page
    gd.update("TestPage", 
                "More test article",
                "Updating Testing",
                admin)         # To update page
    gd.delete("TestPage", 
                admin)         # To delete page
    """
    
    def __init__(self, gamedep_type):
        if not gamedep_type in [GAME, DEP]:
            raise InvalidGameDepType
        self.gamedep_type = gamedep_type
        self.t = TagLib(GAMEDEP)
        
    def get_gamedeptype(self):
        if self.gamedep_type == GAME:
            gamedeptype = DBSession.query(GameDepType).filter_by(
                                                        name="game").one()
        else:
            gamedeptype = DBSession.query(GameDepType).filter_by(
                                                        name="dep").one()
        return gamedeptype
    
    def list(self): #@ReservedAssignment
        """
        List all the pages
        """
        result = set()
        gamedeptype = self.get_gamedeptype()
        gamedeps = DBSession.query(GameDepPage).filter_by(
                                gamedeptype_id=gamedeptype.id, deleted=False)
        if not gamedeps:
            raise GameDepNotFound
        for gamedep in gamedeps:
            result.add(gamedep.name)
        return result
    
    def create(self, name, display_name, description, tags, owner):
        """
        Add a new page
        Raise GameDepFound if page exists
        """
        if not self.exists(name, raise_if_found=True):
            gamedeptype = self.get_gamedeptype()
            page = GameDepPage(gamedeptype, name, display_name, owner)
            page.description = description
            self.t.set_tags(page, tags)
            DBSession.add(page)

    def update(self, name, newname, display_name, description, tags):
        """
        Update a page
        Raise GameDepNotFound if page does not exist
        """
        page = self.show(name)[0]
        page.name = newname
        page.display_name = display_name
        page.description = description
        self.t.set_tags(page, tags)
        
    def flip_published(self, name, revision):
        rev = self.show(name, revision)[1]
        if rev.published == False:
            if self.gamedep_type == GAME and not rev.file_obj:
                raise SourceCodeNotFound
            if self.gamedep_type == DEP and not rev.binary.count():
                raise BinaryNotFound
        rev.published = not(rev.published)
        
    def create_revision(self, name, version, moduletype):
        """
        Add a new revision
        Raise GameDepFound if version exists
        """
        version = float(version)
        moduletype = self.get_moduletype(moduletype)
        if not self.exists(name, version, raise_if_found=True):
            page, rev = self.show(name, no_revision_error=False)
            rev = GameDepRevision(version, moduletype)
            page.revisions.append(rev)

    def create_picture(self, name, picture, mimetype, filename):
        """
        Add a new picture
        """
        page = self.show(name)[0]
        aio = AlchemyIO(fle=picture, sess=DBSession, 
                        mime=mimetype, filename=filename)
        picobj = aio.write()
        page.picture.append(picobj)

    def show_picture(self, page, pic_id):
        """
        Find a picture matching pic_id from page.
        """
        pic_id = int(pic_id)
        picitem = None
        for pagepic in page.picture:
            if pagepic.id == pic_id:
                picitem = pagepic
        if picitem:
            return picitem
        else:
            raise GameDepNotFound

    def delete_picture(self, name, pic_id):
        """
        Delete a picture
        """
        pic_id = int(pic_id)
        page = self.show(name)[0]
        picitem = self.show_picture(page, pic_id)
        page.picture.remove(picitem)
        DBSession.delete(picitem)

    def create_source(self, name, revision, source, mimetype, filename):
        """
        Add a new source code
        """
        rev = self.show(name, revision)[1]
        aio = AlchemyIO(fle=source, sess=DBSession, 
                        mime=mimetype, filename=filename)
        srcobj = aio.write()
        if rev.file_obj:
            DBSession.delete(rev.file_obj)
        rev.file_obj = srcobj

    def show_binary(self, binary_id):
        try:
            bin_obj = DBSession.query(GameDepBinary).filter_by(
                                            id=binary_id).one()
        except NoResultFound:
            raise GameDepNotFound
        return bin_obj
    
    def create_binary(self, name, revision, operatingsystem, architecture, 
                      binary, mimetype, filename):
        """
        Add a new binary
        """
        try:
            os_obj = DBSession.query(OperatingSystems).filter_by(
                                                id=operatingsystem).one()
            arch_obj = DBSession.query(Architectures).filter_by(
                                                id=architecture).one()
        except NoResultFound:
            raise GameDepNotFound
        
        rev = self.show(name, revision)[1]
        aio = AlchemyIO(fle=binary, sess=DBSession, 
                        mime=mimetype, filename=filename)
        aio_obj = aio.write()
        bin_obj = GameDepBinary(aio_obj, os_obj, arch_obj)
        rev.binary.append(bin_obj)

    def update_binary(self, name, revision, binary_id, operatingsystem, 
                      architecture, binary):
        """
        Update a binary
        """
        try:
            if not binary:
                os_obj = DBSession.query(OperatingSystems).filter_by(
                                                    id=operatingsystem).one()
                arch_obj = DBSession.query(Architectures).filter_by(
                                                    id=architecture).one()
        except NoResultFound:
            raise GameDepNotFound
        
        rev = self.show(name, revision)[1]
        bin_obj = None
        for x in rev.binary:
            if x.id == int(binary_id):
                bin_obj = x
                break
        if not bin_obj:
            raise GameDepNotFound
        
        if not binary:
            bin_obj.operatingsystem_obj = os_obj
            bin_obj.architecture_obj = arch_obj
        else:
            aio = AlchemyIO(fle=binary['fp'], sess=DBSession, 
                            mime=binary['mimetype'], 
                            filename=binary['filename'])
            aio_obj = aio.write()
            DBSession.delete(bin_obj.file_obj)
            bin_obj.file_obj = aio_obj

    def delete_binary(self, name, revision, bin_id):
        """
        Delete a binary
        """
        bin_id = int(bin_id)
        rev = self.show(name, revision)[1]
        binitem = None
        for revbin in rev.binary:
            if revbin.id == bin_id:
                binitem = revbin
        if binitem:
            rev.binary.remove(binitem)
            DBSession.delete(binitem)
    
        else:
            raise GameDepNotFound

    def create_dependency(self, name, dep_id, rev_id=None):
        """
        Add a new dependency
        """
        dep_id = int(dep_id)
        gamedeptype = DBSession.query(GameDepType).filter_by(
                                                        name="dep").one()
        try:
            dep = DBSession.query(GameDepPage).filter_by(
                                            gamedeptype_id=gamedeptype.id, 
                                            deleted=False, id=dep_id).one()
            if rev_id:
                rev = DBSession.query(GameDepRevision).filter_by(
                                            id=rev_id).one()
                if not rev in dep.revisions:
                    raise GameDepNotFound
        except NoResultFound:
            raise GameDepNotFound
        
        page = self.show(name)[0]
        for pagedep in page.dependencies:
            if pagedep.page_obj.id == dep.id:
                raise GameDepFound
        
        gdd = GameDepDependency(dep)
        if rev_id:
            gdd.rev_obj = rev
        page.dependencies.append(gdd)

    def show_dependency(self, page, dep_id):
        """
        Find a dependency
        """
        dep_id = int(dep_id)
        found = False
        for item in page.dependencies:
            if dep_id == item.page_obj.id:
                return item
        if not found:
            raise GameDepNotFound
        
    def delete_dependency(self, name, dep_id):
        """
        Delete a dependency
        """
        dep_id = int(dep_id)
        page = self.show(name)[0]
        item = self.show_dependency(page, dep_id)
        page.dependencies.remove(item)
        DBSession.delete(item)

    def update_revision(self, name, revision, version, moduletype):
        """
        Update a revision
        Raise GameDepNotFound if page does not exist
        """
        version = float(version)
        moduletype = self.get_moduletype(moduletype)
        rev = self.show(name, revision)[1]
        rev.version = version
        rev.moduletype = moduletype

    def delete(self, name):
        """
        Delete a page
        Raise GameDepNotFound if page does not exist
        """
        page = self.show(name)[0]
        page.deleted = True

    def exists(self, name, version=None, raise_if_found=False):
        """
        Check to see if a page exists
        Return True/False
        """
        try:
            gamedeptype = self.get_gamedeptype()
            page = DBSession.query(GameDepPage).filter_by(
                                            name=name,
                                            gamedeptype_id=gamedeptype.id, 
                                            deleted=False).one()
        except NoResultFound:
            return False
        
        if version:
            versions = [x.version for x in page.revisions]
            if not version in versions:
                return False
        if raise_if_found:
            raise GameDepFound
        return True

    def deleted(self, name):
        """
        Check to see if page is deleted.
        """
        page = self.show(name)[0]
        return page.deleted
        
    def get_moduletype(self, moduletype):
        """
        Get a Module Type row from database.
        Raise ModuleTypeNotFound if Module Type does not exist.
        """
        try:
            mt = DBSession.query(GameDepModuleType).filter_by(
                                                        name=moduletype).one()
            return mt
        except NoResultFound:
            raise ModuleTypeNotFound
        
    def list_moduletypes(self, with_display_name=True):
        """
        Get a Module Type list from database.
        """
        mt = DBSession.query(GameDepModuleType)
        if with_display_name:
            mtlist = [(x.name, x.display_name) for x in mt]
        else:
            mtlist = [x.name for x in mt]
        return mtlist
    
    def list_operatingsystems(self, with_display_name=True):
        """
        Get a Operating System list from database.
        """
        if with_display_name:
            oslist = DBSession.query(OperatingSystems.id, 
                                    OperatingSystems.display_name).order_by(
                                    OperatingSystems.id).all()
            oslist = [(x[0], x[1]) for x in oslist]
        else:
            oslist = DBSession.query(OperatingSystems.id).order_by(
                                    OperatingSystems.id).all()
            oslist = [x[0] for x in oslist]
        return oslist
    
    def list_architectures(self, with_display_name=True):
        """
        Get a Architecture list from database.
        """
        if with_display_name:
            archlist = DBSession.query(Architectures.id, 
                                    Architectures.display_name).order_by(
                                    Architectures.id).all()
            archlist = [(x[0], x[1]) for x in archlist]
        else:
            archlist = DBSession.query(Architectures.id).order_by(
                                    Architectures.id).all()
            archlist = [x[0] for x in archlist]
        return archlist
    
    def dependency_dropdown(self, with_display_name=True):
        result = []
        gamedeptype = DBSession.query(GameDepType).filter_by(
                                                        name="dep").one()
        page = DBSession.query(GameDepPage).filter_by(
                            deleted=False, gamedeptype_id=gamedeptype.id)
        for x in page:
            if x.revisions.count():
                i = 0
                for revision in x.revisions:
                    if revision.published:
                        i += 1
                if i > 0:
                    if with_display_name:
                        result.append((x.id, "%s (%s)" % (x.display_name, 
                                                          x.name)))
                    else:
                        result.append(x.id)
        return result
    
    def revision_dropdown(self, dep_id, with_display_name=True):
        initial_item = [(-1, "Use Latest Version")]
        if with_display_name:
            rev = DBSession.query(GameDepRevision.id, 
                                   GameDepRevision.version).filter_by(
                                            page_id=dep_id, published=True)
        else:
            rev = DBSession.query(GameDepRevision.id).filter_by(
                                            page_id=dep_id, published=True)
        result = initial_item 
        result.extend(rev.all())
        if with_display_name:
            result = [(x[0], x[1]) for x in result]
        else:
            result = [x[0] for x in result]
        return result
    
    def show(self, name, revision=None, no_revision_error=True):
        """
        Get article of a page or revision
        Raise GameDepNotFound if page does not exist
        """
        if revision:
            revision = int(revision)
        if not name:
            raise GameDepNotFound
        
        if not revision:
            try:
                gamedeptype = self.get_gamedeptype()
                page = DBSession.query(GameDepPage).filter_by(
                                                name=name,
                                                gamedeptype_id=gamedeptype.id, 
                                                deleted=False).one()
            except NoResultFound:
                raise GameDepNotFound("NoResultFound")
            if not page.revisions.count() and no_revision_error:
                raise GameDepNotFound("no_revision_error")
            return (page, page.revisions)
        else:
            try:
                page, rev = self.show(name)
                rev_result = rev.filter_by(id=revision).one()
                return (page, rev_result)
            except NoResultFound:
                raise GameDepNotFound