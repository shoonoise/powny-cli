"""
This module is wrapper to Powny REST API.
"""

import json
import requests
import logging


logger = logging.getLogger(__name__)


class PownyAPIException(Exception):
    pass


def get_cluster_info(powny_server: str):
    resp = requests.get(powny_server + '/rest/v1/system/state')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't get cluster info")
    else:
        return resp.json()


def send_event(powny_server: str, event_desc: dict):
    resp = requests.post(powny_server + '/rest/v1/jobs',
                         headers={'content-type': 'application/json'},
                         data=json.dumps(event_desc))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't post new event.", resp.text)
    else:
        logger.info("New event posted. Job Id: {}".format(resp.json().get('id')))


def terminate_job(powny_server: str, job_id: str):
    resp = requests.delete(powny_server + '/rest/v1/jobs/{}'.format(job_id))

    if resp.status_code == 404:
        logger.info("Job id `{}` is not found. Probably it is already deleted or was not created".format(job_id))
        return
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't delete job id {}".format(job_id), resp.text)
    else:
        logger.info("Job id {} was deleted".format(job_id))


def set_header(powny_server: str, head: str):
    resp = requests.post(powny_server + '/rest/v1/rules/head',
                         headers={'content-type': 'application/json'},
                         data=json.dumps({"head": head}))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't upload new HEAD.", resp.text)
    else:
        logger.info("Set new head: {}".format(head))


def get_header(powny_server: str):
    resp = requests.get(powny_server + '/rest/v1/rules/head')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't upload new HEAD.")
    else:
        return resp.json().get('head')


def get_jobs(powny_server: str):
    resp = requests.get(powny_server + '/rest/v1/jobs')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't get jobs list")
    else:
        return resp.json()
