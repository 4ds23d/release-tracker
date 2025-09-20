import yaml
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProjectConfig:
    name: str
    repoUrl: str
    env: Dict[str, str]
    verify_ssl: bool = True
    use_version_fallback: bool = True
    jira_base_url: str = None
    main_branch: str = "main"


@dataclass
class Config:
    projects: List[ProjectConfig]


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    
    projects = []
    if data and 'projects' in data:
        for project_data in data['projects']:
            project = ProjectConfig(
                name=project_data['name'],
                repoUrl=project_data['repoUrl'],
                env=project_data['env'],
                verify_ssl=project_data.get('verify_ssl', True),
                use_version_fallback=project_data.get('use_version_fallback', True),
                jira_base_url=project_data.get('jira_base_url'),
                main_branch=project_data.get('main_branch', 'main')
            )
            projects.append(project)
    
    return Config(projects=projects)