"""
YAML Manager

Responsible for:

1. Find all *-app.yaml files
2. Update replicas -> 0

3. Find all *-horizontalpodautoscaler.yml files
4. Update minReplicas -> 0

Uses ruamel.yaml so formatting/comments are preserved.
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

        files_found = 0
        files_updated = 0
        values_updated = 0

        #
        # Process *-app.yaml
        #
        app_yaml_files = sorted(
            repository_path.rglob("*-app.yaml")
        )

        #
        # Process *-horizontalpodautoscaler.yml
        #
        hpa_yaml_files = sorted(
            repository_path.rglob("*-horizontalpodautoscaler.yml")
        )

        all_yaml_files = app_yaml_files + hpa_yaml_files

        for yaml_file in all_yaml_files:

            files_found += 1

            updated, count = self.process_yaml_file(
                yaml_file
            )

            if updated:
                files_updated += 1
                values_updated += count

        return (
            files_found,
            files_updated,
            values_updated
        )

    # ------------------------------------------------------------------

    def process_yaml_file(self, yaml_file: Path):

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

            updates = 0

            #
            # Determine which key to update
            #
            if yaml_file.name.endswith("-app.yaml"):

                target_key = "replicas"

            else:

                target_key = "minReplicas"

            for document in documents:

                if document is None:
                    continue

                updates += self.update_key(
                    document,
                    target_key
                )

            if updates == 0:

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
                f"Updated {updates} value(s)"
            )

            return True, updates

        except Exception as ex:

            self.logger.error(
                f"Unable to process {yaml_file}"

            )

            self.logger.error(str(ex))

            return False, 0

    # ------------------------------------------------------------------

    def update_key(self, node, target_key):

        updates = 0

        if isinstance(node, CommentedMap):

            for key in list(node.keys()):

                value = node[key]

                if key == target_key:

                    if value != 0:

                        node[key] = 0

                        updates += 1

                else:

                    updates += self.update_key(
                        value,
                        target_key
                    )

        elif isinstance(node, CommentedSeq):

            for item in node:

                updates += self.update_key(
                    item,
                    target_key
                )

        return updates
