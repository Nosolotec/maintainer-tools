"""UPDATE all addons project.
"""
import click
from ruamel.yaml import YAML
from . import github_login


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
        if repo.name in ["odoo", "enterprise"]:
            continue
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
                last_commit = repo.branch(default_branch).commit
                if merge == "origin $ODOO_VERSION":
                    continue
                repo_info.get("merges")[indx] = f"origin {last_commit.sha}"
                print(f'Repositorio: {repo.name}')
                print(f'Ultimo Commit: {last_commit.sha}')
    with open(repos_yaml, "w") as f:
        yaml.dump(data, f)


if __name__ == '__main__':
   main()