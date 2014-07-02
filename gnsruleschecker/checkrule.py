import json
import os
import uuid
import argparse
import sys
import yaml
import logging
import importlib
import raava

from raava.rules import get_handlers
from raava.rules import EventRoot
from gns.env import setup_config
from pkg_resources import resource_stream


def monkey_patch():

    class Mock():
        def checkpoint(self):
            pass

        def get_current_task(self):
            return self

    raava.worker = Mock()


def import_module(name):
    module = importlib.find_loader(name, [os.getcwd()])
    if not module:
        raise ImportError("Can't import module %s" % name)
    else:
        test_module = module.load_module()
    return test_module.on_event


def get_event_root(event_desc):
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
    matched_tasks = get_handlers(event_root, {'on_event': handlers})
    for task in matched_tasks:
        task(event_root)


def main():
    monkey_patch()

    parser = argparse.ArgumentParser(description='Run GNS rules locally.')
    parser.add_argument('-e', '--event-desc', required=True, help="JSON file with event description")
    parser.add_argument('-r', '--rule-name', required=True, help="Importable test rule module name")
    parser.add_argument('-c', '--config', help="Config for email/sms alerts")
    args = parser.parse_args()

    if args.config:
        config = yaml.load(open(args.config))
    else:
        config = yaml.load(get_default_config())

    if args.event_desc == '-':
        event_desc = json.loads(sys.stdin.read())
    else:
        event_desc = json.loads(open(args.event_desc))


    # setup logging and output(sms, email, etc) configs
    logging.config.dictConfig(config.get('logging'))
    setup_config(config.get('output'))

    handlers_to_check = {import_module(args.rule_name)}

    check_rule(get_event_root(event_desc), handlers_to_check)


if __name__ == "__main__":
    main()
