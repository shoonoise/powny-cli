import json
import click
import os
import sys
import logging
import pprint
from gnscli import uploader
from gnscli import gnsapi
from gnscli import settings


LOG = logging.getLogger(__name__)


def _validate_repo_path(_, value):
    if '.git' not in os.listdir(value):
        raise click.BadParameter(
            "{repo_path} is not git repository!".format(repo_path=value))
    else:
        return value


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
def rules():
    """
    Manage GNS rules
    """


@rules.command()
@click.option('--rules-path', '-r', type=click.Path(exists=True), envvar='GNS_RULES_PATH',
              callback=_validate_repo_path, default='.', help="Path to rules dir")
@click.option('--message', '-m', required=True, help="Describe you changes")
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
def upload(gns_server, rules_path, message):
    """
    Upload new or changed rules in GNS
    """
    LOG.info("Upload updated rules to GNS...")
    uploader.upload(gns_server, rules_path, message)


@cli.group()
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
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

if __name__ == "__main__":
    try:
        cli()
    except (gnsapi.GNSAPIException, uploader.GitCommandError) as error:
        LOG.error("Error occurred: %s", error)
        sys.exit(1)
