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
@click.option('--config', '-c', type=click.File('r'), callback=settings.Config.load_from_option)
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
    try:
        uploader.upload(gns_server, rules_path, message)
    except uploader.UploadRulesException as error:
        LOG.error("Error occurred while rules upload. %s", error)
        sys.exit(1)


@cli.group()
def gns():
    """
    GNS API wrapper
    """


@gns.command()
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
def cluster_info(gns_server):
    try:
        gns_state = gnsapi.get_cluster_info(gns_server)
    except gnsapi.GNSAPIException as error:
        LOG.error("Can't execute GNS API call. %s", error)
        sys.exit(1)
    else:
        click.echo(pprint.pformat(gns_state))


@gns.command()
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
def jobs_list(gns_server):
    try:
        jobs = gnsapi.get_jobs(gns_server)
    except gnsapi.GNSAPIException as error:
        LOG.error("Can't execute GNS API call. %s", error)
        sys.exit(1)
    else:
        click.echo(pprint.pformat(jobs))


@gns.command()
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
@click.argument('job_id')
def kill_job(gns_server, job_id):
    """
    Terminate job by id.
    Now, by GNS API limitation, job just marked as `should be deleted`,
    physically it could be deleted for several time or never.
    """
    try:
        gnsapi.terminate_job(gns_server, job_id)
    except gnsapi.GNSAPIException as error:
        LOG.error("Can't execute GNS API call. %s", error)
        sys.exit(1)


@gns.command()
@click.argument('host', required=False)
@click.argument('service', required=False)
@click.argument('severity', required=False)
@click.option('--file', '-f', type=click.File('r'), help="Path to JSON file with event description")
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
def send_event(host, service, severity, file, gns_server):
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

    try:
        gnsapi.send_event(gns_server, event)
    except gnsapi.GNSAPIException as error:
        LOG.error("Can't execute GNS API call. %s", error)
        sys.exit(1)

if __name__ == "__main__":
    cli()
