"""UPDATE all addons project.
"""
import re

import click
from ruamel.yaml import YAML

from . import github_login

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@click.command("Update all repositories")
@click.argument("org-name")
@click.option(
    "--repos_yaml",
    "repos_yaml",
)
@click.option(
    "--default-branch",
    "default_branch",
)
def main(org_name, repos_yaml, default_branch=None):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)  # Fuerza indentación de listas
    with open(repos_yaml) as f:
        data = yaml.load(f)
    # Connect to GitHub
    github = github_login.login()
    org = github.organization(org_name)
    for repo in org.repositories(type="all"):
        if repo.name.startswith("l10n"):
            continue
        # if repo.name in ["odoo", "enterprise"]:
        #     continue
        repo_info = data.get(f"./{repo.name}")
        if not repo_info:
            continue
        # Saltar repos de la OCA
        origin_url = repo_info.get("remotes", {}).get("origin", "")
        if "OCA" in origin_url or "/oca/" in origin_url:
            continue
        all_branches = []
        for branch in repo.branches():
            all_branches.append(branch.name)
        if default_branch not in all_branches:
            continue
        for indx, merge in enumerate(repo_info.get("merges")):
            if "origin " in merge:
                if merge == "origin $ODOO_VERSION":
                    continue
                # No actualizar referencias a pull requests (refs/pull/*/head)
                if "refs/pull/" in merge:
                    continue
                last_commit = repo.branch(default_branch).commit
                new_merge = f"origin {last_commit.sha}"
                if repo_info.get("merges")[indx] == new_merge:
                    continue
                old_sha = merge.split()[1] if len(merge.split()) == 2 else None
                repo_info.get("merges")[indx] = new_merge
                print(f'Repositorio: {repo.name}')
                print(f'Ultimo Commit: {last_commit.sha}')
                # Listar todos los commits entre el SHA anterior y el nuevo
                if old_sha and SHA_RE.match(old_sha):
                    try:
                        comparison = repo.compare_commits(old_sha, last_commit.sha)
                        commits = list(comparison.commits)
                        print(f'  Commits nuevos: {len(commits)}')
                        for c in reversed(commits):
                            msg = c.commit.message.split("\n")[0] if c.commit.message else "Sin mensaje"
                            url = f"https://github.com/{org_name}/{repo.name}/commit/{c.sha}"
                            print(f'  - {msg} ({url})')
                    except Exception as e:
                        print(f'  (No se pudieron obtener commits intermedios: {e})')
    with open(repos_yaml, "w") as f:
        yaml.dump(data, f)


if __name__ == '__main__':
   main()