
from configparser import RawConfigParser

CONFIG = 'nuvla.conf'


def nuvla_conf_user_pass(fn=CONFIG):
    config = RawConfigParser()
    if fn not in config.read(fn):
        print(f'Failed reading config file {fn}')
        exit(1)
    username = config['default'].get('username')
    password = config['default'].get('password')
    return username, password

