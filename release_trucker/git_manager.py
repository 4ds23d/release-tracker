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
    
    def get_commits_between(self, repo: Repo, from_commit: str, to_commit: str, expand_merges: bool = True) -> List[dict]:
        """
        Get commit messages between two commits, optionally expanding merge commits.
        
        Args:
            repo: Git repository object
            from_commit: Starting commit ID (exclusive)
            to_commit: Ending commit ID (inclusive)
            expand_merges: Whether to expand merge commits to show underlying commits
            
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
            
            if expand_merges:
                commit_info = self._expand_merge_commits(repo, commit_info, from_commit)
            
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
    
    def _expand_merge_commits(self, repo: Repo, commits: List[dict], baseline_commit: str) -> List[dict]:
        """
        Expand merge commits to show the underlying commits that were merged.
        
        Args:
            repo: Git repository object
            commits: List of commit dictionaries
            baseline_commit: The baseline commit to compare against
            
        Returns:
            Expanded list of commit information dictionaries
        """
        expanded_commits = []
        seen_commits = set()
        
        # First, add all original commits to seen set to avoid duplicates
        for commit_info in commits:
            seen_commits.add(commit_info['id'])
        
        for commit_info in commits:
            # Always add the original commit
            expanded_commits.append(commit_info)
            
            try:
                commit = repo.commit(commit_info['id'])
                
                # Check if this is a merge commit (has more than one parent)
                if len(commit.parents) > 1:
                    self.logger.debug(f"Expanding merge commit {commit.hexsha[:8]}: {commit.summary}")
                    
                    # For merge commits, get all commits from the merged branch(es)
                    # that are not already in the baseline
                    for parent in commit.parents[1:]:  # Skip first parent (main branch)
                        try:
                            # Get commits from baseline to this parent
                            parent_range = f"{baseline_commit}..{parent.hexsha}"
                            parent_commits = list(repo.iter_commits(parent_range))
                            
                            # Add commits that haven't been seen yet
                            for parent_commit in reversed(parent_commits):  # Reverse to maintain chronological order
                                if parent_commit.hexsha not in seen_commits:
                                    parent_commit_info = {
                                        'id': parent_commit.hexsha,
                                        'short_id': parent_commit.hexsha[:8],
                                        'message': parent_commit.message.strip(),
                                        'author': str(parent_commit.author),
                                        'date': parent_commit.committed_datetime.isoformat(),
                                        'summary': parent_commit.summary,
                                        'is_merged_commit': True  # Mark as merged commit for identification
                                    }
                                    expanded_commits.append(parent_commit_info)
                                    seen_commits.add(parent_commit.hexsha)
                                    
                        except GitCommandError as e:
                            self.logger.debug(f"Could not expand merge parent {parent.hexsha[:8]}: {e}")
                            continue
                            
            except Exception as e:
                self.logger.debug(f"Error expanding commit {commit_info['id'][:8]}: {e}")
                continue
        
        # Sort by date to maintain chronological order
        try:
            expanded_commits.sort(key=lambda x: x['date'])
        except Exception as e:
            self.logger.debug(f"Could not sort commits by date: {e}")
        
        self.logger.debug(f"Expanded {len(commits)} commits to {len(expanded_commits)} commits")
        return expanded_commits

    def cleanup_repos(self):
        """Remove all cloned repositories."""
        if self.repos_dir.exists():
            shutil.rmtree(self.repos_dir)
            self.repos_dir.mkdir(exist_ok=True)