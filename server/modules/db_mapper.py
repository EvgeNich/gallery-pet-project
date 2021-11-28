from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ImageTable(Base):
    __tablename__ = 'images'

    img_id = Column(Integer, primary_key=True)

    file_name = Column(String(55), nullable=False)
    md5 = Column(String(32), nullable=False)
    file_size = Column(Integer, nullable=False)
    maker = Column(String(256))
    model = Column(String(256))
    creation_date = Column(DateTime)
    thumbnail = Column(Boolean, nullable=False)
    upload_date = Column(DateTime, nullable=False)