"""
This module is wrapper to GNS REST API.
"""

import json
import requests
import logging


LOG = logging.getLogger(__name__)


class GNSAPIException(Exception):
    pass


def get_cluster_info(gns_server: str):
    resp = requests.get(gns_server + '/rest/v1/system/state')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise GNSAPIException("Can't get cluster info")
    else:
        return resp.json()


def send_event(gns_server: str, event_desc: dict):
    resp = requests.post(gns_server + '/rest/v1/jobs',
                         headers={'content-type': 'application/json'},
                         data=json.dumps(event_desc))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise GNSAPIException("Can't post new event.", resp.text)
    else:
        LOG.info("New event posted. Job Id: {}".format(resp.json().get('id')))


def terminate_job(gns_server: str, job_id: str):
    resp = requests.delete(gns_server + '/rest/v1/jobs/{}'.format(job_id))

    if resp.status_code == 404:
        LOG.info("Job id `{}` is not found. Probably it is already deleted or was not created".format(job_id))
        return
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise GNSAPIException("Can't delete job id {}".format(job_id), resp.text)
    else:
        LOG.info("Job id {} was deleted".format(job_id))


def set_header(gns_server: str, head: str):
    resp = requests.post(gns_server + '/rest/v1/rules/head',
                         headers={'content-type': 'application/json'},
                         data=json.dumps({"head": head}))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise GNSAPIException("Can't upload new HEAD.", resp.text)
    else:
        LOG.info("Set new head: {}".format(head))


def get_header(gns_server: str):
    resp = requests.get(gns_server + '/rest/v1/rules/head')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise GNSAPIException("Can't upload new HEAD.")
    else:
        return resp.json().get('head')


def get_jobs(gns_server: str):
    resp = requests.get(gns_server + '/rest/v1/jobs')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise GNSAPIException("Can't get jobs list")
    else:
        return resp.json()
