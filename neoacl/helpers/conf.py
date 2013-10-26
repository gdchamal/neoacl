import yaml

config_file = 'conf/neoacl.yaml'


# XXX : need to really do a correct configuration
def get_config():
    with open(config_file) as f:
        conf = yaml.load(f.read())
    return conf

CONF = get_config()
