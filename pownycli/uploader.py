"""
This module is for upload updated or new rules to Powny.
"""

import envoy
import logging
from pownycli import pownyapi
from pownycli.settings import Settings

logger = logging.getLogger(__name__)


class GitCommandError(Exception):
    pass


def _multiline_log(level: int, prefix: str, out_lines: str):
    for line in out_lines.split('\n'):
        if len(line):
            logger.log(level, prefix, line)


def _show_rules_info(powny_server: str):
    info = pownyapi.get_rules_info(powny_server)
    if len(info['errors']) != 0:
        logger.warning("Cannot load some modules for HEAD=%s:", info['head'])
        for (module_name, exc) in info['errors'].items():
            logger.warning("Error in '%s':\n%s", module_name, exc)
    for dest in ('methods', 'handlers'):
        if len(info['exposed'][dest]) != 0:
            logger.debug("Exposed %s:", dest)
            for func_name in info['exposed'][dest]:
                logger.debug(" --- %s", func_name)


def _update_head(powny_server: str, path: str):
    new_head = _execute_git_command("rev-parse HEAD", path, err_msg="Can't update HEAD").strip()
    logger.debug("Local HEAD is %s", new_head)
    current_head = pownyapi.get_rules_info(powny_server)['head']
    logger.debug("Remote HEAD is %s", current_head)
    if new_head == current_head:
        logger.info("HEAD already updated")
        return
    logger.debug("Update HEAD to %s", new_head)
    pownyapi.set_header(powny_server, new_head)
    _show_rules_info(powny_server)


def _execute_git_command(cmd: str, path, err_msg: str):
    git_warn_exit_code = 1
    if path is not None:
        full_cmd = 'git --git-dir={path}/.git --work-tree={path} {cmd}'.format(cmd=cmd, path=path)
    else:
        full_cmd = cmd
    logger.debug("Execute command: %s", full_cmd)
    result = envoy.run(full_cmd)
    out, err, exit_code = result.std_out, result.std_err, result.status_code
    _multiline_log(logging.DEBUG, "Git stdout: %s", out)
    if exit_code > git_warn_exit_code:
        _multiline_log(logging.ERROR, "Git stderr: %s", err)
        raise GitCommandError(err_msg)
    elif exit_code == git_warn_exit_code:
        if err:
            _multiline_log(logging.ERROR, "Git stderr: %s", err)
            raise GitCommandError(err_msg)
        elif out:
            _multiline_log(logging.DEBUG, "Git stdout: %s", out)
        return out
    else:
        return out


def get_root(fallback):
    try:
        return _execute_git_command('git rev-parse --show-toplevel', None, "Can't find Git repo").strip()
    except GitCommandError:
        return fallback


def add(path: str, file_name: str):
    _execute_git_command('add {name}'.format(name=file_name), path, "Can't add file %s" % file_name)
    logger.info("New rule %s added", file_name)


def upload(powny_server: str, path: str, message: str, force: bool):
    """
    This function execute git commands:
        - git commit -a -m "{message}"
        - git pull --rebase
        - git push # to origin
        - git push ssh://git@powny/remote.git # to each Powny git
    and POST new HEAD hash to Powny via API
    """
    status = _execute_git_command('status --porcelain', path, "Can't get git status")

    if len(status) == 0:
        logger.info("There are no new or modified rules.")
    else:
        commit_needed = False
        for changed_file in filter(len, status.split('\n')):
            file_status, file_name = filter(len, changed_file.split(' '))
            if file_status == "A":
                logger.info("New rule '%s' was added", file_name)
                commit_needed = True
            elif file_status == "M":
                logger.info("Rule '%s' was modified", file_name)
                commit_needed = True
            elif file_status == "D":
                logger.info("Rule '%s' will be removed", file_name)
                commit_needed = True
            elif file_status == "??":
                logger.info("New rule '%s' is present. Use `rules add` command to add the rule", file_name)
            else:
                raise RuntimeError("Unknown status %s for file %s", file_status, file_name)

        if commit_needed:
            logger.info("Commit current changes...")

            if not message:
                logger.info("`--message` option was not specified")
                message = input("Enter commit message: ")

            _execute_git_command('commit -a -m "{}"'.format(message), path,
                                 "Can't commit your changes")

    logger.info("Pull changes from rules server...")

    _execute_git_command('pull --rebase', path, "Can't pull changes from server rules")

    logger.info("Sync you changes with rules server...")

    cmd = 'push --force' if force else 'push'
    _execute_git_command(cmd, path, "Can't push your changes")

    powny_repos = Settings.get("powny_git_remotes")
    assert powny_repos, "Powny git remotes does not defined. Can't upload rules."
    for repo in powny_repos:
        logger.info("Upload rules to {}...".format(repo))
        cmd = 'push --force {} master' if force else 'push {} master'
        _execute_git_command(cmd.format(repo), path, "Can't push to Powny remote")

    logger.debug("Update head...")
    _update_head(powny_server, path)

    logger.info("You rules uploaded to Powny!")
