"""
Git Manager

Responsible for:
- Clone repository
- Checkout base branch
- Synchronize with remote
- Create feature branch
- Stage changes
- Commit changes
"""

from pathlib import Path
from git import Repo, GitCommandError


class GitManager:

    def __init__(self, config, logger):

        self.config = config
        self.logger = logger

        self.clone_directory = config.clone_directory
        self.clone_directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------

    def clone_repository(self, repository):
        """
        Clone repository if it does not exist.
        Otherwise, reuse the existing local repository.
        """

        repo_path = self.repository_path(repository)

        if repo_path.exists():

            self.logger.info(
                f"Repository already exists: {repository['name']}"
            )

            return Repo(repo_path)

        self.logger.info(
            f"Cloning repository: {repository['name']}"
        )

        repo = Repo.clone_from(
            repository["clone_url"],
            repo_path
        )

        return repo

    # ------------------------------------------------------------------

    def checkout_master(self, repo):
        """
        Checkout the configured base branch and synchronize it
        with the remote repository.
        """

        base_branch = self.config.base_branch

        self.logger.info(
            f"Checking out '{base_branch}'"
        )

        origin = repo.remotes.origin

        origin.fetch()

        repo.git.checkout(base_branch)

        repo.git.reset(
            "--hard",
            f"origin/{base_branch}"
        )

        repo.git.clean("-fd")

    # ------------------------------------------------------------------

    def create_feature_branch(self, repo):
        """
        Creates the configured feature branch.

        If it already exists locally, delete and recreate it
        from the latest master.
        """

        feature_branch = self.config.feature_branch

        existing_branches = [
            branch.name
            for branch in repo.branches
        ]

        if feature_branch in existing_branches:

            self.logger.info(
                f"Deleting existing branch '{feature_branch}'"
            )

            repo.git.branch(
                "-D",
                feature_branch
            )

        self.logger.info(
            f"Creating branch '{feature_branch}'"
        )

        repo.git.checkout(
            "-b",
            feature_branch
        )

    # ------------------------------------------------------------------

    def commit_changes(self, repo):
        """
        Stage all modified files and create a commit.

        Returns
        -------
        bool

        True  -> Commit created

        False -> No changes detected
        """

        if not repo.is_dirty(untracked_files=True):

            self.logger.info(
                "No changes detected."
            )

            return False

        self.logger.info(
            "Staging modified files."
        )

        repo.git.add(A=True)

        self.logger.info(
            "Creating commit."
        )

        repo.index.commit(
            self.config.commit_message
        )

        self.logger.info(
            "Commit created successfully."
        )

        return True

    # ------------------------------------------------------------------

    def repository_path(self, repository):
        """
        Returns the local path of a cloned repository.
        """

        return (
            self.clone_directory /
            repository["slug"]
        )