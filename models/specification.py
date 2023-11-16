from sqlalchemy import Column, Integer, String, Text, ForeignKey
from models.base import Base

class Specification(Base):
    __tablename__ = 'specifications'

    id = Column(Integer, primary_key=True)
    base_spec_id = Column(Integer, ForeignKey('specifications.id'))
    name = Column(String(100))
    description = Column(Text)
    ordinality = Column(Integer)
    distance = Column(Integer)
    type = Column(String(100))

    def __str__(self):
        return f"Specification<{self.id}>: Name={self.name}, Type={self.type}, Description={self.description}"

    @classmethod
    def get(cls, session, spec_id):
        return session.query(cls).get(spec_id)
#    def __init__(self, base_spec_id, goal, direction, ordinality, distance):
#        self.base_spec_id = base_spec_id
#        self.goal = goal
#        self.direction = direction
#        self.ordinality = ordinality
#        self.distance = distance

#    @classmethod
#    def insert(cls, session, base_spec_id, goal, direction, ordinality, distance):
#        from main import session

#        new_spec = cls(base_spec_id, goal, direction, ordinality, distance)
#        session.add(new_spec)
#        session.commit()
