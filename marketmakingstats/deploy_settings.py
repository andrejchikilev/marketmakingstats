import os

USER = 'root'
HOST = '165.227.126.229'

CURRENT_HOST = '165.227.126.229'

REPOSITORY = 'https://github.com/andrejchikilev/marketmakingstats'
PROJECT_NAME = 'marketmakingstats'
KEY_FILENAME = '~/.ssh/mms_rsa'

ROOT_USER = 'root'

DEPLOYMENT_USER = 'marketmakingstats'
DEPLOYMENT_GROUP = 'marketmakingstats'

REMOTE_DEPLOY_DIR = os.path.join('/home', DEPLOYMENT_USER)

USER_PROFILE_FILE = os.path.join(REMOTE_DEPLOY_DIR, '.profile')

DEPLOY_DIR = os.path.join(REMOTE_DEPLOY_DIR, PROJECT_NAME)

MEDIA_ROOT = os.path.join(DEPLOY_DIR, 'uploads')
MEDIA_URL = '/uploads/'

STATIC_ROOT = os.path.join(DEPLOY_DIR, 'staticfiles')
STATIC_URL = '/static/'

UBUNTU_PACKAGES = [
    'git',
    'python-pip',
    'nginx',
    'postgresql-9.5',
    'python3.5',
]

WORKON_HOME = os.path.join(REMOTE_DEPLOY_DIR, '.virtualenvs')
ENV_NAME = PROJECT_NAME
VENV_BIN_DIR = os.path.join(WORKON_HOME, ENV_NAME, 'bin')
VENV_ACTIVATE = os.path.join(VENV_BIN_DIR, 'activate')

ENV_PATH = os.path.join(WORKON_HOME, ENV_NAME)

LOCAL_CONF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'conf_templates')

DB_HOST = 'localhost'
DB_USER = 'marketmakingstats'
DB_PASSWORD = 'zo1queiYae8uje5aNgaek'
DB_NAME = 'marketmakingstats'

DATABASE_URL = 'postgres://%s:%s@%s/%s' % (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)

# Systemd service name
BACKEND_SERVICE = 'marketmakingstats.service'

SETTINGS_MODULE = 'marketmakingstats.prod_settings'
ENVIRONMENTS = {
    # TODO: this may include more env-specific things like
    # deployment users, database credentials, etc
    'PROD': {
        'HOST': HOST,
        'SSH_PORT': '22',
        'USER': USER,
        'GIT_BRANCH': 'master',
        'CURRENT_HOST': CURRENT_HOST,
        'SETTINGS_MODULE': SETTINGS_MODULE,
        'KEY_FILENAME': KEY_FILENAME,
    },
}
