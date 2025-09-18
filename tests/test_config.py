import pytest
import tempfile
import yaml
from pathlib import Path

from git_release_notifier.config import load_config, Config, ProjectConfig


class TestConfig:
    
    def test_load_config_valid(self):
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {
                        'PROD': 'https://prod.example.com',
                        'PRE': 'https://pre.example.com',
                        'TEST': 'https://test.example.com',
                        'DEV': 'https://dev.example.com'
                    }
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            assert isinstance(config, Config)
            assert len(config.projects) == 1
            
            project = config.projects[0]
            assert isinstance(project, ProjectConfig)
            assert project.name == 'test-project'
            assert project.repoUrl == 'https://github.com/test/repo.git'
            assert project.env['PROD'] == 'https://prod.example.com'
            assert project.env['DEV'] == 'https://dev.example.com'
        finally:
            Path(config_path).unlink()
    
    def test_load_config_multiple_projects(self):
        config_data = {
            'projects': [
                {
                    'name': 'project1',
                    'repoUrl': 'https://github.com/test/repo1.git',
                    'env': {'PROD': 'https://prod1.com'}
                },
                {
                    'name': 'project2',
                    'repoUrl': 'https://github.com/test/repo2.git',
                    'env': {'PROD': 'https://prod2.com'}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            assert len(config.projects) == 2
            assert config.projects[0].name == 'project1'
            assert config.projects[1].name == 'project2'
        finally:
            Path(config_path).unlink()
    
    def test_load_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config('nonexistent.yaml')
    
    def test_load_config_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content:')
            config_path = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                load_config(config_path)
        finally:
            Path(config_path).unlink()
    
    def test_project_config_creation(self):
        project = ProjectConfig(
            name='test-project',
            repoUrl='https://github.com/test/repo.git',
            env={
                'PROD': 'https://prod.example.com',
                'DEV': 'https://dev.example.com'
            }
        )
        
        assert project.name == 'test-project'
        assert project.repoUrl == 'https://github.com/test/repo.git'
        assert len(project.env) == 2
        assert project.env['PROD'] == 'https://prod.example.com'
    
    def test_config_creation(self):
        project1 = ProjectConfig('proj1', 'url1', {'PROD': 'prod1'})
        project2 = ProjectConfig('proj2', 'url2', {'PROD': 'prod2'})
        
        config = Config(projects=[project1, project2])
        
        assert len(config.projects) == 2
        assert config.projects[0].name == 'proj1'
        assert config.projects[1].name == 'proj2'
    
    def test_load_config_with_ssl_verification_disabled(self):
        config_data = {
            'projects': [
                {
                    'name': 'insecure-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {
                        'PROD': 'https://prod.example.com'
                    },
                    'verify_ssl': False
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            assert len(config.projects) == 1
            project = config.projects[0]
            assert project.name == 'insecure-project'
            assert project.verify_ssl is False
        finally:
            Path(config_path).unlink()
    
    def test_load_config_ssl_verification_default_true(self):
        config_data = {
            'projects': [
                {
                    'name': 'secure-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {
                        'PROD': 'https://prod.example.com'
                    }
                    # No verify_ssl specified, should default to True
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            assert len(config.projects) == 1
            project = config.projects[0]
            assert project.name == 'secure-project'
            assert project.verify_ssl is True  # Should default to True
        finally:
            Path(config_path).unlink()
    
    def test_project_config_creation_with_ssl_options(self):
        # Test with SSL verification disabled
        project1 = ProjectConfig(
            name='insecure-project',
            repoUrl='https://github.com/test/repo.git',
            env={'PROD': 'https://prod.example.com'},
            verify_ssl=False
        )
        
        assert project1.verify_ssl is False
        
        # Test with SSL verification enabled (default)
        project2 = ProjectConfig(
            name='secure-project',
            repoUrl='https://github.com/test/repo.git',
            env={'PROD': 'https://prod.example.com'}
        )
        
        assert project2.verify_ssl is True