import click
import git
import os
import multiprocessing


class Jit(object):

	def __init__(self):
		self.root = self.get_root(os.getcwd())
		self.root_files = []
		if not self.root:
			print("Could not find a root directory.")
			return

		self.root_files = os.listdir(self.root)
		return

	def get_root(self, dir):
		if self.is_repo(dir):
			return os.path.dirname(dir)
		elif len(dir) <= 1:
			return False
		else:
			return self.get_root(os.path.dirname(dir))

	def get_repo_root(self, repo_name):
		return self.root + '/' + repo_name

	@staticmethod
	def get_repo_name(repo):
		return os.path.basename(repo.working_dir)

	def get_repos(self):
		repos = []
		for dir in self.root_files:
			dir_path = self.get_repo_root(dir)
			if self.is_repo(dir_path):
				repos.append(git.Repo(dir_path))

		return repos

	@staticmethod
	def is_repo(dir_path):
		return os.path.isdir(dir_path + '/.git')

	@staticmethod
	def get_branches(repo):
		branches = []
		for branch in repo.branches:
			if branch.name != 'master':
				branches.append(branch)

		return branches

	def format_active_branch_output(self, repo):
		return self.get_repo_name(repo).ljust(35) + repo.active_branch.name

	def get_dirty_repos(self):
		return [repo for repo in self.get_repos() if repo.is_dirty()]

	def handle_dirty_repos(self, dirty_repos = None):
		if dirty_repos is None:
			dirty_repos = self.get_dirty_repos()

		if dirty_repos:
			print("Please commit or stash your changes in the following repos.")
			for repo in dirty_repos:
				print(self.format_active_branch_output(repo))
			return True
		return False;

	def get_relevant_repos(self, branch_name):
		relevant_repos = []
		for repo in self.get_repos():
			for branch in repo.branches:
				if branch.name == branch_name:
					relevant_repos.append((repo, branch_name))

		return relevant_repos

	def checkout_relevant_repos(self, branch_name):
		with multiprocessing.Pool(10) as p:
			p.starmap(self.checkout_branch, self.get_relevant_repos(branch_name))

	def checkout_branch(self, repo, branch_name):
		repo.git.checkout(branch_name)
		print(self.format_active_branch_output(repo))

	def all_to_master(self):
		if not self.handle_dirty_repos():
			for repo in self.get_repos():
				repo.heads.master.checkout()

	def pull_all(self):
		if not self.handle_dirty_repos():
			with multiprocessing.Pool(10) as p:
				p.map(self.pull_one, self.get_repos())

	def pull_one(self, repo):
		try:
			repo.remotes.origin.pull()
			click.echo("Pulled %s" % self.get_repo_name(repo))
		except:
			click.echo("Could not pull %s" % self.get_repo_name(repo))

	def display_user_repos(self):
		for repo in self.get_repos():
			if (len(repo.branches) > 1):
				print(self.get_repo_name(repo))
			for branch in self.get_branches(repo):
				print(branch.name.ljust(5))

	def display_current_branches(self):
		repos = self.get_repos()
		for repo in repos:
			print(self.format_active_branch_output(repo))

	def display_dirty_repos(self):
		for repo in self.get_dirty_repos():
			print(self.format_active_branch_output(repo))

	def display_relevant_repos(self, branch_name):
		for repo, _ in self.get_relevant_repos(branch_name):
			print(self.format_active_branch_output(repo))


@click.group()
def cli():
	"""jit allows you to interact with all git repositories within a directory in bulk."""
	pass


@cli.command()
def	all():
	"""Display all current branches."""
	jit = Jit()
	jit.display_current_branches()


@cli.command()
def mine():
	"""Display all branches for all repos."""
	jit = Jit()
	jit.display_user_repos()


@cli.command()
def dirty():
	"""Display all repos with uncommitted changes."""
	jit = Jit()
	jit.display_dirty_repos()


@cli.command()
def master():
	"""Checkout master branch on all repos."""
	jit = Jit()
	jit.all_to_master()


@cli.command()
def pull():
	"""Pull from remote origin on all repos."""
	jit = Jit()
	jit.pull_all()


@click.command()
@click.argument('branch')
def show(branch):
	"""Show all repos that contain specified branch name."""
	jit = Jit()
	jit.display_relevant_repos(branch)


@click.command()
@click.argument('branch')
def co(branch):
	"""Checkout specified branch in all repos where it exists."""
	jit = Jit()
	jit.checkout_relevant_repos(branch)


cli.add_command(show)
cli.add_command(co)
