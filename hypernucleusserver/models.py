from datetime import datetime
from pyracms.models import Files, User, Base
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

class GameDepPicture(Base):
    __tablename__ = 'gamedeppicture'
    __table_args__ = (UniqueConstraint('game_id', 'file_id'),
                        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('gamedeppage.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    
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
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    file_obj = relationship(Files, uselist=False, single_parent=True,
                            cascade="all, delete, delete-orphan")
    operatingsystem_obj = relationship(OperatingSystems, uselist=False)
    architecture_obj = relationship(Architectures, uselist=False)
                            
    def __init__(self, file_obj, operatingsystem_obj, architecture_obj):
        self.file_obj = file_obj
        self.operatingsystem_obj = operatingsystem_obj
        self.architecture_obj = architecture_obj

class GameDepDependencyOne(Base):
    __tablename__ = 'gamedepdependencyone'
    __table_args__ = (UniqueConstraint('dep_id', 'page_id'),
                        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})
    
    id = Column(Integer, primary_key=True)
    dep_id = Column(Integer, ForeignKey('gamedepdependency.id'),
                    nullable=False)
    page_id = Column(Integer, ForeignKey('gamedeppage.id'), nullable=False)
    
class GameDepDependencyTwo(Base):
    __tablename__ = 'gamedepdependencytwo'
    __table_args__ = (UniqueConstraint('dep_id', 'rev_id'),
                        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})
    
    id = Column(Integer, primary_key=True)
    dep_id = Column(Integer, ForeignKey('gamedepdependency.id'),
                    nullable=False)
    rev_id = Column(Integer, ForeignKey('gamedeprevision.id'), nullable=True)

class GameDepDependency(Base):
    __tablename__ = 'gamedepdependency'
    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('gamedeppage.id'), nullable=False)
    page_obj = relationship("GameDepPage",
                            secondary=GameDepDependencyOne.__table__,
                            uselist=False)
    rev_obj = relationship("GameDepRevision",
                            secondary=GameDepDependencyTwo.__table__,
                            uselist=False)

    def __init__(self, page_obj):
        self.page_obj = page_obj

class GameDepRevision(Base):
    __tablename__ = 'gamedeprevision'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
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

class GameDepPage(Base):
    __tablename__ = 'gamedeppage'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    gamedeptype = Column(Enum("game", "dep"), nullable=False)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    owner = relationship(User)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)
    display_name = Column(Unicode(128), index=True, nullable=False)
    description = Column(Unicode(16384), default="")
    created = Column(DateTime, default=datetime.now)
    deleted = Column(Boolean, default=False, index=True)
    revisions = relationship(GameDepRevision,
                             cascade="all, delete, delete-orphan",
                             lazy="dynamic",
                             order_by=desc(GameDepRevision.id),
                             single_parent=True)
    tags = relationship(GameDepTags, cascade="all, delete, delete-orphan")
    dependencies = relationship(GameDepDependency, cascade="all, delete")
    picture = relationship(Files, secondary=GameDepPicture.__table__,
                           cascade="all, delete")
    votes = relationship(GameDepVotes, lazy="dynamic",
                         cascade="all, delete, delete-orphan")
    
    def __init__(self, gamedeptype, name, display_name, owner):
        self.name = name
        self.display_name = display_name
        self.gamedeptype = gamedeptype
        self.owner = owner

