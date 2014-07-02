import json
import os
import uuid
import argparse
import yaml
import logging
import importlib
import raava

from raava.rules import get_handlers
from raava.rules import EventRoot
from gns.env import setup_config


def monkey_patch():

    class Mock():
        def checkpoint(self):
            pass

        def get_current_task(self):
            return self

    raava.worker = Mock()


def load_file(file_name, loaders):
    try:
        with open(file_name) as f:
            content = f.read()
    except BaseException:
        logging.error("Can't open file %s", file_name)
        raise
    else:
        exp = None
        parsed_content = {}

        for loader in loaders:
            try:
                parsed_content = loader(content)
            except BaseException as e:
                exp = e

        if not parsed_content:
            raise RuntimeError("Can't parse file: %s", file_name) from exp
        else:
            return parsed_content


def config_alerts(conf):
    setup_config(load_file(conf, (json.loads, yaml.load)))


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

    event.update(load_file(event_desc, (yaml.load,)))
    return event


def check_rule(event_root, handlers):
    matched_tasks = get_handlers(event_root, {'on_event': handlers})
    for task in matched_tasks:
        task(event_root)


def main():
    parser = argparse.ArgumentParser(description='Run GNS rules locally.')
    parser.add_argument('-e', '--event-desc', required=True, help="JSON/YAML file with event description")
    parser.add_argument('-r', '--rule-path', required=True, help="Importable test rule module name")
    parser.add_argument('-c', '--config', required=True, help="Config for email/sms alerts")
    args = parser.parse_args()

    logging.config.dictConfig(load_file(args.config, (yaml.load,)).get('logging'))

    monkey_patch()
    config_alerts(args.config)

    handlers_to_check = set()
    handlers_to_check.add(import_module(args.rule_path))

    check_rule(get_event_root(args.event_desc), handlers_to_check)

if __name__ == "__main__":
    main()
