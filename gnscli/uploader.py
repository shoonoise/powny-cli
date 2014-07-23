"""
This module is for upload updated or new rules to GNS.
"""

import envoy
from gnscli import gnsapi
import logging
from gnscli.settings import get_config

LOG = logging.getLogger(__name__)


class UploadRulesException(Exception):
    pass


def _update_head(gns_server: str, path):
    new_head = _execute_git_command(cmd="rev-parse HEAD", extra={'path': path}, err_msg="Can't update HEAD").strip()
    current_head = gnsapi.get_header(gns_server)
    if new_head == current_head:
        LOG.info("HEAD already updated")
        return
    try:
        gnsapi.set_header(gns_server, new_head)
    except gnsapi.GNSAPIException:
        raise UploadRulesException("Can't update HEAD")


def _execute_git_command(cmd: str, extra: dict, err_msg: str):
    full_cmd = 'git --git-dir={path}/.git --work-tree={path} {cmd}'.format(cmd=cmd, **extra)
    result = envoy.run(full_cmd)
    if result.status_code > 10:
        raise UploadRulesException(err_msg, result.std_err, result.std_out, full_cmd)
    else:
        LOG.debug("Execute command: %s", full_cmd)
        LOG.info(result.std_out)
        return result.std_out


def main(gns_server, path, message):

    status = _execute_git_command(cmd='status', extra={'path': path}, err_msg="Can't get git status").split('\n')

    if 'nothing to commit, working directory clean' in status[3]:
        LOG.info("There is no changes.")

    LOG.info("Commit current changes...")

    msg = message

    _execute_git_command(cmd='commit -a -m {}'.format(msg), extra={'path': path},
                         err_msg="Can't commit your changes")

    LOG.info("Pull changes from rules server...")

    _execute_git_command(cmd='pull --rebase', extra={'path': path},
                         err_msg="Can't pull changes from server rules")

    LOG.info("Sync you changes with rules server...")

    _execute_git_command(cmd='push', extra={'path': path},
                         err_msg="Can't push your changes")

    gns_repos = get_config().get("gns_git_remotes")
    for repo in gns_repos:
        LOG.info("Upload rules to {}...".format(repo))
        _execute_git_command(cmd='push {} master'.format(repo), extra={'path': path},
                             err_msg="")

    _update_head(gns_server, path)

    LOG.info("You rules uploaded to GNS!")
