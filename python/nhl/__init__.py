from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sys

engine = create_engine('sqlite:///%s' % sys.argv[1], echo=False)

Base = declarative_base()
#Base.metadata.create_all(engine) 

Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

