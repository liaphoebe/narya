import json
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base
from viewer import Viewer
from utils import create_key_from_path

class Mechanism(Base):
    __tablename__ = 'mechanisms'

    id = Column(Integer, primary_key=True)
    _params = Column(String, nullable=False) # We use a different internal variable to store data
    name = Column(String, nullable=False)
    class_name = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey('projects.id'))

    @property
    def params(self):
        """Return params as a dict."""
        return json.loads(self._params)

    @params.setter
    def params(self, d):
        """Set params as a string representation of dict."""
        self._params = json.dumps(d)

    @property
    def code(self):
        """Return code implementation of mechanism."""
        from main import app_instance
        func_name_with_path = f"{create_key_from_path(self.class_name.lower())}#{self.name}"
        return app_instance.viewer.get_method(func_name_with_path)

    @classmethod
    def create(cls, name, params, class_name):
        from main import session

        result = session.query(Mechanism).filter_by(name=name, class_name=class_name).first()
        if result is not None:
            return cls(name=name, params=params, class_name=class_name)
        else:
            new_mechanism = cls(name=name, params=params, class_name=class_name)
            session.add(new_mechanism)
            session.commit()
            return new_mechanism
