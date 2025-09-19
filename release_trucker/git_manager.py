import os
import shutil
from pathlib import Path
from git import Repo, GitCommandError
from typing import List, Optional
import logging


class GitManager:
    """Manages git repository operations including cloning and updating."""
    
    def __init__(self, repos_dir: str = "repos"):
        self.repos_dir = Path(repos_dir)
        self.repos_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def get_or_update_repo(self, repo_url: str, project_name: str) -> Optional[Repo]:
        """
        Clone repository if it doesn't exist, otherwise update it.
        
        Args:
            repo_url: Git repository URL
            project_name: Name of the project (used as directory name)
            
        Returns:
            Git Repo object or None if operation fails
        """
        repo_path = self.repos_dir / project_name
        
        try:
            if repo_path.exists():
                self.logger.info(f"Updating existing repository: {project_name}")
                repo = Repo(repo_path)
                origin = repo.remotes.origin
                origin.fetch()
                # Reset to latest origin/main or origin/master
                try:
                    repo.heads.main.checkout()
                    repo.heads.main.reset('origin/main', index=True, working_tree=True)
                except:
                    try:
                        repo.heads.master.checkout()
                        repo.heads.master.reset('origin/master', index=True, working_tree=True)
                    except:
                        self.logger.warning(f"Could not reset to main/master for {project_name}")
                
                return repo
            else:
                self.logger.info(f"Cloning repository: {project_name}")
                repo = Repo.clone_from(repo_url, repo_path)
                return repo
                
        except GitCommandError as e:
            self.logger.error(f"Git operation failed for {project_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error managing repository {project_name}: {e}")
            return None
    
    def get_commits_between(self, repo: Repo, from_commit: str, to_commit: str) -> List[dict]:
        """
        Get commit messages between two commits.
        
        Args:
            repo: Git repository object
            from_commit: Starting commit ID (exclusive)
            to_commit: Ending commit ID (inclusive)
            
        Returns:
            List of commit information dictionaries
        """
        try:
            # Get commits that are in to_commit but not in from_commit
            commit_range = f"{from_commit}..{to_commit}"
            commits = list(repo.iter_commits(commit_range))
            
            commit_info = []
            for commit in commits:
                commit_info.append({
                    'id': commit.hexsha,
                    'short_id': commit.hexsha[:8],
                    'message': commit.message.strip(),
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat(),
                    'summary': commit.summary
                })
            
            return commit_info
            
        except GitCommandError as e:
            self.logger.error(f"Failed to get commits between {from_commit} and {to_commit}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error getting commits: {e}")
            return []
    
    def commit_exists(self, repo: Repo, commit_id: str) -> bool:
        """Check if a commit exists in the repository."""
        try:
            repo.commit(commit_id)
            return True
        except:
            return False
    
    def resolve_commit_reference(self, repo: Repo, reference: str) -> Optional[str]:
        """
        Resolve a git reference (commit, tag, branch) to a commit ID.
        
        Args:
            repo: Git repository object
            reference: Git reference (commit hash, tag, or branch name)
            
        Returns:
            Resolved commit ID or None if reference cannot be resolved
        """
        try:
            # Try to resolve the reference to a commit
            commit = repo.commit(reference)
            return commit.hexsha
        except Exception as e:
            self.logger.debug(f"Could not resolve reference '{reference}': {e}")
            return None
    
    def tag_exists(self, repo: Repo, tag_name: str) -> bool:
        """Check if a tag exists in the repository."""
        try:
            # Check if tag exists in repository
            for tag in repo.tags:
                if tag.name == tag_name:
                    return True
            return False
        except Exception as e:
            self.logger.debug(f"Error checking tag '{tag_name}': {e}")
            return False
    
    def cleanup_repos(self):
        """Remove all cloned repositories."""
        if self.repos_dir.exists():
            shutil.rmtree(self.repos_dir)
            self.repos_dir.mkdir(exist_ok=True)