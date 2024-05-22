import git
import uuid
from models.branch import Branch
from composer import Composer
from sqlalchemy import desc
from main import session

class BranchManager:

    def __init__(self, repo_path=".", run=True, disposable=True):
        self.repo = git.Repo(repo_path)
        self.branch = self.get_or_create_open_branch()
        self.disposable = disposable

        self.composers = {}

        if run:
            self.checkout_branch()

    def edit_file(self, filename, current_code, new_code):
        if not self.composers.get(filename):
            self.composers[filename] = Composer(filename)

        comp = self.composers[filename]

        comp.modify(current_code, new_code)

        comp.recompose()

    def close(self):
        if self.disposable:
            # Revert to main branch, deleting this one and all changes made
            self.repo.git.checkout('main')  # Assuming the main branch is named 'main'
            self.repo.git.branch('-D', self.branch.name)  # Delete the branch 
        else:
            # Commit this branch, merging it into main
            self.repo.git.checkout('main')  # Switch to the main branch
            self.repo.git.merge(self.branch.name)  # Merge the branch into main
            self.repo.git.branch('-D', self.branch.name)  # Delete the branch

        self.branch.status = 'closed'
        session.commit()

    def get_or_create_open_branch(self):
        # Find the newest 'open' branch
        newest_open_branch = session.query(Branch).filter_by(status='open').order_by(desc(Branch.id)).first()

        if newest_open_branch:
            return newest_open_branch

        # Create a new 'open' branch with a unique name
        unique_id = uuid.uuid4().hex[:8]
        new_branch_name = f"feature-branch-{unique_id}"
        new_branch = Branch(name=new_branch_name, status='open')

        session.add(new_branch)
        session.commit()

        return new_branch

    def checkout_branch(self):
        branch_name = self.branch.name

        # Check if branch already exists in repo
        branch_exists = branch_name in self.repo.branches

        # Checkout the branch if it exists, otherwise create and checkout new branch
        if branch_exists:
            self.repo.git.checkout(branch_name)
        else:
            self.repo.git.checkout('HEAD', b=branch_name)
