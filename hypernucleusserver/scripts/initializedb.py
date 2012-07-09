from ..models import (OperatingSystems, Architectures, GameDepModuleType, 
    GameDepType)
from pyracms.lib.userlib import UserLib
from pyracms.models import Base, RootFactory, DBSession
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
    
        # Add Module types
        DBSession.add(GameDepModuleType("file",
                            "Python module that is initialised " +
                            "with (for example) foo.py"))
        DBSession.add(GameDepModuleType("folder",
                            "Python module that is initialised " +
                            "with __init__.py"))
    
        # Add the GameDepTypes
        DBSession.add(GameDepType("game"))
        DBSession.add(GameDepType("dep"))
    
        # Default Groups
        u.create_group("gamedep", "Ability to Add, Edit and Delete" +
                       " games and dependencies.", [admin_user])
        
        # Default ACL
        acl = RootFactory()
        acl.__acl__.add((Allow, Everyone, 'gamedep_view'))
        acl.__acl__.add((Allow, Everyone, 'gamedep_list'))
        acl.__acl__.add((Allow, "group:gamedep", "group:gamedep"))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_view'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_list'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_publish'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_edit'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_delete'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_add_picture'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_delete_picture'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_add_source'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_add_binary'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_edit_binary'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_delete_binary'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_add_dependency'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_delete_dependency'))
        acl.__acl__.add((Allow, "group:gamedep", 'gamedep_edit_revision'))
        acl.sync_to_database()