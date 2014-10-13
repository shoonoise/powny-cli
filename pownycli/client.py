import json
import click
import os
import sys
import logging
import logging.config
import requests
import shutil
import yaml
import webbrowser
import tabloid
from pkg_resources import resource_stream
from datetime import datetime as dt
from pownycli.settings import Settings
from pownycli import gitapi
from pownycli import pownyapi
from pownycli import checker
from requests.compat import urljoin
from pownycli.util import Colorfull


logger = logging.getLogger(__name__)


def _validate_repo_path(ctx, param, value):
    listing = os.listdir(value)
    if ('.git' not in listing) or ('pownyrules.yaml' not in listing):
        raise click.BadParameter(
            "{repo_path} is not git repository or file `pownyrules.yaml` not exist!"
            " Make sure that the path is a Powny rules repository.".format(repo_path=value))
    else:
        return value


def _validate_event_desc(ctx, param, event_file):
    if event_file is None:
        return None
    try:
        event_desc = json.load(event_file)
    except (TypeError, ValueError):
        logger.error("Can't parse event description file %s", event_file)
    else:
        return event_desc


def _read_powny_api_url_from_settings(ctx, param, api_url):
    if api_url:
        return api_url
    api_url = Settings.get('powny_api_url')
    if api_url:
        return api_url
    else:
        click.BadParameter("Powny API url does not defined")


def _get_event_from_args(event_args):
    if event_args and len(event_args) == 3:
        return {'host': event_args[0], 'service': event_args[1], 'status': event_args[2]}
    else:
        raise click.BadParameter("You mast pass `host service status` args or `--file` option")


@click.group()
@click.option('--debug/--no-debug', '-d', help="Enable debug logs")
@click.option('--work-dir', '-w', type=click.Path(), envvar='POWNY_WORK_DIR',
              callback=_validate_repo_path, default=gitapi.get_root(fallback="."), help="Path to rules dir")
@click.option('--config', '-c', callback=Settings.load, type=click.File('r'),
              help="Load config from file", metavar='PATH')
@click.version_option()
def cli(debug, work_dir, config):
    """
    Powny command line tool.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.config.dictConfig(Settings.get('logging', {}))
    # `pownyrules.yaml` from work dir has highest priority
    with open(os.path.join(work_dir, 'pownyrules.yaml')) as repo_conf:
        Settings.load(None, None, repo_conf)
    Settings.config['rules-path'] = work_dir


@cli.command("create-config")
@click.option('--force/--no-force', '-f', help="Rewrite existing config")
def gen_config(force):
    """
    Generate default user's config.
    """
    config_dir = '~/.config/powny-cli/'
    full_conf_dir = os.path.expanduser(config_dir)
    os.makedirs(full_conf_dir, exist_ok=True)
    full_config_path = os.path.join(full_conf_dir, 'config.yaml')
    if os.path.exists(full_config_path):
        if force:
            logging.warning("Config %s, already created. Will be rewrote.", full_config_path)
        else:
            raise RuntimeError(
                "Config {}, already exist. Nothing generated. Use `--force` to rewrite it.".format(full_config_path))

    with resource_stream(__name__, 'config.yaml') as source:
        with open(full_config_path, 'wb') as target:
            shutil.copyfileobj(source, target)
    logging.info("%s file created", full_config_path)


@cli.command("browse-logs")
@click.option('--browser', '-b', help="Target browser")
def open_log_page(browser):
    """
    Open kibana logs dashboard in browser.
    """
    url = Settings.get("kibana_dashboard_url")
    click.echo("Try to open {}".format(url))

    try:
        if browser:
            webbrowser.get(using=browser).open_new_tab(url)
        else:
            webbrowser.open_new_tab(url)
    except Exception as error:
        logger.error("Can't open %s in %s browser. Error occurred: %s", url, browser or "default", error)


@cli.command("cluster-info")
def cluster_info():
    """
    Show generic cluster info.
    """
    powny_state = pownyapi.get_cluster_info(Settings.get('powny_api_url'))
    click.echo(yaml.dump(powny_state))


@cli.group()
def rules():
    """
    Manage Powny rules.
    """


@rules.command()
@click.option('--force/--no-force', '-f', help="Force to upload rules")
def upload(force):
    """
    Upload new or changed rules in Powny.
    """
    logger.info("Upload updated rules to Powny...")
    gitapi.upload(Settings.get('powny_api_url'), Settings.get('rules-path'), force)


@rules.command("exec")
@click.argument('event_args', nargs=-1, required=False)
@click.option('--event-desc', '-e', type=click.File('r'),
              callback=_validate_event_desc, help="JSON file with event description")
def execute(event_desc, event_args):
    """
    Run Powny rules locally.
    """
    event = event_desc or _get_event_from_args(event_args)

    config = Settings.config
    checker.check(config, event)


@cli.group()
def job():
    """
    Powny API wrapper.
    """


@job.command("logs")
@click.option('--size', '-s', type=int, default=50, help="Amount of records")
@click.argument('job_id', required=True)
def job_logs(job_id, size):
    elastic_url = Settings.get('elastic_url')
    resp = requests.get(urljoin(elastic_url, '/_all/_search'),
                        params={'q': 'job_id:%s' % job_id, 'size': size})
    hits = resp.json()['hits']['hits']
    hits.sort(key=lambda x: x["_source"]["@timestamp"])

    lines = []
    for hit in hits:
        fields = hit["_source"]
        message = fields["msg"]
        args = fields.get("args")
        time = dt.strptime(fields["@timestamp"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d %b %H:%M:%S")
        level = fields["level"]
        node = fields["node"]

        if logger.getEffectiveLevel() != logging.DEBUG and level == 'DEBUG':
            continue

        node_name, node_role = node.split('-')[0], node.split('-')[1]

        if args:
            try:
                # To catch cases when `message = '%s (parents: %s)'`, but `args = ['Spawned the new job']`
                formatted_msg = message % tuple(args)
            except TypeError as error:
                logger.warning("Can't format string. %s. So next record is a raw.", error)
                formatted_msg = message + str(args)
        else:
            formatted_msg = message

        lines.append([node_name, node_role, time, level, formatted_msg])

    table = tabloid.FormattedTable()
    table.add_column('Role')
    table.add_column('Node', Colorfull.get_node)
    table.add_column('Time', Colorfull.timestamp)
    table.add_column('Level', Colorfull.get_level)
    table.add_column('Message')

    for line in lines:
        table.add_row(line)

    formatted_out = '\n'.join(table.get_table())

    if formatted_out:
        click.echo(formatted_out)
    else:
        click.echo("No logs yet.")


@job.command("list")
def job_list():
    """
    Show current jobs list by id.
    """
    jobs = pownyapi.get_jobs(Settings.get('powny_api_url'))
    click.echo('\n'.join(list(jobs)))


@job.command("kill")
@click.argument('job_id')
def kill_job(job_id):
    """
    Terminate job by id.
    Now, by Powny API limitation, job just marked as `should be deleted`,
    physically it could be deleted for several time or never.
    """
    pownyapi.terminate_job(Settings.get('powny_api_url'), job_id)


@job.command("send-event")
@click.argument('event_args', nargs=-1, required=False)
@click.option('--file', '-f', callback=_validate_event_desc, type=click.File('r'),
              help="Path to JSON file with event description")
def send_event(event_args, file):
    """
    Send event to Powny via API.
    Could be called with arguments `host service status` or with JSON file event description.
    """

    event = file or _get_event_from_args(event_args)

    logger.info("Send event: {}".format(event))
    pownyapi.send_event(Settings.get('powny_api_url'), event)


def main():
    """
    Command's entry point
    """
    try:
        cli()
    except Exception as error:
        logger.error("Error occurred: %s", error)
        if logger.getEffectiveLevel() == logging.DEBUG:
            raise
        sys.exit(1)

if __name__ == '__main__':
    main()
