#!/usr/bin/env python3
"""Update last commit SHA in repos YAML file for gitaggregate deployments."""
import os
import re
import sys

import github3
from ruamel.yaml import YAML

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_COMMITS = 500


def get_commits_between(repo, old_sha, new_sha):
    """Return list of commits (oldest→newest) between old_sha and new_sha.

    Tries the compare API first; if it returns no commits falls back to
    iterating repo.commits() from new_sha until old_sha is found.
    """
    # --- Try compare API ---
    try:
        comparison = repo.compare_commits(old_sha, new_sha)
        if comparison is not None:
            commits = list(comparison.commits)
            if commits:
                return list(reversed(commits))
            print(f"  compare_commits returned 0 commits, falling back to iteration")
        else:
            print(f"  compare_commits returned None, falling back to iteration")
    except Exception as e:
        print(f"  compare_commits raised {e!r}, falling back to iteration")

    # --- Fallback: iterate commits newest→oldest, stop at old_sha ---
    commits = []
    for commit in repo.commits(sha=new_sha):
        if commit.sha == old_sha:
            break
        commits.append(commit)
        if len(commits) >= MAX_COMMITS:
            print(f"  Reached {MAX_COMMITS} commits limit, stopping iteration")
            break
    return commits  # already newest→oldest; caller uses them in this order


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
    commit_messages = []

    for repo in org.repositories(type="all"):
        # Skip localization repos
        if repo.name.startswith("l10n"):
            continue
        # Skip core Odoo repos
        # if repo.name in ["odoo", "enterprise"]:
        #     continue

        repo_info = data.get(f"./{repo.name}") or data.get(
            f"./{repo.name.replace('_', '-')}"
        )
        if not repo_info:
            continue

        # # Skip OCA repos
        # origin_url = repo_info.get("remotes", {}).get("origin", "")
        # if "OCA" in origin_url or "/oca/" in origin_url.lower():
        #     continue

        # Determine the effective branch from target in repos.yaml
        target = repo_info.get("target", "")
        if target:
            # target format: "origin <branch>" e.g. "origin 17.0-farmamia"
            target_branch = target.split()[-1] if target.split() else default_branch
            # If target uses $ODOO_VERSION, resolve to default_branch
            if target_branch == "$ODOO_VERSION":
                target_branch = default_branch
        else:
            target_branch = default_branch

        # Check if target branch exists
        all_branches = [branch.name for branch in repo.branches()]
        if target_branch not in all_branches:
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

            last_commit = repo.branch(target_branch).commit
            new_merge = f"origin {last_commit.sha}"

            if merges[idx] != new_merge:
                old_sha = merge.split()[1] if len(merge.split()) == 2 else None
                merges[idx] = new_merge
                updated_repos.append(repo.name)
                print(f"Updated: {repo.name} -> {last_commit.sha}")

                # Get all commits between old and new SHA
                last_commit_msg = last_commit.commit.message.split("\n")[0] if last_commit.commit.message else "No message"
                last_commit_url = f"https://github.com/{org_name}/{repo.name}/commit/{last_commit.sha}"
                if old_sha and SHA_RE.match(old_sha):
                    commits = get_commits_between(repo, old_sha, last_commit.sha)
                    repo_header = f"### {repo.name} ({len(commits)} commit{'s' if len(commits) != 1 else ''})"
                    commit_messages.append(repo_header)
                    if commits:
                        display_commits = commits[:50]
                        for c in display_commits:
                            msg = c.commit.message.split("\n")[0] if c.commit.message else "No message"
                            url = f"https://github.com/{org_name}/{repo.name}/commit/{c.sha}"
                            commit_messages.append(f"- {msg} ([{c.sha[:7]}]({url}))")
                        if len(commits) > 50:
                            commit_messages.append(f"- _...and {len(commits) - 50} more commits_")
                    else:
                        commit_messages.append(f"- {last_commit_msg} ([{last_commit.sha[:7]}]({last_commit_url}))")
                else:
                    repo_header = f"### {repo.name}"
                    commit_messages.append(repo_header)
                    commit_messages.append(f"- {last_commit_msg} ([{last_commit.sha[:7]}]({last_commit_url}))")

    # Save updated YAML
    with open(repos_yaml, "w") as f:
        yaml.dump(data, f)

    # Set output for GitHub Actions
    if updated_repos:
        print(f"\nTotal repositories updated: {len(updated_repos)}")
        print("\nCommit messages:")
        for msg in commit_messages:
            print(msg)
        # Write to GITHUB_OUTPUT if available
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"updated_count={len(updated_repos)}\n")
                f.write(f"updated_repos={','.join(updated_repos)}\n")
                # Write commit messages as multiline output
                f.write("commit_messages<<EOF\n")
                f.write("\n".join(commit_messages))
                f.write("\nEOF\n")
    else:
        print("\nNo repositories were updated")


if __name__ == "__main__":
    main()
