import pytest
import tempfile
import yaml
from pathlib import Path

from release_trucker.config import load_config, Config, ProjectConfig


class TestConfig:
    
    def create_test_config(self, config_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
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
    
    def test_load_config_with_version_fallback_disabled(self):
        config_data = {
            'projects': [
                {
                    'name': 'fallback-disabled-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {
                        'PROD': 'https://prod.example.com'
                    },
                    'use_version_fallback': False
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
            assert project.name == 'fallback-disabled-project'
            assert project.use_version_fallback is False
        finally:
            Path(config_path).unlink()
    
    def test_load_config_version_fallback_default_true(self):
        config_data = {
            'projects': [
                {
                    'name': 'fallback-default-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {
                        'PROD': 'https://prod.example.com'
                    }
                    # No use_version_fallback specified, should default to True
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
            assert project.name == 'fallback-default-project'
            assert project.use_version_fallback is True  # Should default to True
        finally:
            Path(config_path).unlink()
    
    def test_project_config_creation_with_version_fallback_options(self):
        # Test with version fallback disabled
        project1 = ProjectConfig(
            name='fallback-disabled',
            repoUrl='https://github.com/test/repo.git',
            env={'PROD': 'https://prod.example.com'},
            use_version_fallback=False
        )
        
        assert project1.use_version_fallback is False
        
        # Test with version fallback enabled (default)
        project2 = ProjectConfig(
            name='fallback-enabled',
            repoUrl='https://github.com/test/repo.git',
            env={'PROD': 'https://prod.example.com'}
        )
        
        assert project2.use_version_fallback is True
    
    def test_load_config_with_jira_base_url(self):
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'},
                    'jira_base_url': 'https://company.atlassian.net'
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        try:
            config = load_config(config_file)
            
            assert len(config.projects) == 1
            assert config.projects[0].jira_base_url == 'https://company.atlassian.net'
        finally:
            Path(config_file).unlink()
    
    def test_load_config_jira_base_url_default_none(self):
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        try:
            config = load_config(config_file)
            
            assert len(config.projects) == 1
            assert config.projects[0].jira_base_url is None
        finally:
            Path(config_file).unlink()
    
    def test_project_config_creation_with_jira_options(self):
        project = ProjectConfig(
            name="test-project",
            repoUrl="https://github.com/test/repo.git",
            env={"PROD": "https://prod.example.com"},
            jira_base_url="https://mycompany.atlassian.net"
        )
        
        assert project.name == "test-project"
        assert project.jira_base_url == "https://mycompany.atlassian.net"