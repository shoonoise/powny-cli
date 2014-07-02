import json
import os
import uuid
import argparse
import sys
import yaml
import logging
import raava

from raava.rules import get_handlers
from raava.rules import EventRoot
from raava.handlers import Loader
from gns.env import setup_config
from pkg_resources import resource_stream


def monkey_patch():
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


def import_module(path_to_module):
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
        raise RuntimeError("Can't find function {name}".format(name=checked_fn_name))
    else:
        return functions_to_check


def get_event_root(event_desc):
    """
    Return event object, which GNS expected
    """
    event = EventRoot()
    event.set_extra({'handler': 'on_event',
                     'job_id': str(uuid.uuid4()),
                     'counter': 0})

    event.update(event_desc)
    return event


def get_default_config():
    config_stream = resource_stream(__name__, 'config.yaml')
    return config_stream


def check_rule(event_root, handlers):
    """
    Search for jobs which mapped for this event
    and execute it
    """
    matched_tasks = get_handlers(event_root, {'on_event': handlers})
    for task in matched_tasks:
        task(event_root)


def main():
    monkey_patch()

    parser = argparse.ArgumentParser(description='Run GNS rules locally.')
    parser.add_argument('-e', '--event-desc', required=True, help="JSON file with event description")
    parser.add_argument('-r', '--rule-path', required=True, help="Path to package with tested rules")
    parser.add_argument('-c', '--config', help="Config for email/sms alerts")
    args = parser.parse_args()

    if args.config:
        config = yaml.load(open(args.config))
    else:
        config = yaml.load(get_default_config())

    if args.event_desc == '-':
        event_desc = json.loads(sys.stdin.read())
    else:
        event_desc = json.loads(open(args.event_desc).read())

    # setup logging and output(sms, email, etc) configs
    logging.config.dictConfig(config.get('logging'))
    setup_config(config.get('output'))

    check_rule(get_event_root(event_desc), import_module(args.rule_path))


if __name__ == "__main__":
    main()
