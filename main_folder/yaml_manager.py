"""
YAML Manager

Responsible for:
1. Find all *-app.yaml files
2. Update replicas -> 0

3. Find all *-horizontalpodautoscaler.yml files
4. Update minReplicas -> 0

This implementation updates only the required lines and
preserves the original file formatting.
"""

import re
from pathlib import Path


class YAMLManager:

    def __init__(self, logger):

        self.logger = logger

        self.replicas_pattern = re.compile(
            r'^(\s*replicas\s*:\s*)\d+(\s*(#.*)?)?$'
        )

        self.min_replicas_pattern = re.compile(
            r'^(\s*minReplicas\s*:\s*)\d+(\s*(#.*)?)?$'
        )

    # ------------------------------------------------------------------

    def process_repository(self, repository_path: Path):

        files_found = 0
        files_updated = 0
        values_updated = 0

        yaml_files = []

        yaml_files.extend(
            repository_path.rglob("*-app.yaml")
        )

        yaml_files.extend(
            repository_path.rglob("*-horizontalpodautoscaler.yml")
        )

        for yaml_file in sorted(yaml_files):

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

                lines = file.readlines()

            updated_lines = []
            updates = 0

            if yaml_file.name.endswith("-app.yaml"):

                pattern = self.replicas_pattern
                replacement = r"\g<1>0\2"

            else:

                pattern = self.min_replicas_pattern
                replacement = r"\g<1>0\2"

            for line in lines:

                new_line, count = pattern.subn(
                    replacement,
                    line
                )

                if count:

                    updates += count

                updated_lines.append(
                    new_line
                )

            if updates == 0:

                return False, 0

            with open(
                yaml_file,
                "w",
                encoding="utf-8"
            ) as file:

                file.writelines(
                    updated_lines
                )

            self.logger.info(
                f"Updated {updates} value(s)"
            )

            return True, updates

        except Exception as ex:

            self.logger.error(
                f"Unable to process {yaml_file}"
            )

            self.logger.error(
                str(ex)
            )

            return False, 0
