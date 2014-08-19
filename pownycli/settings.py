import os
import yaml
import logging
from pkg_resources import resource_stream

logger = logging.getLogger(__name__)


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
            logger.debug("Load config from %s", file)
            cls.config = yaml.load(file)
        else:
            config = yaml.load(resource_stream(__name__, 'config.yaml'))
            logger.debug("Load default config")
            path_to_user_config = os.path.expanduser('~/.config/powny-cli/config.yaml')
            if os.path.exists(path_to_user_config):
                logger.debug("Rewrite default values by %s", path_to_user_config)
                try:
                    user_conf = yaml.load(open(path_to_user_config))
                except (TypeError, ValueError) as error:
                    logger.warning("Can't load user config. %s", error)
                else:
                    config.update(user_conf)
            cls.config = config
