import git


class GitPythonUtilities:
    def __init__(self) -> None:
        pass

    def router(self, cfg):
        repos = cfg.repos.copy()

        for repo in repos:
            repo_cfg = cfg.common_cfg.copy()
            repo_cfg.update(repo)
            repo = git.Repo(repo_cfg["io"])
            if repo_cfg["status"]:
                self.get_status(repo)
            if repo_cfg["commit"]:
                self.commit(repo)
            if repo_cfg["push"]:
                self.push(repo)

    def get_status(self, repo):
        status = repo.git.status()
        print(status)

    def commit(self, repo):
        self.add(repo)
        pass

    def add(self, repo):
        repo.index.add()

    def push(self, repo):
        print(repo.remotes.origin.push())
