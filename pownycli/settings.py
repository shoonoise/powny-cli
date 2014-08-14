import os
import yaml
from pkg_resources import resource_stream


class Settings:

    config = None

    @classmethod
    def get(cls, key, default=None):
        if cls.config:
            return cls.config.get(key, default)

    @classmethod
    def load(cls, ctx, param, file):
        """This callback loads config from file, if option `--config/-c` is defined,
           in any other cases loads config by default paths"""
        if file:
            cls.config = yaml.load(file)
        else:
            config = yaml.load(resource_stream(__name__, 'config.yaml'))
            path_to_user_config = os.path.expanduser('~/.config/powny-cli/config.yaml')
            if os.path.exists(path_to_user_config):
                config.update(yaml.load(open(path_to_user_config)))
            cls.config = config
