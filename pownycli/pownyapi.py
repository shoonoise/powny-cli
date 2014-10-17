"""
This module is wrapper to Powny REST API.
"""

import json
import requests
import logging


logger = logging.getLogger(__name__)


class PownyAPIException(Exception):
    pass


def _safe_api_invocation(req, msg, *args, **kwargs):
    try:
        resp = req(*args, **kwargs)
    except requests.ConnectionError:
        raise PownyAPIException("Connection error while execute request: {}".format(*args, **kwargs))
    else:
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            logger.error("Something goes wrong: {}".format(resp.content))
            raise PownyAPIException(msg)
        else:
            return resp.json()['result']


def get_cluster_info(powny_server: str):
    return _safe_api_invocation(requests.get, "Can't get cluster info",
                                powny_server + '/v1/system/state')


def send_event(powny_server: str, event_desc: dict):
    logger.info("Try to send event %s", event_desc)
    jobs = _safe_api_invocation(requests.post, "Can't post new event.",
                                powny_server + '/v1/jobs',
                                headers={'content-type': 'application/json'},
                                data=json.dumps(event_desc))
    if len(jobs) == 0:
        logger.info("No matching handlers for this event")
    else:
        logger.info("New event posted. Relevant jobs:")
        for (job_id, job_info) in jobs.items():
            logger.info("Job: %s -> %s", job_id, job_info['method'])


def terminate_job(powny_server: str, job_id: str):
    logger.info("Try to kill job %s", job_id)
    try:
        resp = requests.delete(powny_server + '/v1/jobs/{}'.format(job_id))
    except requests.ConnectionError:
        raise PownyAPIException("Connection error while execute request: {}".format(
            powny_server + '/v1/jobs/{}'.format(job_id)))

    if resp.status_code == 404:
        logger.info("Job id `{}` is not found. Probably it is already deleted or was not created".format(job_id))
        return
    elif resp.status_code == 503:
        logger.error("Can't delete job with id `{}` in this time. Please try again now".format(job_id))
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise PownyAPIException("Can't delete job id {}".format(job_id), resp.text)
    else:
        logger.info("Job id {} was deleted".format(job_id))


def set_header(powny_server: str, head: str):
    return _safe_api_invocation(requests.post, "Can't upload new HEAD.",
                                powny_server + '/v1/rules',
                                headers={'content-type': 'application/json'},
                                data=json.dumps({'head': head}))


def get_rules_info(powny_server: str):
    return _safe_api_invocation(requests.get, "Can't get the rules info.",
                                powny_server + '/v1/rules')


def get_jobs(powny_server: str):
    return _safe_api_invocation(requests.get, "Can't get jobs list",
                                powny_server + '/v1/jobs')


def get_cluster_config(powny_server: str):
    return _safe_api_invocation(requests.get, "Can't get powny's cluster config from server",
                                powny_server + '/v1/system/config')
