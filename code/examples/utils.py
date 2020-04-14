
from configparser import RawConfigParser

CONFIG = 'nuvla.conf'


def nuvla_conf_user_pass(fn=CONFIG):
    config = RawConfigParser()
    if fn not in config.read(fn):
        print("Failed reading config file {0}".format(cf))
        exit(1)
    username = config['default'].get('username')
    password = config['default'].get('password')
    return username, password

