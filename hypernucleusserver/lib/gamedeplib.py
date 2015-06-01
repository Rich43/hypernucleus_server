from pyracms.lib.filelib import FileLib
from pyracms.lib.settingslib import SettingsLib
from ..models import (OperatingSystems, Architectures, GameDepBinary,
    GameDepPage, GameDepRevision, GameDepTags, GameDepDependency, GameDepVotes)
from pyracms.lib.taglib import TagLib, GAMEDEP
from pyracms.models import DBSession, Files
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import transaction

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

class AlreadyVoted(Exception):
    pass

GAME = "game"
DEP = "dep"

class GameDepLib():
    """
    A library to manage the Games and Dependencies database.
    Usage examples:
    from hypernucleusserver.lib.gamedeplib import GameDepLib
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
        self.t = TagLib(GameDepTags, GAMEDEP)

    def list(self): #@ReservedAssignment
        """
        List all the pages
        """
        result = set()
        gamedeps = DBSession.query(GameDepPage).filter_by(
                                gamedeptype=self.gamedep_type)
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
            page = GameDepPage(self.gamedep_type, name, display_name, owner)
            page.description = description
            self.t.set_tags(page, tags)
            s = SettingsLib()
            if s.has_setting("PYRACMS_FORUM"):
                from pyracms_forum.lib.boardlib import BoardLib
                page.thread_id = BoardLib().add_thread(name, display_name, "",
                                                       owner, add_post=False).id
            if s.has_setting("PYRACMS_GALLERY"):
                from pyracms_gallery.lib.gallerylib import GalleryLib
                album = GalleryLib().create_album(name, display_name, owner)
                page.album_id = album
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
            if self.gamedep_type == DEP and not len(rev.binary):
                raise BinaryNotFound
        rev.published = not(rev.published)

    def create_source(self, name, revision, source, mimetype, 
                      filename, request):
        """
        Add a new source code
        """
        rev = self.show(name, revision)[1]
        file_lib = FileLib(request)
        if rev.file_obj:
            file_lib.delete(rev.file_obj)
        srcobj = file_lib.write(filename, source, mimetype)
        rev.file_obj = srcobj

    def show_binary(self, binary_id):
        try:
            bin_obj = DBSession.query(GameDepBinary).filter_by(
                                            id=binary_id).one()
        except NoResultFound:
            raise GameDepNotFound
        return bin_obj
    
    def create_binary(self, name, revision, operatingsystem, architecture, 
                      binary, mimetype, filename, request):
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
        file_lib = FileLib(request)
        aio_obj = file_lib.write(filename, binary, mimetype)
        bin_obj = GameDepBinary(aio_obj, os_obj, arch_obj)
        rev.binary.append(bin_obj)

    def update_binary(self, name, revision, binary_id, operatingsystem, 
                      architecture, binary, request):
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
            file_lib = FileLib(request)
            old_name = bin_obj.file_obj.name
            old_mimetype = bin_obj.file_obj.mimetype
            aio_obj = file_lib.write(old_name, binary, old_mimetype)
            file_lib.delete(bin_obj.file_obj)
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

    def create_dependency(self, name, dep_id, rev_id):
        """
        Add a new dependency
        """
        dep_id = int(dep_id)
        try:
            dep = DBSession.query(GameDepPage).filter_by(gamedeptype="dep", 
                                                         id=dep_id).one()
            rev = DBSession.query(GameDepRevision).filter_by(
                                        id=rev_id).one()
            if not rev in dep.revisions:
                raise GameDepNotFound
        except NoResultFound:
            raise GameDepNotFound
        
        page = self.show(name)[0]
        for pagedep in page.dependencies:
            if pagedep.page.id == dep.id:
                raise GameDepFound
        page.dependencies.append(rev)

    def show_dependency(self, page, dep_id):
        """
        Find a dependency
        """
        dep_id = int(dep_id)
        found = False
        for item in page.dependencies:
            if dep_id == item.page.id:
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
        
    def create_revision(self, name, version, moduletype):
        """
        Add a new revision
        Raise GameDepFound if version exists
        """
        version = float(version)
        if not self.exists(name, version, raise_if_found=True):
            page, rev = self.show(name, no_revision_error=False)
            rev = GameDepRevision(version, moduletype)
            page.revisions.append(rev)
            
    def update_revision(self, name, revision, version, moduletype):
        """
        Update a revision
        Raise GameDepNotFound if page does not exist
        """
        version = float(version)
        rev = self.show(name, revision)[1]
        rev.version = version
        rev.moduletype = moduletype
    
    def delete_revision(self, name, revision, request):
        """
        Delete a revision
        Raise GameDepNotFound if page does not exist
        """
        f = FileLib(request)
        rev = self.show(name, revision)[1]
        files = set()
        if rev.file_obj:
            files.add(rev.file_obj)
            rev.file_obj = None
        for item in rev.binary:
            files.add(item.file_obj)
            item.file_obj = None
        for item in files:
            f.delete(item)
        DBSession.delete(rev)
        
    def delete(self, name, request):
        """
        Delete a page
        Raise GameDepNotFound if page does not exist
        """
        page = self.show(name)[0]
        for item in page.revisions:
            rev_id = item.id
            self.delete_revision(name, rev_id, request)
        if page.thread_id != -1:
            from pyracms_forum.lib.boardlib import BoardLib
            BoardLib().delete_thread(page.thread_id)
        if page.album_id != -1:
            from pyracms_gallery.lib.gallerylib import GalleryLib
            GalleryLib().delete_album(page.album_id, request)
        DBSession.delete(page)

    def exists(self, name, version=None, raise_if_found=False):
        """
        Check to see if a page exists
        Return True/False
        """
        try:
            page = DBSession.query(GameDepPage).filter_by(
                                            name=name,
                                            gamedeptype=self.gamedep_type
                                            ).one()
        except NoResultFound:
            return False
        
        if version:
            versions = [x.version for x in page.revisions]
            if not version in versions:
                return False
        if raise_if_found:
            raise GameDepFound
        return True
    
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
        page = DBSession.query(GameDepPage).filter_by(gamedeptype="dep")
        for x in page:
            if x.revisions.count():
                i = 0
                for revision in x.revisions:
                    if revision.published:
                        i += 1
                if i > 0:
                    if with_display_name:
                        result.append((str(x.id), 
                                       "%s (%s)" % (x.display_name, 
                                                    x.name)))
                    else:
                        result.append(str(x.id))
        return result
    
    def revision_dropdown(self, dep_id, with_display_name=True):
        initial_item = [("-1", "Use Latest Version")]
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
            result = [(str(x[0]), str(x[1])) for x in result]
        else:
            result = [str(x[0]) for x in result]
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
                page = DBSession.query(GameDepPage).filter_by(
                                                name=name,
                                                gamedeptype=self.gamedep_type
                                                ).one()
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
            
    def add_vote(self, db_obj, user, like):
        """
        Add a vote to the database
        """
        
        vote = GameDepVotes(user, like)
        vote.game = db_obj
        try:
            DBSession.add(vote)
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            raise AlreadyVoted
