import os
import yaml
import logging
from pkg_resources import resource_stream

logger = logging.getLogger(__name__)


class Settings:

    config = {}

    @classmethod
    def get(cls, key, default=None):
        if cls.config:
            value = cls.config.get(key, default)
            if value is None:
                raise RuntimeError("{} set to None. It's required option.".format(key))
            return value
        else:
            raise RuntimeError("powny-cli misconfigured.")

    @staticmethod
    def merge(config, update, paths=None):
        if paths is None:
            paths = []
        for key in update:
            if key in config:
                if isinstance(config[key], dict) and isinstance(update[key], dict):
                    Settings.merge(config[key], update[key], list(paths) + [str(key)])
                    continue
            config[key] = update[key]
        return config

    @classmethod
    def load(cls, ctx, param, file):
        """This callback loads config from file, if option `--config/-c` is defined,
           in any other cases loads config by default paths"""
        if file:
            logger.debug("Load config from %s", file)
            added_config = yaml.load(file) or {}
            cls.merge(cls.config, added_config)
        else:
            cls.merge(cls.config, yaml.load(resource_stream(__name__, 'config.yaml')))
            logger.debug("Load default config")
            path_to_user_config = os.path.expanduser('~/.config/powny-cli/config.yaml')
            if os.path.exists(path_to_user_config):
                logger.debug("Rewrite default values by %s", path_to_user_config)
                try:
                    user_conf = yaml.load(open(path_to_user_config))
                except (TypeError, ValueError) as error:
                    logger.warning("Can't load user config. %s", error)
                else:
                    cls.merge(cls.config, user_conf)
