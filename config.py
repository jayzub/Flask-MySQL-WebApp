# Create dummy secrey key so we can use sessions
SECRET_KEY = 'jhgfdxcvbnkihgpoiuyghj@Tzfhg'

# Create in-memory database
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root2:root@localhost/inventory_db'
SQLALCHEMY_ECHO = False

# Flask-Security config
#SECURITY_URL_PREFIX = "/admin"
SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
SECURITY_PASSWORD_SALT = "jhytrfHJUYTRiuhgcvbnjk"

# Flask-Security URLs, overridden because they don't put a / at the end
#SECURITY_LOGIN_URL = "/login/"
#SECURITY_LOGOUT_URL = "/logout/"
#SECURITY_REGISTER_URL = "/register/"

#SECURITY_POST_LOGIN_VIEW = "/admin/"
#SECURITY_POST_LOGOUT_VIEW = "/admin/"
#SECURITY_POST_REGISTER_VIEW = "/admin/"

# Flask-Security features
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
SQLALCHEMY_TRACK_MODIFICATIONS = False

FLASK_ADMIN_SWATCH = 'flatly'
