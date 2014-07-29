"""
This module is for upload updated or new rules to GNS.
"""

import envoy
from gnscli import gnsapi
import logging
from gnscli.settings import Settings

logger = logging.getLogger(__name__)


class GitCommandError(Exception):
    pass


def _update_head(gns_server: str, path: str):
    new_head = _execute_git_command(cmd="rev-parse HEAD", extra={'path': path}, err_msg="Can't update HEAD").strip()
    current_head = gnsapi.get_header(gns_server)
    if new_head == current_head:
        logger.info("HEAD already updated")
        return
    gnsapi.set_header(gns_server, new_head)


def _execute_git_command(cmd: str, extra: dict, err_msg: str):
    git_warn_exit_code = 1
    full_cmd = 'git --git-dir={path}/.git --work-tree={path} {cmd}'.format(cmd=cmd, **extra)
    logger.debug("Execute command: %s", full_cmd)
    result = envoy.run(full_cmd)
    out, err, exit_code = result.std_out, result.std_err, result.status_code
    logger.debug("Git stdout: %s", out)
    if exit_code > git_warn_exit_code:
        raise GitCommandError(err_msg, err, out, full_cmd)
    elif exit_code == git_warn_exit_code:
        logger.warning("Git stderr: %s", err)
        return out
    else:
        return out


def upload(gns_server: str, path: str, message: str):
    """
    This function execute git commands:
        - git commit -a -m "{message}"
        - git pull --rebase
        - git push # to origin
        - git push ssh://git@gns/remote.git # to each GNS git
    and POST new HEAD hash to GNS via API
    """
    status = _execute_git_command(cmd='status', extra={'path': path}, err_msg="Can't get git status").split('\n')

    if 'nothing to commit, working directory clean' in status[3]:
        logger.info("There is no changes.")

    logger.info("Commit current changes...")

    _execute_git_command(cmd='commit -a -m {}'.format(message), extra={'path': path},
                         err_msg="Can't commit your changes")

    logger.info("Pull changes from rules server...")

    _execute_git_command(cmd='pull --rebase', extra={'path': path},
                         err_msg="Can't pull changes from server rules")

    logger.info("Sync you changes with rules server...")

    _execute_git_command(cmd='push', extra={'path': path},
                         err_msg="Can't push your changes")

    gns_repos = Settings.config.get("gns_git_remotes")
    for repo in gns_repos:
        logger.info("Upload rules to {}...".format(repo))
        _execute_git_command(cmd='push {} master'.format(repo), extra={'path': path},
                             err_msg="")

    _update_head(gns_server, path)

    logger.info("You rules uploaded to GNS!")
