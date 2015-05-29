from ..models import OperatingSystems, Architectures
from pyracms.factory import RootFactory
from pyracms.lib.menulib import MenuLib
from pyracms.lib.userlib import UserLib
from pyracms.models import Base, DBSession, Settings, Menu
from pyramid.paster import get_appsettings, setup_logging
from pyramid.security import Everyone, Allow
from sqlalchemy import engine_from_config
import os
import sys
import transaction

def usage(argv):
    cmd = os.path.basename(argv[0])
    print(('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        u = UserLib()
        admin_user = u.show("admin")
        # Add Operating Systems
        DBSession.add(OperatingSystems("pi", "Platform Independent"))
        DBSession.add(OperatingSystems("win", "Windows"))
        DBSession.add(OperatingSystems("mac", "Mac OS X"))
        DBSession.add(OperatingSystems("lin", "Linux"))
        DBSession.add(OperatingSystems("sol", "Solaris"))
        DBSession.add(OperatingSystems("fbsd", "FreeBSD"))
        DBSession.add(OperatingSystems("nbsd", "NetBSD"))
        DBSession.add(OperatingSystems("obsd", "OpenBSD"))
        
        # Add Architectures
        DBSession.add(Architectures("pi", "Platform Independent"))
        DBSession.add(Architectures("i386", "32bit X86"))
        DBSession.add(Architectures("x86_64", "64bit X86"))
        DBSession.add(Architectures("arm", "ARM Little Endian"))
        DBSession.add(Architectures("armeb", "ARM Big Endian"))
        DBSession.add(Architectures("ppc", "32bit PowerPC"))
        DBSession.add(Architectures("ppc64", "64bit PowerPC"))
        DBSession.add(Architectures("sparc", "32bit SPARC"))
        DBSession.add(Architectures("sparc64", "64bit SPARC"))
    
        # Default Groups
        u.create_group("gamedep", "Ability to Add, Edit and Delete" +
                       " games and dependencies.", [admin_user])
        
        # Default ACL
        acl = RootFactory()
        acl.__acl__.append((Allow, Everyone, 'gamedep_view'))
        acl.__acl__.append((Allow, Everyone, 'gamedep_list'))
        acl.__acl__.append((Allow, "group:gamedep", "group:gamedep"))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_view'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_list'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_publish'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_edit'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_delete'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_add_picture'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_delete_picture'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_add_source'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_add_binary'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_edit_binary'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_delete_binary'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_add_dependency'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_delete_dependency'))
        acl.__acl__.append((Allow, "group:gamedep", 'gamedep_edit_revision'))
        
        def add_dict(d):
            for k, v in d.items():
                if not v:
                    DBSession.add(Settings(k))
                else:
                    DBSession.add(Settings(k, v))
        
        d = {"INFO_PIC_ADDED": "Your picture (%s) has been added.",
             "INFO_PIC_DELETED": "Your picture (%s) has been deleted.",
             "INFO_BINARY_ADDED": "Your binary (%s) has been added.",
             "INFO_BINARY_UPDATED": "Your binary (%s) has been updated.",
             "INFO_BINARY_DELETED": "Your binary (%s) has been deleted.",
             "INFO_SOURCE_UPLOADED": 
             "The source code (%s) has been successfully uploaded.",
             "INFO_DEPENDENCY_ADDED": "Your dependency (%s) has been added.",
             "INFO_DEPENDENCY_DELETED": "Your dependency (%s) has been deleted.",
             "INFO_REVISION_UPDATED": 
             "A new version (%s) has been updated for %s.",
             "INFO_REVISION_CREATED": 
             "A new version (%s) has been created for %s.",
             "ERROR_INVALID_BINARY_ID": "Invalid Binary ID and/or Edit Type.",
             "HYPERNUCLEUS_SERVER":""}
        add_dict(d)
        
        m = MenuLib()
        group = m.show_group("main_menu")
        DBSession.add(Menu("Games", "/gamedep/game/list", 3, group, Everyone))
        DBSession.add(Menu("Dependencies", "/gamedep/dep/list", 4, 
                         group, Everyone))