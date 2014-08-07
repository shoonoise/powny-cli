import json
import click
import os
import sys
import logging
import logging.config
import pprint
import yaml
import webbrowser
from pownycli.settings import Settings
from pownycli import uploader
from pownycli import gnsapi
from pownycli import checker


LOG = logging.getLogger(__name__)


def _validate_repo_path(_, value):
    if '.git' not in os.listdir(value):
        raise click.BadParameter(
            "{repo_path} is not git repository!".format(repo_path=value))
    else:
        return value


def _validate_event_desc(_, event_file):
    try:
        event_desc = json.load(event_file)
    except (TypeError, ValueError):
        LOG.error("Can't parse event description file %s", event_file)
    else:
        return event_desc


def _read_gns_api_url_from_settings(_, api_url):
    if api_url:
        return api_url
    api_url = Settings.get('gns_api_url')
    if api_url:
        return api_url
    else:
        click.BadParameter("GNS API url does not defined")


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--config', '-c', type=click.File('r'), callback=Settings.load)
def cli(debug, config):
    """
    GNS command line tool.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.config.dictConfig(Settings.get('logging', {}))


@cli.group()
@click.option('--rules-path', '-r', type=click.Path(exists=True), envvar='GNS_RULES_PATH',
              callback=_validate_repo_path, default='.', help="Path to rules dir")
@click.pass_context
def rules(ctx, rules_path):
    """
    Manage GNS rules.
    """
    ctx.obj = rules_path


@rules.command()
@click.option('--message', '-m', required=True, help="Describe you changes")
@click.option('--api-url', envvar='GNS_API_URL', help="GNS API URL",
              callback=_read_gns_api_url_from_settings)
@click.pass_obj
def upload(rules_path, api_url, message):
    """
    Upload new or changed rules in GNS.
    """
    LOG.info("Upload updated rules to GNS...")
    uploader.upload(api_url, rules_path, message)


@rules.command("exec")
@click.option('--event-desc', '-e', required=True, type=click.File('r'),
              callback=_validate_event_desc, help="JSON file with event description")
@click.pass_obj
def execute(rules_path, event_desc):
    """
    Run GNS rules locally.
    """
    config = Settings.config
    checker.check(config, rules_path, event_desc)


@cli.group()
@click.option('--api-url', envvar='GNS_API_URL', callback=_read_gns_api_url_from_settings,
              help="GNS API URL", metavar="<url>")
@click.pass_context
def gns(ctx, api_url):
    """
    GNS API wrapper.
    """
    ctx.obj = api_url


@gns.command("cluster-info")
@click.pass_obj
def cluster_info(api_url):
    """
    Show generic cluster info.
    """
    gns_state = gnsapi.get_cluster_info(api_url)
    click.echo(yaml.dump(gns_state))


@gns.command("job-list")
@click.pass_obj
def job_list(api_url):
    """
    Show current jobs list by id.
    """
    jobs = gnsapi.get_jobs(api_url)
    click.echo(pprint.pformat(jobs))


@gns.command("kill-job")
@click.argument('job_id')
@click.pass_obj
def kill_job(api_url, job_id):
    """
    Terminate job by id.
    Now, by GNS API limitation, job just marked as `should be deleted`,
    physically it could be deleted for several time or never.
    """
    gnsapi.terminate_job(api_url, job_id)


@gns.command("send-event")
@click.argument('host', required=False)
@click.argument('service', required=False)
@click.argument('severity', required=False)
@click.option('--file', '-f', type=click.File('r'), help="Path to JSON file with event description")
@click.pass_obj
def send_event(api_url, host, service, severity, file):
    """
    Send event to GNS via API.
    Could be called with arguments `host service severity` or with JSON file event description.
    """

    if file:
        with file:
            event = json.load(file)
    elif host and service and severity:
        event = {'host': host, 'service': service, 'severity': severity}
    else:
        LOG.error("You mast pass `host service severity` args or --file option")
        sys.exit(1)

    LOG.info("Send event: {}".format(pprint.pformat(event)))

    gnsapi.send_event(api_url, event)


@cli.command("browse-logs")
@click.option('--browser', '-b', help="Target browser")
def open_log_page(browser):
    """
    Open kibana logs dashboard immediately in browser.
    """
    url = Settings.get("kibana_dashboard_url")

    try:
        if browser:
            webbrowser.get(using=browser).open_new_tab(url)
        else:
            webbrowser.open_new_tab(url)
    except Exception as error:
        LOG.error("Can't open %s in %s browser. Error occurred: %s", url, browser or "default", error)


def main():
    """
    Command's entry point
    """
    try:
        cli()
    except Exception as error:
        LOG.error("Error occurred: %s", error)
        sys.exit(1)

if __name__ == '__main__':
    main()
