from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base
from models.project import Project
from models.mechanism import Mechanism

class Dependency(Base):
    __tablename__ = 'dependencies'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project')
    name = Column(String)
    description = Column(String)

    mech_id = Column(Integer, ForeignKey('mechanisms.id'))
    mechanism = relationship('Mechanism', back_populates='dependencies')

Mechanism.dependencies = relationship('Dependency', order_by=Dependency.id, back_populates="mechanism")
