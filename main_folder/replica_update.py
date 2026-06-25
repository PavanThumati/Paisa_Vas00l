"""
Main Application

Workflow

1. Load configuration
2. Initialize logger
3. Connect to Bitbucket
4. Fetch repositories
5. Clone repository
6. Checkout master
7. Create feature branch
8. Update replicas to 0
9. Commit changes
10. Write summary
"""

import traceback

from config import Config
from logger_manager import LoggerManager
from bitbucket_client import BitbucketClient
from git_manager import GitManager
from yaml_manager import YAMLManager


class ReplicaUpdater:

    def __init__(self):

        self.config = Config()

        self.logger = LoggerManager(
            self.config.log_directory
        )

        self.bitbucket = BitbucketClient(
            self.config,
            self.logger
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

    def run(self):

        self.logger.info("=" * 80)
        self.logger.info("Replica Updater Started")
        self.logger.info("=" * 80)

        try:

            repositories = self.bitbucket.get_repositories()

            self.total_repositories = len(repositories)

            self.logger.info(
                f"Repositories discovered : {self.total_repositories}"
            )

            for repository in repositories:

                self.process_repository(repository)

        except Exception as ex:

            self.logger.error(str(ex))
            self.logger.error(traceback.format_exc())

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

            #
            # Clone Repository
            #
            repo = self.git.clone_repository(
                repository
            )

            #
            # Checkout master
            #
            self.git.checkout_master(
                repo
            )

            #
            # Create Feature Branch
            #
            self.git.create_feature_branch(
                repo
            )

            #
            # Repository Path
            #
            repo_path = self.git.repository_path(
                repository
            )

            #
            # Update YAML Files
            #
            (
                files_found,
                files_updated,
                replica_updates
            ) = self.yaml.process_repository(
                repo_path
            )

            #
            # No YAML Files
            #
            if files_found == 0:

                self.logger.info(
                    "No *-app.yaml files found."
                )

                self.logger.write_summary(
                    repository=repo_name,
                    status="SKIPPED",
                    files_found=0,
                    files_updated=0,
                    replica_updates=0,
                    commit_created="No",
                    remarks="No *-app.yaml files found"
                )

                self.skipped += 1

                return

            #
            # Commit Changes
            #
            commit_created = self.git.commit_changes(
                repo
            )

            if commit_created:

                status = "SUCCESS"

                remarks = "Commit created"

                self.successful += 1

            else:

                status = "SKIPPED"

                remarks = "No file changes"

                self.skipped += 1

            #
            # CSV Summary
            #
            self.logger.write_summary(
                repository=repo_name,
                status=status,
                files_found=files_found,
                files_updated=files_updated,
                replica_updates=replica_updates,
                commit_created=(
                    "Yes"
                    if commit_created
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
                replica_updates=0,
                commit_created="No",
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
        self.logger.info(
            "Execution completed."
        )

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