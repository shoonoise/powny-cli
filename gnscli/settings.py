import os
from pkg_resources import resource_stream
import yaml


class Config:

    loaded = False
    config = None

    @classmethod
    def load_from_option(cls, ctx, param, file):
        if file:
            cls.loaded = True
            config = yaml.load(file)
            cls.config = config

    @classmethod
    def load_config(cls):
        config = yaml.load(resource_stream(__name__, 'config.yaml'))
        path_to_user_config = '~/.config/gnscli/config.yaml'
        if os.path.exists(path_to_user_config):
            config.update(yaml.load(open(path_to_user_config)))
        return config

    @classmethod
    def get_conf(cls):
        if cls.loaded:
            return cls.config
        else:
            return cls.load_config()
