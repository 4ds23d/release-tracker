from datetime import datetime
from pathlib import Path
from typing import List
from jinja2 import Template
import logging

from .analyzer import ProjectAnalysis


class HTMLReportGenerator:
    """Generates HTML reports for release analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, analyses: List[ProjectAnalysis], output_file: str = "release_report.html", project_configs: List = None):
        """
        Generate HTML report from project analyses.
        
        Args:
            analyses: List of ProjectAnalysis objects
            output_file: Output file path
            project_configs: List of ProjectConfig objects for JIRA base URLs
        """
        template = self._get_template()
        
        # Create a mapping of project names to their configs for JIRA URLs
        project_config_map = {}
        if project_configs:
            project_config_map = {config.name: config for config in project_configs}
        
        # Classify projects as up-to-date or having changes
        projects_with_changes = []
        projects_up_to_date = []
        
        for project in analyses:
            if self._project_has_changes(project):
                projects_with_changes.append(project)
            else:
                projects_up_to_date.append(project)
        
        # Prepare data for template
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'projects_with_changes': projects_with_changes,
            'projects_up_to_date': projects_up_to_date,
            'environment_order': ['DEV', 'TEST', 'PRE', 'PROD'],
            'project_configs': project_config_map
        }
        
        # Render template
        html_content = template.render(**report_data)
        
        # Write to file
        output_path = Path(output_file)
        output_path.write_text(html_content, encoding='utf-8')
        
        self.logger.info(f"Report generated: {output_path.absolute()}")
    
    def _project_has_changes(self, project: ProjectAnalysis) -> bool:
        """
        Determine if a project has any changes to propagate between environments.
        
        A project is considered "up to date" when:
        - All non-PROD environments have no commits
        - All non-PROD environments have no JIRA tickets
        
        Args:
            project: ProjectAnalysis object
            
        Returns:
            True if project has changes, False if up to date
        """
        for env_name, env_data in project.environments.items():
            # Skip PROD as it's the baseline
            if env_name == "PROD":
                continue
                
            # Check if environment has commits or JIRA tickets
            if env_data.commits or env_data.jira_tickets:
                return True
        
        return False
    
    def _get_template(self) -> Template:
        """Get Jinja2 template for HTML report."""
        template_str = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Release Tracker</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }
        .header .timestamp {
            opacity: 0.9;
            font-size: 1.1em;
        }
        .project {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .project-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 20px;
            font-size: 1.5em;
            font-weight: bold;
        }
        .environments {
            display: grid;
            gap: 0;
        }
        .environment {
            border-bottom: 1px solid #eee;
        }
        .environment:last-child {
            border-bottom: none;
        }
        .env-header {
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1em;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .env-header:hover {
            background-color: #f8f9fa;
        }
        .env-dev { background-color: #f8fafe; }
        .env-test { background-color: #fefcf8; }
        .env-pre { background-color: #fcf9fc; }
        .env-prod { background-color: #f9fdf9; }
        
        .env-info {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        .toggle-icons {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .version-commit-badge {
            background: rgba(255,255,255,0.9);
            padding: 6px 12px;
            border-radius: 12px;
            font-family: monospace;
            font-size: 0.9em;
            border: 1px solid rgba(0,0,0,0.15);
            color: #555;
        }
        .commits-count {
            background: #ff5722;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .commits-count:hover {
            background: #e64a19;
        }
        .jira-count {
            background: #0052cc;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .jira-count:hover {
            background: #003d99;
        }
        .jira-tickets {
            padding: 0 20px 20px 20px;
            display: none;
        }
        .jira-tickets.expanded {
            display: block;
        }
        .jira-tickets h4 {
            margin: 0 0 12px 0;
            color: #555;
            font-size: 0.9em;
            padding-top: 10px;
        }
        .jira-ticket {
            display: inline-block;
            background: #0052cc;
            color: white;
            padding: 6px 10px;
            margin: 4px 6px 4px 0;
            border-radius: 4px;
            text-decoration: none;
            font-family: monospace;
            font-size: 0.85em;
            transition: background-color 0.2s;
        }
        .jira-ticket:hover {
            background: #003d99;
            text-decoration: none;
            color: white;
        }
        .commits-list {
            padding: 0 20px 20px 20px;
            display: none;
        }
        .commits-list.expanded {
            display: block;
        }
        .commit-item {
            background: #f8f9fa;
            margin: 8px 0;
            padding: 12px 15px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        .commit-summary {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .commit-meta {
            font-size: 0.85em;
            color: #666;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .commit-id {
            font-family: monospace;
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .no-commits {
            padding: 20px;
            text-align: center;
            color: #666;
            font-style: italic;
        }
        .no-commits-inline {
            color: #666;
            font-style: italic;
            font-size: 0.9em;
            background: rgba(108, 117, 125, 0.1);
            padding: 4px 8px;
            border-radius: 12px;
        }
        .toggle-icon {
            transition: transform 0.2s;
        }
        .toggle-icon.rotated {
            transform: rotate(180deg);
        }
        .up-to-date-section {
            margin-bottom: 30px;
        }
        .up-to-date-header {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            font-size: 1.3em;
            font-weight: bold;
        }
        .up-to-date-projects {
            background: white;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 0;
        }
        .up-to-date-item {
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .up-to-date-item:last-child {
            border-bottom: none;
        }
        .up-to-date-icon {
            font-size: 1.5em;
            color: #28a745;
        }
        .up-to-date-info {
            flex: 1;
        }
        .up-to-date-name {
            font-weight: bold;
            margin-bottom: 4px;
        }
        .up-to-date-status {
            color: #6c757d;
            font-size: 0.9em;
        }
        .changes-section {
            margin-bottom: 30px;
        }
        .changes-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: bold;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Release Tracker</h1>
        <div class="timestamp">Generated: {{ generated_at }}</div>
    </div>

    {% if projects_up_to_date %}
    <div class="up-to-date-section">
        <div class="up-to-date-header">
            ✅ Projects Up to Date
        </div>
        <div class="up-to-date-projects">
            {% for project in projects_up_to_date %}
            <div class="up-to-date-item">
                <div class="up-to-date-icon">📦</div>
                <div class="up-to-date-info">
                    <div class="up-to-date-name">{{ project.project_name }}</div>
                    <div class="up-to-date-status">All environments are synchronized with PROD</div>
                </div>
                <div class="up-to-date-icon">✅</div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    {% if projects_with_changes %}
    <div class="changes-section">
        <div class="changes-header">
            🚀 Projects with Changes to Deploy
        </div>
        
        {% for project in projects_with_changes %}
        <div class="project">
            <div class="project-header">
                📦 {{ project.project_name }}
            </div>
            
            <div class="environments">
                {% for env in environment_order %}
                    {% if env in project.environments %}
                        {% set env_data = project.environments[env] %}
                        <div class="environment">
                            <div class="env-header env-{{ env.lower() }}">
                                <div class="env-info">
                                    <span>{{ env }}</span>
                                    <span class="version-commit-badge">{{ env_data.version }}({{ env_data.commit_id[:8] }})</span>
                                    {% if env_data.commits %}
                                        <span class="commits-count" onclick="toggleCommits('{{ project.project_name }}-{{ env }}')">{{ env_data.commits|length }} commits</span>
                                    {% elif env != 'PROD' %}
                                        <span class="no-commits-inline">No new commits compared to baseline</span>
                                    {% endif %}
                                    {% if env_data.jira_tickets and project.project_name in project_configs and project_configs[project.project_name].jira_base_url %}
                                        <span class="jira-count" onclick="toggleJiraTickets('{{ project.project_name }}-{{ env }}')">{{ env_data.jira_tickets|length }} tickets</span>
                                    {% endif %}
                                </div>
                                <div class="toggle-icons">
                                    {% if env_data.commits %}
                                        <span class="toggle-icon" id="commits-icon-{{ project.project_name }}-{{ env }}" onclick="toggleCommits('{{ project.project_name }}-{{ env }}')">▼</span>
                                    {% endif %}
                                    {% if env_data.jira_tickets and project.project_name in project_configs and project_configs[project.project_name].jira_base_url %}
                                        <span class="toggle-icon" id="jira-icon-{{ project.project_name }}-{{ env }}" onclick="toggleJiraTickets('{{ project.project_name }}-{{ env }}')">🎫</span>
                                    {% endif %}
                                </div>
                            </div>
                            
                            {% if env_data.jira_tickets and project.project_name in project_configs and project_configs[project.project_name].jira_base_url %}
                                <div class="jira-tickets" id="jira-{{ project.project_name }}-{{ env }}">
                                    <h4>🎫 JIRA Tickets:</h4>
                                    {% for ticket in env_data.jira_tickets %}
                                        <a href="{{ project_configs[project.project_name].jira_base_url }}/browse/{{ ticket }}" 
                                           target="_blank" class="jira-ticket">{{ ticket }}</a>
                                    {% endfor %}
                                </div>
                            {% endif %}
                            
                            {% if env_data.commits %}
                                <div class="commits-list" id="commits-{{ project.project_name }}-{{ env }}">
                                    {% for commit in env_data.commits %}
                                        <div class="commit-item">
                                            <div class="commit-summary">{{ commit.summary }}</div>
                                            <div class="commit-meta">
                                                <span class="commit-id">{{ commit.short_id }}</span>
                                                <span>{{ commit.author }}</span>
                                                <span>{{ commit.date[:19] }}</span>
                                            </div>
                                        </div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <script>
        function toggleCommits(id) {
            const commitsList = document.getElementById('commits-' + id);
            const icon = document.getElementById('commits-icon-' + id);
            
            if (commitsList) {
                commitsList.classList.toggle('expanded');
                if (icon) {
                    icon.classList.toggle('rotated');
                }
            }
        }
        
        function toggleJiraTickets(id) {
            const jiraList = document.getElementById('jira-' + id);
            const icon = document.getElementById('jira-icon-' + id);
            
            if (jiraList) {
                jiraList.classList.toggle('expanded');
                if (icon) {
                    // Toggle between ticket emoji and expanded state
                    icon.textContent = jiraList.classList.contains('expanded') ? '🎫▲' : '🎫';
                }
            }
        }
    </script>
</body>
</html>
        '''
        return Template(template_str)