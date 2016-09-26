from datetime import datetime
from pyracms.models import Files, User, Base, JsonBase
from sqlalchemy import (Column, Integer, Unicode, DateTime, Boolean, Float, desc, 
    Enum)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey, UniqueConstraint

class GameDepVotes(Base):
    __tablename__ = 'gamedepvotes'
    __table_args__ = (UniqueConstraint('user_id', 'game_id'),
                      {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('gamedeppage.id'))
    game = relationship("GameDepPage")
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)
    like = Column(Boolean, nullable=False, index=True)

    def __init__(self, user, like):
        self.user = user
        self.like = like

class GameDepTags(Base):
    __tablename__ = 'gamedeptags'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, nullable=False)
    game_id = Column(Integer, ForeignKey('gamedeppage.id'))
    game = relationship("GameDepPage")

    def __init__(self, name):
        self.name = name

class OperatingSystems(Base):
    __tablename__ = 'operatingsystems'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(32), index=True, unique=True, nullable=False)
    display_name = Column(Unicode(128), index=True, unique=True,
                                                            nullable=False)
    def __init__(self, name, display_name):
        self.name = name
        self.display_name = display_name
        
class Architectures(Base):
    __tablename__ = 'architectures'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(32), index=True, unique=True, nullable=False)
    display_name = Column(Unicode(128), index=True, unique=True,
                                                            nullable=False)
    def __init__(self, name, display_name):
        self.name = name
        self.display_name = display_name
    
class GameDepBinary(Base):
    __tablename__ = 'gamedepbinary'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    revision_id = Column(Integer, ForeignKey('gamedeprevision.id'),
                         nullable=False)
    operatingsystem_id = Column(Integer, ForeignKey('operatingsystems.id'),
                                nullable=False)
    architecture_id = Column(Integer, ForeignKey('architectures.id'),
                             nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    file_obj = relationship(Files, uselist=False, single_parent=True,
                            cascade="all, delete, delete-orphan")
    operatingsystem_obj = relationship(OperatingSystems, uselist=False)
    architecture_obj = relationship(Architectures, uselist=False)
                            
    def __init__(self, file_obj, operatingsystem_obj, architecture_obj):
        self.file_obj = file_obj
        self.operatingsystem_obj = operatingsystem_obj
        self.architecture_obj = architecture_obj
        
class GameDepRevision(Base, JsonBase):
    __tablename__ = 'gamedeprevision'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    __json__ = ["moduletype", "version", "published"]

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('gamedeppage.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    moduletype = Column(Enum("file", "folder"), nullable=False)
    page = relationship("GameDepPage")
    version = Column(Float(), default=0.1, index=True, nullable=False)
    created = Column(DateTime, default=datetime.now)
    published = Column(Boolean, default=False, index=True)
    file_obj = relationship(Files, uselist=False)
    binary = relationship(GameDepBinary, cascade="all, delete")
    
    def __init__(self, version, moduletype):
        self.version = version
        self.moduletype = moduletype

class GameDepDependency(Base):
    __tablename__ = 'gamedepdependency'
    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('gamedeppage.id'), 
                     nullable=False)
    rev_id = Column(Integer, ForeignKey('gamedeprevision.id'), 
                    nullable=False)
    page_obj = relationship("GameDepPage", uselist=False)
    rev_obj = relationship(GameDepRevision, uselist=False)
    
    def __init__(self, page_obj, rev_obj):
        self.page_obj = page_obj
        self.rev_obj = rev_obj

class GameDepPage(Base, JsonBase):
    __tablename__ = 'gamedeppage'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    __json__ = ["name", "display_name", "gamedeptype", "description",
                "view_count"]

    id = Column(Integer, primary_key=True)
    gamedeptype = Column(Enum("game", "dep"), nullable=False)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    owner = relationship(User)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)
    display_name = Column(Unicode(128), index=True, nullable=False)
    description = Column(Unicode(16384), default="")
    created = Column(DateTime, default=datetime.now)
    thread_id = Column(Integer, nullable=False, default=-1)
    album_id = Column(Integer, nullable=False, default=-1)
    view_count = Column(Integer, default=0, index=True)
    revisions = relationship(GameDepRevision,
                             cascade="all, delete, delete-orphan",
                             lazy="dynamic",
                             order_by=desc(GameDepRevision.version),
                             single_parent=True)
    tags = relationship(GameDepTags, 
                        cascade="all, delete, delete-orphan")
    dependencies = relationship(GameDepRevision, 
                                secondary=GameDepDependency.__table__, 
                                order_by=desc(GameDepRevision.version),
                                cascade="all, delete, delete-orphan",
                                single_parent=True)
    votes = relationship(GameDepVotes, lazy="dynamic",
                         cascade="all, delete, delete-orphan")
    
    def __init__(self, gamedeptype, name, display_name, owner):
        self.name = name
        self.display_name = display_name
        self.gamedeptype = gamedeptype
        self.owner = owner
