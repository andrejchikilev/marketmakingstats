import os
import logging

from marketmakingstats.deploy_settings import *

from fabric.api import env, task, sudo, prefix, run, cd, settings, local, require
from fabric.contrib.files import upload_template, contains, append, exists

SUDO_PREFIX = 'sudo -i'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fabfile')


def _load_environment(env_name):
    """
    Sets specified environment
    """
    if env_name not in ENVIRONMENTS:
        raise ValueError("Incorrect environment name ({}). "
                         "Valid options are: {}"
                         .format(env_name, ENVIRONMENTS.keys()))
    _env = ENVIRONMENTS[env_name]
    env.user = _env['USER']
    env.hosts = ["{host}:{port}".format(host=_env['HOST'],
                                        port=_env['SSH_PORT'])]
    env.host_url = _env['HOST']
    env.branch = _env['GIT_BRANCH']
    env.current_host = _env['CURRENT_HOST']
    env.env_name = env_name
    env.settings_module = _env['SETTINGS_MODULE']
    env.key_filename = _env['KEY_FILENAME']


@task
def prod():
    """
    Makes sure prod environment is enabled
    """
    _load_environment('PROD')


@task
def create_non_priveledged_user():
    with settings(warn_only=True):
        sudo('adduser --disabled-login --gecos os {}'.format(DEPLOYMENT_USER))
        sudo('addgroup {}'.format(DEPLOYMENT_GROUP))
        sudo('adduser {user} {group}'
             .format(user=DEPLOYMENT_USER, group=DEPLOYMENT_GROUP))


@task
def install_system_packages():
    with settings(warn_only=True):
        sudo('apt-get update')
    sudo('apt-get -y --no-upgrade install {packages}'.format(packages=' '.join(UBUNTU_PACKAGES)))


@task
def checkout_repository():
    with cd(REMOTE_DEPLOY_DIR), settings(sudo_user=DEPLOYMENT_USER):
        if exists(PROJECT_NAME, use_sudo=True):
            sudo('rm -rf {project_dir}'.format(project_dir=PROJECT_NAME))       
        sudo('git clone {repo} {dir}'.format(repo=REPOSITORY, dir=PROJECT_NAME))
        sudo('chown -R {user}:{group} {dir}'
            .format(user=DEPLOYMENT_USER,
                    group=DEPLOYMENT_GROUP,
                    dir=PROJECT_NAME))


@task
def create_deploy_dirs():
    with cd(DEPLOY_DIR):
        sudo('mkdir -p static logs pid uploads',
             user=DEPLOYMENT_USER)


def add_virtualenv_settings_to_profile(profile_file):
    if not exists(profile_file):
        logger.info("Creating user profile: {}".format(profile_file))
        sudo('touch %s' % profile_file,
             user=DEPLOYMENT_USER)

    lines_to_append = [
        'export WORKON_HOME=%s' % WORKON_HOME,
        'export PROJECT_HOME=%s' % REMOTE_DEPLOY_DIR,
        'source /usr/local/bin/virtualenvwrapper.sh',
    ]

    for line in lines_to_append:
        logging.info("Trying to add lines into user {}".format(profile_file))
        if not contains(profile_file, line):
            append(profile_file, '\n' + line,
                   use_sudo=True)
            logging.info("{line} added".format(line=line))

    sudo('chown {user}:{group} {file}'
         .format(user=DEPLOYMENT_USER,
                 group=DEPLOYMENT_GROUP,
                 file=profile_file))


@task
def config_virtualenv():
    remote_postactivate_path = os.path.join(WORKON_HOME, ENV_NAME,
                                            'bin/postactivate')
    postactivate_context = {
        'DATABASE_URL': DATABASE_URL,
        'SETTINGS_MODULE': env.settings_module
    }
    upload_template(os.path.join(LOCAL_CONF_DIR, 'postactivate'),
                    remote_postactivate_path, context=postactivate_context,
                    use_sudo=True)


@task
def prepare_virtualenv():
    logger.info("Setting up the virtual environment.")
    sudo('pip install virtualenv')
    sudo('pip install virtualenvwrapper')

    add_virtualenv_settings_to_profile(USER_PROFILE_FILE)

    with prefix('source %s' % USER_PROFILE_FILE):
        with settings(warn_only=True), cd(REMOTE_DEPLOY_DIR):
            logger.info("Creating new virualenv.")
            sudo('mkvirtualenv %s -p /usr/bin/python3.5' % ENV_NAME,
                 user=DEPLOYMENT_USER)
    config_virtualenv()


@task
def create_database():
    """
    Create postgres database and dedicated user
    """
    logger.info("Setting the database.")
    with settings(warn_only=True):
        # Create database user
        with prefix("export PGPASSWORD=%s" % DB_PASSWORD):
            sudo('psql -c "CREATE ROLE %s WITH CREATEDB CREATEUSER LOGIN ENCRYPTED PASSWORD \'%s\';"' % (DB_USER, DB_PASSWORD),
                 user='postgres')
            sudo('psql -c "CREATE DATABASE %s WITH OWNER %s"' % (DB_NAME, DB_USER),
                 user='postgres')


@task
def prepare():
    install_system_packages()
    checkout_repository()
    create_deploy_dirs()
    prepare_virtualenv()
    create_database()

    if exists('/etc/nginx/sites-available/default'):
        with settings(warn_only=True):
            sudo('rm /etc/nginx/sites-available/default')


@task
def install_systemd_service():
    service_name = BACKEND_SERVICE
    remote_service = '/etc/systemd/system/{}'.format(service_name)
    context = {
        'PROJECT_NAME': PROJECT_NAME,
        'USER': DEPLOYMENT_USER,
        'GROUP': DEPLOYMENT_GROUP,
        'DEPLOY_DIR': DEPLOY_DIR,
    }
    upload_template(os.path.join(LOCAL_CONF_DIR, service_name),
                    remote_service,
                    context=context,
                    use_sudo=True,
                    backup=False)

    # Reread updated settings
    sudo('systemctl daemon-reload')
    # Autostart unit
    sudo('systemctl enable {}'.format(BACKEND_SERVICE))


@task
def deploy_nginx_config():
    require('host_url', 'env_name')
    remote_sa_path = '/etc/nginx/sites-available/%s' % PROJECT_NAME
    context = {
        'HOST': env.host_url,
        'CURRENT_HOST': env.current_host,
        'ENV': env.env_name,
        'DEPLOY_DIR': DEPLOY_DIR,
        'STATIC_ROOT': STATIC_ROOT,
        'STATIC_URL': STATIC_URL,
        'MEDIA_ROOT': MEDIA_ROOT,
        'MEDIA_URL': MEDIA_URL
    }
    upload_template(template_dir=LOCAL_CONF_DIR,
                    filename='nginx.conf.j2',
                    destination=remote_sa_path,
                    context=context,
                    use_sudo=True,
                    use_jinja=True)
    sudo('ln -sf %s /etc/nginx/sites-enabled' % remote_sa_path)


@task
def restart():
    with settings(warn_only=True):
        if 'inactive' not in sudo('systemctl --no-pager --full status %s' % BACKEND_SERVICE):
            sudo('systemctl stop %s' % BACKEND_SERVICE)
        sudo('systemctl start %s' % BACKEND_SERVICE)

    sudo('service nginx restart')


@task
def config(restart_after=True):
    require('current_host', 'hosts', 'settings_module')

    remote_conf_path = '%s/conf' % DEPLOY_DIR

    sudo('mkdir -p %s' % remote_conf_path,
         user=DEPLOYMENT_USER)
    GUNI_HOST = '127.0.0.1'

    upload_template(os.path.join(LOCAL_CONF_DIR, 'gunicorn.sh'), remote_conf_path, context={
        'DEPLOY_DIR': DEPLOY_DIR,
        'ENV_PATH': ENV_PATH,
        'SETTINGS_MODULE': env.settings_module,
        'GUNI_HOST': GUNI_HOST,
        'GUNI_PORT': GUNI_PORT,
        'GUNI_WORKERS': GUNI_WORKERS,
        'GUNI_TIMEOUT': GUNI_TIMEOUT,
        'GUNI_GRACEFUL_TIMEOUT': GUNI_GRACEFUL_TIMEOUT,
        'USER': DEPLOYMENT_USER,
        'GROUP': DEPLOYMENT_GROUP,
        'PROJECT_NAME': PROJECT_NAME
    }, mode=0o0750, use_sudo=True)

 
    # TODO: replace it with systemd unit
    install_systemd_service()
    deploy_nginx_config()
    sudo('chown -R {}:{} {}'.format(DEPLOYMENT_USER, DEPLOYMENT_GROUP, remote_conf_path))
    # sudo('systemd daemon-reload')

    config_virtualenv()
    if restart_after:
        with settings(warn_only=True):
            restart()


@task
def deploy_files():
    with cd(DEPLOY_DIR), settings(sudo_user=DEPLOYMENT_USER):
        sudo('git fetch')
        sudo('git reset --hard')
        sudo('git checkout {}'.format(env.branch))
        sudo('git pull origin {}'.format(env.branch))


@task
def install_req():
    logger.info("Installing python requirements.")
    with cd(DEPLOY_DIR), prefix('source %s' % VENV_ACTIVATE):
        with settings(sudo_user=DEPLOYMENT_USER):
            cache_dir = os.path.join(DEPLOY_DIR, '.cache')
            sudo('pip install -U pip')
            sudo('pip install --cache-dir {cache} -r {req_file}'
                 .format(cache=cache_dir, req_file='requirements.txt'))


@task
def deploy_static():
    """
    Collects django static files.
    """
    require('settings_module')
    with settings(sudo_user=DEPLOYMENT_USER,
                  sudo_prefix=SUDO_PREFIX), cd(DEPLOY_DIR):
        with prefix('workon %s' % ENV_NAME):
            sudo('python manage.py collectstatic --noinput --settings %s'
                 % env.settings_module)


@task
def update_static_chmod():
    sudo('chmod -R 664 %s' % STATIC_ROOT)
    sudo('chmod -R a+X %s' % STATIC_ROOT)
    sudo('chmod -R 664 %s' % MEDIA_ROOT)
    sudo('chmod -R a+X %s' % MEDIA_ROOT)


@task
def clean_pyc():
    """
    Cleans up redundant python bytecode files.
    """
    logger.info("Cleaning .pyc files.")
    with cd(DEPLOY_DIR):
        sudo("find . -name '*.pyc'")
        sudo('find . -name \*.pyc -delete')


@task
def migrate():
    with cd(DEPLOY_DIR):
        with settings(sudo_user=DEPLOYMENT_USER,
                      sudo_prefix=SUDO_PREFIX), prefix('workon %s' % ENV_NAME):
            sudo('python manage.py migrate')


@task
def first_time_deploy():
    """
    Call this task when deploying for the first time
    """
    create_non_priveledged_user()
    prepare()
    config()
    deploy()


@task
def deploy():
    require('branch', 'user', 'hosts')
    deploy_files()
    install_req()
    deploy_static()
    update_static_chmod()
    clean_pyc()
    migrate()
    restart()