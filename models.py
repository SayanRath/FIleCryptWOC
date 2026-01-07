
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class File(Base):
    __tablename__ = "Files_n_Folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    owned_by = Column(String)
    Access= Column(String)
    Actions = Column(String)
    location = Column(String, default="home")

class Folder(Base):
    __tablename__ = "FolderNames"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    owned_by = Column(String)
    Access= Column(String)
    Actions = Column(String)
    location = Column(String, default="home")

class FileMetadata(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True) # Original filename (encrypted or plain)
    content_type = Column(String)
    file_size = Column(BigInteger)
    file_type = Column(String)
    owned_by = Column(String)
    access= Column(String)
    action=Column(String)
    minio_key = Column(String, unique=True) # The path inside MinIO
    created_at = Column(DateTime(timezone=True), server_default=func.now())