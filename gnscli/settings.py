from pkg_resources import resource_stream
import yaml


def get_config():
    return yaml.load(resource_stream(__name__, 'config.yaml'))
