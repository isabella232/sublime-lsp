import subprocess
import re
import os
import sys
import logging


def get_url_struct(cwd, file_path):
    git_url = clean_git_url(get_git_url(cwd))
    commit_hash = get_git_commit_hash(cwd)
    path = file_path.replace(cwd, "")
    path = "/".join(path.split(os.sep))
    path = path.lstrip(os.sep)
    if git_url is None or commit_hash is None:
        return None
    return (git_url, commit_hash, path)


def get_git_commit_hash(cwd):
    args = ["git", "rev-parse", "HEAD"]
    return run_command_sync(args, cwd)


def get_git_url(cwd):
    args = ["git", "config", "--get", "remote.origin.url"]
    return run_command_sync(args, cwd)


GIT_PATTERN = re.compile("git\@|.git|https:\/\/")
SSH_PATTERN = re.compile("com:")


def clean_git_url(git_url):
    # TODO there are more cases to cover than this
    if git_url is None:
        return None
    git_url = GIT_PATTERN.sub("", git_url, 10)
    return SSH_PATTERN.sub("com/", git_url, 10)


def run_command_sync(args, cwd):
    try:
        output = subprocess.check_output(args, cwd=cwd)
        if sys.version_info >= (3, 0):
            return str(output, "utf-8").strip()
        return output.strip()
    except Exception as e:
        logging.debug("Error running %s in working directory %s" % (args, cwd))
        return None

# function getGitStatus(data) {
#     const parentDirectory = path.resolve(data.filename, "..").split(" ").join("\\ ");
#     const basename = path.basename(data.filename);

#     // if file has changed, return because annotations won't correlate
#     if (data.is_dirty) {
#         return null;
#     }
#     const fileChanged = this.hasFileChanged(parentDirectory, basename);
#     if (fileChanged) {
#         return null;
#     }

#     let gitCommitID = this.getGitCommitHash(parentDirectory);

#     const mainGitRepo = this.getTopLevelGitDirectory(parentDirectory);

#     let gitWebURI = this.getGitUrl(parentDirectory);
#     gitWebURI = this.cleanGitUrl(gitWebURI);

#     const relativeGitRepo = parentDirectory.split(mainGitRepo).join("");
#     const relativeFilePath = data.filename.split(`${mainGitRepo}/`).join("");

#     return {gitWebUri: gitWebURI, relativeGitRepo: relativeGitRepo, relativeFilePath: relativeFilePath, gitCommitId: gitCommitID};

# }