# Bitbucket Replica Updater

## Overview

The Bitbucket Replica Updater is a Python utility that automates updating Kubernetes deployment YAML files across multiple Bitbucket repositories.

The tool performs the following operations:

1. Connects to Bitbucket Server.
2. Retrieves all repositories from a specified Bitbucket project.
3. Clones each repository.
4. Checks out the `master` branch.
5. Creates a feature branch.
6. Searches recursively for all `*-app.yaml` files.
7. Updates every `replicas` value to `0`.
8. Commits the changes if any files were modified.
9. Generates execution logs and a CSV summary.

---

# Project Structure

```
bitbucket-replica-update/
│
├── config.json
├── requirements.txt
├── config.py
├── logger_manager.py
├── bitbucket_client.py
├── git_manager.py
├── yaml_manager.py
├── replica_update.py
├── README.md
│
├── logs/
│   ├── execution.log
│   └── summary.csv
│
└── repos/
```

---

# Requirements

* Python 3.9+
* Git installed and available in PATH
* Access to Bitbucket Server
* Read permission on the Bitbucket project
* Commit permission on the repositories

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

Update `config.json`.

Example:

```json
{
    "bitbucket": {
        "url": "https://bitbucket.company.com",
        "project_key": "ABCD",
        "username": "your_username",
        "password": "your_password"
    },

    "git": {
        "base_branch": "master",
        "feature_branch": "feature/update-replicas-zero",
        "commit_message": "Update replicas to 0 in *-app.yaml files"
    },

    "directories": {
        "clone_directory": "repos",
        "log_directory": "logs"
    }
}
```

---

# Running the Script

```bash
python replica_update.py
```

---

# Processing Flow

For each repository in the Bitbucket project:

1. Clone the repository.
2. Checkout the `master` branch.
3. Synchronize with the latest `master`.
4. Create the configured feature branch.
5. Search recursively for every `*-app.yaml` file.
6. Update all `replicas` values to `0`.
7. Stage modified files.
8. Commit the changes.
9. Record the result in `summary.csv`.

---

# Example

Before:

```yaml
apiVersion: apps/v1

kind: Deployment

spec:

  replicas: 5
```

After:

```yaml
apiVersion: apps/v1

kind: Deployment

spec:

  replicas: 0
```

---

# Output Files

## execution.log

Location:

```
logs/execution.log
```

Example:

```
2026-06-25 10:15:01 | INFO | Replica Updater Started

2026-06-25 10:15:04 | INFO | Fetching repositories

2026-06-25 10:15:10 | INFO | Processing customer-service

2026-06-25 10:15:18 | INFO | Commit created successfully
```

---

## summary.csv

Location:

```
logs/summary.csv
```

Example:

| Repository       | Status  | Files Found | Files Updated | Replica Values Updated | Commit Created | Remarks                   |
| ---------------- | ------- | ----------- | ------------- | ---------------------- | -------------- | ------------------------- |
| customer-service | SUCCESS | 4           | 4             | 6                      | Yes            | Commit created            |
| payment-service  | SKIPPED | 0           | 0             | 0                      | No             | No *-app.yaml files found |
| auth-service     | FAILED  | 0           | 0             | 0                      | No             | Clone failed              |

---

# Notes

* The script searches the entire repository recursively.
* Only files matching `*-app.yaml` are processed.
* Every `replicas` key is updated to `0`.
* YAML formatting, indentation, comments, and key order are preserved using `ruamel.yaml`.
* Repositories without matching files are skipped.
* Commits are created only when changes are detected.
* The script continues processing other repositories even if one repository fails.

---

# Limitations

* The script does not push feature branches to Bitbucket.
* The script does not create Pull Requests.
* The script assumes Git authentication is already configured for cloning repositories.

---

# Future Enhancements

Possible future enhancements include:

* Push feature branches to Bitbucket.
* Automatically create Pull Requests.
* Support Personal Access Tokens.
* Generate HTML or PDF execution reports.
* Send execution summary via email or Slack notifications.

---

# Author

Internal Automation Utility
