import os
import uuid
import sys
import raava

from raava.rules import get_handlers
from raava.rules import EventRoot
from raava.handlers import Loader
from gns.env import setup_config


class GNSCheckerException(Exception):
    pass


def __monkey_patch():
    """
    Patch raava worker to avoid import issue
    """
    class Mock():

        def __init__(self):
            pass

        def checkpoint(self):
            pass

        def get_current_task(self):
            return self

    raava.worker = Mock()


def _import_module(path_to_module: str):
    """
    Import modules from path
    returns set of functions named 'on_event'
    which fined in path
    """
    checked_fn_name = 'on_event'
    abspath_to_module = os.path.abspath(path_to_module)
    sys.path.append(abspath_to_module)
    loader = Loader(abspath_to_module, [checked_fn_name])
    functions_to_check = loader.get_handlers('').get(checked_fn_name)
    if not functions_to_check:
        raise GNSCheckerException("Can't find function {name}".format(name=checked_fn_name))
    else:
        return functions_to_check


def _get_event_root(event_desc: dict):
    """
    Return event object, which GNS expected
    """
    event = EventRoot()
    event.set_extra({'handler': 'on_event',
                     'job_id': str(uuid.uuid4()),
                     'counter': 0})

    event.update(event_desc)
    return event


def check(config: dict, rule_path: str, event_desc: dict):
    """
    Search for functions in GNS, which mapped for this event
    and execute it
    """
    setup_config(config)
    __monkey_patch()
    event_root = _get_event_root(event_desc)
    on_event_fn = _import_module(rule_path)

    matched_tasks = get_handlers(event_root, {'on_event': on_event_fn})
    for task in matched_tasks:
        try:
            task(event_root)
        except Exception as error:
            raise GNSCheckerException("Can't execute rule {}, by reason: {}".format(task, error))
