import os

DEBUG = True

SECRET_KEY = os.urandom(24)

DB_URI = 'mysql+pymysql://root:123456@localhost:3306/test?charset=utf8'

SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# dialect+driver://username:password@host:port/database
# DIALECT = 'mysql'
# DRIVER = 'pymysql'
# USERNAME = 'root'
# PASSWORD = '123456'
# HOST = 'localhost'
# PORT = '3306'
# DATABASE = 'label_system'
#
# SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT,
#                                                                        DATABASE)
# SQLALCHEMY_TRACK_MODIFICATIONS = False