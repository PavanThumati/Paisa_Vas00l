"""
YAML Manager

Responsible for:
- Finding all *-app.yaml files
- Updating every replicas value to 0
- Preserving YAML formatting using ruamel.yaml
"""

from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq


class YAMLManager:

    def __init__(self, logger):

        self.logger = logger

        self.yaml = YAML()

        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False

    # ------------------------------------------------------------------

    def process_repository(self, repository_path: Path):
        """
        Process all *-app.yaml files in a repository.

        Returns
        -------
        tuple
            (
                files_found,
                files_updated,
                replica_updates
            )
        """

        files_found = 0
        files_updated = 0
        replica_updates = 0

        yaml_files = sorted(
            repository_path.rglob("*-app.yaml")
        )

        for yaml_file in yaml_files:

            files_found += 1

            updated, count = self.process_yaml_file(
                yaml_file
            )

            if updated:
                files_updated += 1
                replica_updates += count

        return (
            files_found,
            files_updated,
            replica_updates
        )

    # ------------------------------------------------------------------

    def process_yaml_file(self, yaml_file: Path):
        """
        Process a single YAML file.

        Returns
        -------
        tuple

        (
            updated,
            replica_count
        )
        """

        self.logger.info(
            f"Scanning {yaml_file}"
        )

        try:

            with open(
                yaml_file,
                "r",
                encoding="utf-8"
            ) as file:

                documents = list(
                    self.yaml.load_all(file)
                )

            replica_updates = 0

            for document in documents:

                if document is None:
                    continue

                replica_updates += self.update_replicas(
                    document
                )

            if replica_updates == 0:

                self.logger.info(
                    "No replica changes required."
                )

                return False, 0

            with open(
                yaml_file,
                "w",
                encoding="utf-8"
            ) as file:

                self.yaml.dump_all(
                    documents,
                    file
                )

            self.logger.info(
                f"Updated {replica_updates} replica value(s)"
            )

            return True, replica_updates

        except Exception as ex:

            self.logger.error(
                f"Unable to process '{yaml_file}'. {ex}"
            )

            return False, 0

    # ------------------------------------------------------------------

    def update_replicas(self, node):
        """
        Recursively traverse YAML nodes and update:

            replicas: <any value>

        to

            replicas: 0
        """

        updates = 0

        if isinstance(node, CommentedMap):

            for key, value in node.items():

                if key == "replicas":

                    if value != 0:

                        node[key] = 0
                        updates += 1

                else:

                    updates += self.update_replicas(
                        value
                    )

        elif isinstance(node, CommentedSeq):

            for item in node:

                updates += self.update_replicas(
                    item
                )

        return updates