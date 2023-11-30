from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Branch(Base):
    __tablename__ = 'branches'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    status = Column(String(20), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint('name'),
    )

    @validates('status')
    def validate_status(self, key, value):
        if value not in ['open', 'closed']:
            raise ValueError('Invalid status value. Must be "open" or "closed".')
        return value
