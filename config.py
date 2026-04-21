import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Railway provides DATABASE_URL with legacy "postgres://" prefix; SQLAlchemy 2.x requires "postgresql://"
_db_url = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
# Convert relative sqlite paths to absolute so the db file always lands in the project root
if _db_url.startswith('sqlite:///'):
    db_path = _db_url[len('sqlite:///'):]
    if not os.path.isabs(db_path):
        _db_url = 'sqlite:///' + os.path.join(basedir, db_path)

SQLALCHEMY_DATABASE_URI = _db_url
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
