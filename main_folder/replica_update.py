"""
Main Application

Workflow

1. Read repositories from repos.txt
2. Clone repository
3. Checkout master
4. Create feature branch
5. Update YAML files
6. Commit changes
7. Push feature branch
8. Write summary
"""

import traceback

from config import Config
from logger_manager import LoggerManager
from git_manager import GitManager
from yaml_manager import YAMLManager


class ReplicaUpdater:

    def __init__(self):

        self.config = Config()

        self.logger = LoggerManager(
            self.config.log_directory
        )

        self.git = GitManager(
            self.config,
            self.logger
        )

        self.yaml = YAMLManager(
            self.logger
        )

        self.total_repositories = 0
        self.successful = 0
        self.skipped = 0
        self.failed = 0

    # ------------------------------------------------------------

    def read_repositories(self):

        repositories = []

        with open(
            self.config.repository_list,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                repo = line.strip()

                if not repo:
                    continue

                repositories.append({
                    "name": repo,
                    "slug": repo,
                    "clone_url": (
                        f"{self.config.bitbucket_url}"
                        f"/scm/"
                        f"{self.config.project_key.lower()}"
                        f"/{repo}.git"
                    )
                })

        return repositories

    # ------------------------------------------------------------

    def run(self):

        self.logger.info("=" * 80)
        self.logger.info("Replica Updater Started")
        self.logger.info("=" * 80)

        try:

            repositories = self.read_repositories()

            self.total_repositories = len(
                repositories
            )

            self.logger.info(
                f"Repositories Found : {self.total_repositories}"
            )

            for repository in repositories:

                self.process_repository(
                    repository
                )

        except Exception as ex:

            self.logger.error(str(ex))

            self.logger.error(
                traceback.format_exc()
            )

        self.print_summary()

    # ------------------------------------------------------------

    def process_repository(self, repository):

        repo_name = repository["name"]

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info(
            f"Processing Repository : {repo_name}"
        )
        self.logger.info("=" * 80)

        try:

            repo = self.git.clone_repository(
                repository
            )

            self.git.checkout_master(
                repo
            )

            self.git.create_feature_branch(
                repo
            )

            repo_path = self.git.repository_path(
                repository
            )

            (
                files_found,
                files_updated,
                values_updated
            ) = self.yaml.process_repository(
                repo_path
            )

            #
            # No matching YAML files
            #
            if files_found == 0:

                self.logger.info(
                    "No matching YAML files found."
                )

                self.logger.write_summary(
                    repository=repo_name,
                    status="SKIPPED",
                    files_found=0,
                    files_updated=0,
                    values_updated=0,
                    commit_created="No",
                    branch_pushed="No",
                    remarks="No matching YAML files found"
                )

                self.skipped += 1

                return

            #
            # Commit
            #
            commit_created = self.git.commit_changes(
                repo
            )

            branch_pushed = False

            if commit_created:

                branch_pushed = self.git.push_branch(
                    repo
                )

                status = "SUCCESS"

                remarks = (
                    "Commit created and branch pushed"
                )

                self.successful += 1

            else:

                status = "SKIPPED"

                remarks = "No file changes"

                self.skipped += 1

            self.logger.write_summary(
                repository=repo_name,
                status=status,
                files_found=files_found,
                files_updated=files_updated,
                values_updated=values_updated,
                commit_created=(
                    "Yes"
                    if commit_created
                    else "No"
                ),
                branch_pushed=(
                    "Yes"
                    if branch_pushed
                    else "No"
                ),
                remarks=remarks
            )

        except Exception as ex:

            self.failed += 1

            self.logger.error(
                f"Repository Failed : {repo_name}"
            )

            self.logger.error(
                str(ex)
            )

            self.logger.error(
                traceback.format_exc()
            )

            self.logger.write_summary(
                repository=repo_name,
                status="FAILED",
                files_found=0,
                files_updated=0,
                values_updated=0,
                commit_created="No",
                branch_pushed="No",
                remarks=str(ex)
            )
                # ------------------------------------------------------------

    def print_summary(self):

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("Execution Summary")
        self.logger.info("=" * 80)

        self.logger.info(
            f"Total Repositories : {self.total_repositories}"
        )

        self.logger.info(
            f"Successful          : {self.successful}"
        )

        self.logger.info(
            f"Skipped             : {self.skipped}"
        )

        self.logger.info(
            f"Failed              : {self.failed}"
        )

        self.logger.info("")
        self.logger.info("Execution completed.")

        self.logger.info(
            f"Execution Log : {self.config.log_directory / 'execution.log'}"
        )

        self.logger.info(
            f"Summary CSV   : {self.config.log_directory / 'summary.csv'}"
        )


# ----------------------------------------------------------------------

def main():

    updater = ReplicaUpdater()
    updater.run()


# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
