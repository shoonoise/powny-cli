import json
import click
import os
import logbook
from gnscli import uploader
from gnscli import gnsapi
from gnscli.log import LOG


def _validate_repo_path(_, value):
    if '.git' not in os.listdir(value):
        raise click.BadParameter(
            "{repo_path} is not git repository!".format(repo_path=value))
    else:
        return value


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug: bool):
    """
    GNS command line tool.
    """
    if debug:
        LOG.level = logbook.DEBUG


@cli.group()
def rules():
    """
    Manage GNS rules
    """


@rules.command()
@click.option('--rules-path', '-r', type=click.Path(exists=True), envvar='GNS_RULES_PATH',
              callback=_validate_repo_path, required=True, help="Path to rules dir")
@click.option('--message', '-m', required=True, help="Describe you changes")
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
def upload(gns_server, rules_path, message):
    """
    Upload new or changes rules in GNS
    """
    uploader.main(gns_server, rules_path, message)


@cli.group()
def gns():
    """
    GNS API wrapper
    """


@gns.command()
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
def cluster_info(gns_server):
    try:
        gns_state = json.dumps(gnsapi.get_cluster_info(gns_server), indent=2, separators=(',', ': '), sort_keys=True)
    except gnsapi.GNSAPIException:
        raise
    else:
        click.echo(gns_state)
    try:
        jobs = gnsapi.get_jobs(gns_server)
    except gnsapi.GNSAPIException:
        raise
    else:
        click.echo(jobs)


@gns.command()
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
@click.argument('job_id')
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
@click.option('--gns-server', envvar='GNS_SERVER', required=True, help="GNS FQDN")
def send_event(host, service, severity, file, gns_server):
    """
    Send event to GNS via API.
    Could be called with arguments `host service severity` or with JSON file event description.
    """

    if file:
        with file:
            event = json.loads(file.read())
    elif host and service and severity:
        event = {'host': host, 'service': service, 'severity': severity}
    else:
        LOG.error("You mast pass `host service severity` args or --file option")
        return

    LOG.info("Send event: {}".format(event))
    gnsapi.send_event(gns_server, event)

if __name__ == "__main__":
    cli()  # pylint: disable=E1120
