"""
Logger Manager

Handles:
- Console logging
- File logging
- Summary CSV generation
"""

import csv
import logging
from pathlib import Path


class LoggerManager:

    def __init__(self, log_directory: Path):

        self.log_directory = log_directory
        self.log_directory.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_directory / "execution.log"
        self.summary_file = self.log_directory / "summary.csv"

        self.logger = logging.getLogger("ReplicaUpdater")
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers if logger is initialized multiple times
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(
            self.log_file,
            mode="w",
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self._initialize_summary_file()

    # ------------------------------------------------------------------

    def _initialize_summary_file(self):
        """
        Creates summary.csv with header.
        """

        with open(
            self.summary_file,
            mode="w",
            newline="",
            encoding="utf-8"
        ) as csv_file:

            writer = csv.writer(csv_file)

            writer.writerow([
                "Repository",
                "Status",
                "Files Found",
                "Files Updated",
                "Replica Values Updated",
                "Commit Created",
                "Remarks"
            ])

    # ------------------------------------------------------------------

    def write_summary(
        self,
        repository,
        status,
        files_found,
        files_updated,
        replica_updates,
        commit_created,
        remarks
    ):
        """
        Appends one repository result to summary.csv.
        """

        with open(
            self.summary_file,
            mode="a",
            newline="",
            encoding="utf-8"
        ) as csv_file:

            writer = csv.writer(csv_file)

            writer.writerow([
                repository,
                status,
                files_found,
                files_updated,
                replica_updates,
                commit_created,
                remarks
            ])

    # ------------------------------------------------------------------

    def info(self, message):
        self.logger.info(message)

    # ------------------------------------------------------------------

    def warning(self, message):
        self.logger.warning(message)

    # ------------------------------------------------------------------

    def error(self, message):
        self.logger.error(message)