import os
from pkg_resources import resource_stream
import yaml


class Settings:

    config = None

    @classmethod
    def load(cls, ctx, param, file):
        if file:
            cls.loaded = True
            config = yaml.load(file)
            cls.config = config
        else:
            config = yaml.load(resource_stream(__name__, 'config.yaml'))
            path_to_user_config = os.path.expanduser('~/.config/gnscli/config.yaml')
            if os.path.exists(path_to_user_config):
                config.update(yaml.load(open(path_to_user_config)))
            cls.config = config
