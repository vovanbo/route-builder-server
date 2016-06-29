from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geography

Base = declarative_base()


def init_db(engine):
    Base.metadata.create_all(bind=engine)


class Route(Base):
    __tablename__ = 'route'

    id = Column(postgresql.UUID(), nullable=False, primary_key=True)
    origin = Column(Geography(geometry_type='POINT'))
    origin_name = Column(String, nullable=False)
    destination = Column(Geography(geometry_type='POINT'))
    destination_name = Column(String, nullable=False)
    waypoints = Column(postgresql.ARRAY(Geography(geometry_type='POINT')),
                       nullable=True)
    waypoints_names = Column(postgresql.ARRAY(String), nullable=True)
    polyline = Column(Geography(geometry_type='LINESTRING'))
    bounds = Column(postgresql.JSON, nullable=True)
    created = Column(DateTime(timezone=True))
