from sqlalchemy import create_engine

from nhl import Base, engine, session
from nhl.tables import Owner, EspnCred

import sys


if __name__ == '__main__':
    Base.metadata.create_all(engine) 

    session.add( Owner(1, 'Jenn Ranter', 'JENN') )
    session.add( Owner(2, 'Chris Wilson', 'WILS') )
    session.add( Owner(3, 'John Raines', 'RAIN') )
    session.add( Owner(4, 'Brandon Michael Burdette', 'BMB') )
    session.add( Owner(5, 'Ellen Richard', 'ELLN') )
    session.add( Owner(6, 'Abbey Siebert', 'SIEB') )
    session.add( Owner(7, 'Jake Schlossberg', 'PBX') )
    session.add( Owner(8, 'Stephen Sloat', 'SLOAT') )
    session.add( Owner(9, 'Laura Leonard', 'LEON') )
    session.add( Owner(10, 'Paul Moore', 'SEAL') )

    session.add( EspnCred(sys.argv[2], sys.argv[3]) )

    session.commit()
