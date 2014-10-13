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
    resp = requests.get(powny_server + '/v1/system/state')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't get cluster info")
    else:
        return resp.json()['result']


def send_event(powny_server: str, event_desc: dict):
    resp = requests.post(powny_server + '/v1/jobs',
                         headers={'content-type': 'application/json'},
                         data=json.dumps(event_desc))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't post new event.", resp.text)
    else:
        jobs = resp.json()['result']
        if len(jobs) == 0:
            logger.info("No matching handlers for this event")
        else:
            logger.info("New event posted. Relevant jobs:")
            for (job_id, job_info) in resp.json()['result'].items():
                logger.info("Job: %s -> %s", job_id, job_info['method'])


def terminate_job(powny_server: str, job_id: str):
    logger.info("Try to kill job {}".format(job_id))
    resp = requests.delete(powny_server + '/v1/jobs/{}'.format(job_id))

    if resp.status_code == 404:
        logger.info("Job id `{}` is not found. Probably it is already deleted or was not created".format(job_id))
        return
    elif resp.status_code == 503:
        logger.info("Can't delete job with id `{}` in this time. Please try again now".format(job_id))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't delete job id {}".format(job_id), resp.text)
    else:
        logger.info("Job id {} was deleted".format(job_id))


def set_header(powny_server: str, head: str):
    resp = requests.post(powny_server + '/v1/rules',
                         headers={'content-type': 'application/json'},
                         data=json.dumps({'head': head}))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't upload new HEAD.", resp.text)
    else:
        logger.info("Set new head: {}".format(head))


def get_rules_info(powny_server: str):
    resp = requests.get(powny_server + '/v1/rules')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't get the rules info. {}".format(resp.content))
    else:
        return resp.json()['result']


def get_jobs(powny_server: str):
    resp = requests.get(powny_server + '/v1/jobs')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't get jobs list")
    else:
        return resp.json()['result']


def get_cluster_config(powny_server: str):
    resp = requests.get(powny_server + '/v1/system/config')
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't get powny's cluster config from server")
    else:
        return resp.json()['result']
