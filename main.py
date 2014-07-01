import json
import uuid
import argparse
import yaml
from raava.rules import get_handlers
from raava.rules import EventRoot
from gns.env import setup_config


def monkey_patch():
    import raava

    class Mock():
        def checkpoint(self):
            pass

        def get_current_task(self):
            return self

    raava.worker = Mock()


def config_alerts(conf=None):
    if conf:
        try:
            with open(conf) as config_file:
                conf_ = config_file.read()
        except Exception:
            print("Can't read config file")
            raise
        else:
            try:
                conf_dict = yaml.load(conf_)
            except ValueError as e:
                raise RuntimeError("Can't parse config.", e)
            else:
                setup_config(conf_dict)
    else:
        setup_config({'output':
                     {'email': {'server': 'gns-testing.haze.yandex.net'}}})


def import_module(name):
    module = __import__(name)
    return module.on_event


def get_event_root(event_desc):
    event = EventRoot()
    event.set_extra({'handler': 'on_event',
                     'job_id': str(uuid.uuid4()),
                     'counter': 0})
    description = {}

    try:
        with open(event_desc) as event_desc_file:
            event_desc_ = event_desc_file.read()
    except Exception:
        print("Can't open event description file.")
        raise
    else:
        exp = None
        try:
            description = json.loads(event_desc_)
        except ValueError as e1:
            exp = e1
            try:
                description = yaml.load(event_desc_)
            except ValueError as e2:
                exp = e2
        finally:
            if description:
                event.update(description)
            else:
                raise RuntimeError("Can't parse event description", exp)

    return event


def check_rule(event_root, handlers):
    matched_tasks = get_handlers(event_root, {'on_event': handlers})
    for task in matched_tasks:
        task(event_root)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run GNS rules locally.')
    parser.add_argument('-e', '--event-desc', required=True, help="JSON file with event description")
    parser.add_argument('-r', '--rule-path', required=True, help="Importable test rule module name")
    parser.add_argument('-c', '--config', help="Config for email/sms alerts")
    args = parser.parse_args()

    monkey_patch()
    config_alerts(args.config)

    handlers_to_check = set()
    handlers_to_check.add(import_module(args.rule_path))

    check_rule(get_event_root(args.event_desc), handlers_to_check)
