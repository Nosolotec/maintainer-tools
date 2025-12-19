#!/usr/bin/env python3
"""Update last commit SHA in repos YAML file for gitaggregate deployments."""
import os
import sys

import github3
from ruamel.yaml import YAML


def main():
    # Get parameters from environment variables
    github_token = os.environ.get("GITHUB_TOKEN")
    org_name = os.environ.get("INPUT_ORG_NAME")
    repos_yaml = os.environ.get("INPUT_REPOS_YAML")
    default_branch = os.environ.get("INPUT_DEFAULT_BRANCH")

    if not all([github_token, org_name, repos_yaml, default_branch]):
        print("Error: Missing required parameters")
        print(f"  GITHUB_TOKEN: {'set' if github_token else 'missing'}")
        print(f"  INPUT_ORG_NAME: {org_name or 'missing'}")
        print(f"  INPUT_REPOS_YAML: {repos_yaml or 'missing'}")
        print(f"  INPUT_DEFAULT_BRANCH: {default_branch or 'missing'}")
        sys.exit(1)

    # Setup YAML parser
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Load repos YAML file
    with open(repos_yaml) as f:
        data = yaml.load(f)

    # Connect to GitHub
    github = github3.login(token=github_token)
    org = github.organization(org_name)

    updated_repos = []

    for repo in org.repositories(type="all"):
        # Skip localization repos
        if repo.name.startswith("l10n"):
            continue
        # Skip core Odoo repos
        if repo.name in ["odoo", "enterprise"]:
            continue

        repo_info = data.get(f"./{repo.name}")
        if not repo_info:
            continue

        # Skip OCA repos
        origin_url = repo_info.get("remotes", {}).get("origin", "")
        if "OCA" in origin_url or "/oca/" in origin_url.lower():
            continue

        # Check if default branch exists
        all_branches = [branch.name for branch in repo.branches()]
        if default_branch not in all_branches:
            continue

        # Update merges with last commit SHA
        merges = repo_info.get("merges", [])
        for idx, merge in enumerate(merges):
            if "origin " not in merge:
                continue
            if merge == "origin $ODOO_VERSION":
                continue
            # Skip pull request references
            if "refs/pull/" in merge:
                continue

            last_commit = repo.branch(default_branch).commit
            new_merge = f"origin {last_commit.sha}"

            if merges[idx] != new_merge:
                merges[idx] = new_merge
                updated_repos.append(repo.name)
                print(f"Updated: {repo.name} -> {last_commit.sha}")

    # Save updated YAML
    with open(repos_yaml, "w") as f:
        yaml.dump(data, f)

    # Set output for GitHub Actions
    if updated_repos:
        print(f"\nTotal repositories updated: {len(updated_repos)}")
        # Write to GITHUB_OUTPUT if available
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"updated_count={len(updated_repos)}\n")
                f.write(f"updated_repos={','.join(updated_repos)}\n")
    else:
        print("\nNo repositories were updated")


if __name__ == "__main__":
    main()
