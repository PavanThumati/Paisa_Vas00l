"""
Bitbucket Server REST API Client

Responsible for:
- Connecting to Bitbucket Server
- Fetching all repositories from a project
- Handling pagination
"""

import requests
from requests.auth import HTTPBasicAuth


class BitbucketClient:

    def __init__(self, config, logger):

        self.config = config
        self.logger = logger

        self.base_url = config.bitbucket_url.rstrip("/")
        self.project_key = config.project_key

        self.session = requests.Session()

        self.session.auth = HTTPBasicAuth(
            config.username,
            config.password
        )

        self.session.headers.update({
            "Content-Type": "application/json"
        })

    # ------------------------------------------------------------------

    def get_repositories(self):
        """
        Returns all repositories in the configured Bitbucket project.

        Returns
        -------
        list

        Example

        [
            {
                "name": "customer-service",
                "slug": "customer-service",
                "clone_url": "https://bitbucket.company.com/scm/abcd/customer-service.git"
            }
        ]
        """

        repositories = []

        start = 0
        limit = 100

        while True:

            url = (
                f"{self.base_url}"
                f"/rest/api/1.0/projects/"
                f"{self.project_key}"
                f"/repos"
                f"?limit={limit}&start={start}"
            )

            self.logger.info(
                f"Fetching repositories (start={start})"
            )

            response = self.session.get(
                url,
                timeout=60
            )

            if response.status_code == 401:
                raise Exception(
                    "Authentication failed. Check username/password."
                )

            if response.status_code == 404:
                raise Exception(
                    f"Project '{self.project_key}' not found."
                )

            response.raise_for_status()

            data = response.json()

            for repo in data.get("values", []):

                repositories.append({
                    "name": repo["name"],
                    "slug": repo["slug"],
                    "clone_url": self._get_clone_url(repo)
                })

            if data.get("isLastPage", True):
                break

            start = data.get("nextPageStart", 0)

        self.logger.info(
            f"Discovered {len(repositories)} repositories."
        )

        return repositories

    # ------------------------------------------------------------------

    def _get_clone_url(self, repo):
        """
        Returns the HTTP clone URL for the repository.
        """

        clone_links = repo.get("links", {}).get("clone", [])

        for clone in clone_links:

            if clone.get("name") == "http":
                return clone.get("href")

        raise Exception(
            f"HTTP clone URL not found for repository '{repo['slug']}'"
        )