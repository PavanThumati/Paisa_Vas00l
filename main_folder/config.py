"""
Configuration Manager

Reads application configuration from config.json and provides
easy access to configuration properties.
"""

import json
from pathlib import Path


class Config:
    """Loads and exposes application configuration."""

    def __init__(self, config_path="config.json"):
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file '{self.config_path}' not found."
            )

        with open(self.config_path, "r", encoding="utf-8") as config_file:
            self.config = json.load(config_file)

    @property
    def bitbucket_url(self):
        return self.config["bitbucket"]["url"].rstrip("/")

    @property
    def project_key(self):
        return self.config["bitbucket"]["project_key"]

    @property
    def username(self):
        return self.config["bitbucket"]["username"]

    @property
    def password(self):
        return self.config["bitbucket"]["password"]

    @property
    def base_branch(self):
        return self.config["git"]["base_branch"]

    @property
    def feature_branch(self):
        return self.config["git"]["feature_branch"]

    @property
    def commit_message(self):
        return self.config["git"]["commit_message"]

    @property
    def clone_directory(self):
        return Path(self.config["directories"]["clone_directory"])

    @property
    def log_directory(self):
        return Path(self.config["directories"]["log_directory"])

    @property
    def repository_list(self):
        return self.config["repository_list"]
