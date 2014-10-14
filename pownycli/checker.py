import logging
from pownycli import pownyapi
from powny.core import context, apps, tools, rules
from powny.core.backends import CasNoValue, CasNoValueError, CasData, CasVersionError

logger = logging.getLogger(__name__)


class PownyCheckerException(Exception):
    pass


class FakeCas:
    data = {}

    @classmethod
    def replace_value(cls, path, value=CasNoValue, version=None,
                      default=CasNoValue, fatal_write=True):
        old = cls.data.get(path)
        if old is None:
            if default is CasNoValue:
                raise CasNoValueError()
            old = CasData(value=default, version=None, stored=None)
        else:
            old = CasData(
                value=old["value"],
                version=old["version"],
                stored=tools.from_isotime(old["stored"]),
            )
        if value is not CasNoValue:
            if version is not None and old.version is not None and version <= old.version:
                write_ok = False
                msg = "Can't rewrite '{}' with version {} (old version: {})".format(path, version, old.version)
                if fatal_write:
                    raise CasVersionError(msg)
                else:
                    logger.debug(msg)
            else:
                cls.data[path] = {
                    "value": value,
                    "version": version,
                    "stored": tools.make_isotime(),
                }
                write_ok = True
        else:
            write_ok = None
        return old, write_ok


class FakeContext:
    def __init__(self):
        self.number = 0
        self.old_value = None
        self.value = None

    def get_extra(self):
        return {'number': self.number}

    def get_job_id(self):
        return str(self.number)

    def save(self):
        pass

    @staticmethod
    def get_cas_storage():
        return FakeCas


def _build_events(event_desc):
    events = []
    event_type = type(event_desc)

    if event_type is list:
        events.extend(event_desc)
    elif event_type is dict:
        events.append(event_desc)
    else:
        raise PownyCheckerException("Event description should be array "
                                    "of events or event object. Not {}".format(event_type))
    for event in events:
        if 'description' not in event:
            event['description'] = ''
        logger.info("Add event: %s", event)

    return events


def _get_cluster_config(powny_server: str):
    config = pownyapi.get_cluster_config(powny_server)
    return config


def check(config: dict, event_desc):
    cluster_config = _get_cluster_config(config.get('powny_api_url'))
    cluster_config['logging'] = config.get('logging')
    apps.init('powny', 'local', args=[], raw_config=cluster_config)

    context.get_context = FakeContext

    exposed, errors = tools.make_loader('rules').get_exposed(config['rules-path'])

    for module in errors:
        logger.error("Can't load %s module by reason %s", module, errors[module])

    for event in _build_events(event_desc):
        for (name, handler) in exposed.get("handlers", {}).items():
            if rules.check_match(handler, event):
                try:
                    handler(**event)
                except Exception as error:
                    logger.exception("Can't execute %s rule by reason %s", name, error)
