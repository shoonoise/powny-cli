"""
This module is for upload updated or new rules to GNS.
"""

import envoy
import logging
from pownycli import gnsapi
from pownycli.settings import Settings

logger = logging.getLogger(__name__)


class GitCommandError(Exception):
    pass


def _update_head(gns_server: str, path: str):
    new_head = _execute_git_command("rev-parse HEAD", path, err_msg="Can't update HEAD").strip()
    current_head = gnsapi.get_header(gns_server)
    if new_head == current_head:
        logger.info("HEAD already updated")
        return
    gnsapi.set_header(gns_server, new_head)


def _execute_git_command(cmd: str, path, err_msg: str):
    git_warn_exit_code = 1
    full_cmd = 'git --git-dir={path}/.git --work-tree={path} {cmd}'.format(cmd=cmd, path=path)
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
    status = _execute_git_command('status', path, "Can't get git status").split('\n')

    if 'nothing to commit, working directory clean' in status[3]:
        logger.info("There is no changes.")

    logger.info("Commit current changes...")

    _execute_git_command('commit -a -m "{}"'.format(message), path,
                         "Can't commit your changes")

    logger.info("Pull changes from rules server...")

    _execute_git_command('pull --rebase', path, "Can't pull changes from server rules")

    logger.info("Sync you changes with rules server...")

    _execute_git_command('push', path, "Can't push your changes")

    gns_repos = Settings.get("gns_git_remotes")
    assert gns_repos, "GNS git remotes does not defined. Can't upload rules."
    for repo in gns_repos:
        logger.info("Upload rules to {}...".format(repo))
        _execute_git_command('push {} master'.format(repo), path, "Can't push to GNS remote")

    _update_head(gns_server, path)

    logger.info("You rules uploaded to GNS!")
