import json
import click
import os
import sys
import logging
import pprint
from gnscli import uploader
from gnscli import gnsapi
from gnscli import checker
from gnscli import settings


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


def _read_gns_server_from_settings(_, gns_server):
    if gns_server:
        return gns_server
    gns_server = settings.Settings.config.get('gns_api_fqdn')
    if gns_server:
        return gns_server
    else:
        click.BadParameter("GNS API FQDN does not defined")


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--config', '-c', type=click.File('r'), callback=settings.Settings.load)
def cli(debug, config):
    """
    GNS command line tool.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@cli.group()
@click.option('--rules-path', '-r', type=click.Path(exists=True), envvar='GNS_RULES_PATH',
              callback=_validate_repo_path, default='.', help="Path to rules dir")
@click.pass_context
def rules(ctx, rules_path):
    """
    Manage GNS rules
    """
    ctx.obj = rules_path


@rules.command()
@click.option('--message', '-m', required=True, help="Describe you changes")
@click.option('--gns-server', envvar='GNS_SERVER', help="GNS FQDN",
              callback=_read_gns_server_from_settings)
@click.pass_obj
def upload(rules_path, gns_server, message):
    """
    Upload new or changed rules in GNS
    """
    LOG.info("Upload updated rules to GNS...")
    uploader.upload(gns_server, rules_path, message)


@rules.command()
@click.option('--event-desc', '-e', required=True, type=click.File('r'),
              callback=_validate_event_desc, help="JSON file with event description")
@click.pass_obj
def execute(rules_path, event_desc):
    """
    Run GNS rules locally
    """
    config = settings.Settings.config
    checker.check(config, rules_path, event_desc)


@cli.group()
@click.option('--gns-server', envvar='GNS_SERVER', callback=_read_gns_server_from_settings,
              help="GNS FQDN")
@click.pass_context
def gns(ctx, gns_server):
    """
    GNS API wrapper
    """
    ctx.obj = gns_server


@gns.command()
@click.pass_obj
def cluster_info(gns_server):
    """
    Show generic cluster info
    Equivalent to  GET `/system/state`
    """
    gns_state = gnsapi.get_cluster_info(gns_server)
    click.echo(pprint.pformat(gns_state))


@gns.command()
@click.pass_obj
def jobs_list(gns_server):
    """
    Show current jobs list by id
    Equivalent to  GET `/jobs/`
    """
    jobs = gnsapi.get_jobs(gns_server)
    click.echo(pprint.pformat(jobs))


@gns.command()
@click.argument('job_id')
@click.pass_obj
def kill_job(gns_server, job_id):
    """
    Terminate job by id.
    Now, by GNS API limitation, job just marked as `should be deleted`,
    physically it could be deleted for several time or never.
    """
    gnsapi.terminate_job(gns_server, job_id)


@gns.command()
@click.argument('host', required=False)
@click.argument('service', required=False)
@click.argument('severity', required=False)
@click.option('--file', '-f', type=click.File('r'), help="Path to JSON file with event description")
@click.pass_obj
def send_event(gns_server, host, service, severity, file):
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

    gnsapi.send_event(gns_server, event)


def main():
    """
    Command's entry point
    """
    try:
        cli()
    except (gnsapi.GNSAPIException, uploader.GitCommandError) as error:
        LOG.error("Error occurred: %s", error)
        sys.exit(1)

if __name__ == '__main__':
    main()
