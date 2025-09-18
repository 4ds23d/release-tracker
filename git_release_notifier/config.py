import yaml
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProjectConfig:
    name: str
    repoUrl: str
    env: Dict[str, str]


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
                env=project_data['env']
            )
            projects.append(project)
    
    return Config(projects=projects)