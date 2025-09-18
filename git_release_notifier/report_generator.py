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
    
    def generate_report(self, analyses: List[ProjectAnalysis], output_file: str = "release_report.html"):
        """
        Generate HTML report from project analyses.
        
        Args:
            analyses: List of ProjectAnalysis objects
            output_file: Output file path
        """
        template = self._get_template()
        
        # Prepare data for template
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'projects': analyses,
            'environment_order': ['DEV', 'TEST', 'PRE', 'PROD']
        }
        
        # Render template
        html_content = template.render(**report_data)
        
        # Write to file
        output_path = Path(output_file)
        output_path.write_text(html_content, encoding='utf-8')
        
        self.logger.info(f"Report generated: {output_path.absolute()}")
    
    def _get_template(self) -> Template:
        """Get Jinja2 template for HTML report."""
        template_str = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Release Report</title>
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
        .env-dev { background-color: #e3f2fd; }
        .env-test { background-color: #fff3e0; }
        .env-pre { background-color: #f3e5f5; }
        .env-prod { background-color: #e8f5e8; }
        
        .env-info {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        .version-badge {
            background: rgba(255,255,255,0.8);
            padding: 5px 12px;
            border-radius: 15px;
            font-family: monospace;
            font-size: 0.9em;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .commit-badge {
            background: rgba(255,255,255,0.6);
            padding: 4px 8px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 0.8em;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .commits-count {
            background: #ff5722;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
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
        .toggle-icon {
            transition: transform 0.2s;
        }
        .toggle-icon.rotated {
            transform: rotate(180deg);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Release Report</h1>
        <div class="timestamp">Generated: {{ generated_at }}</div>
    </div>

    {% for project in projects %}
    <div class="project">
        <div class="project-header">
            📦 {{ project.project_name }}
        </div>
        
        <div class="environments">
            {% for env in environment_order %}
                {% if env in project.environments %}
                    {% set env_data = project.environments[env] %}
                    <div class="environment">
                        <div class="env-header env-{{ env.lower() }}" onclick="toggleCommits('{{ project.project_name }}-{{ env }}')">
                            <div class="env-info">
                                <span>{{ env }}</span>
                                <span class="version-badge">{{ env_data.version }}</span>
                                <span class="commit-badge">{{ env_data.commit_id[:8] }}</span>
                                {% if env_data.commits %}
                                    <span class="commits-count">{{ env_data.commits|length }} new commits</span>
                                {% endif %}
                            </div>
                            {% if env_data.commits %}
                                <span class="toggle-icon" id="icon-{{ project.project_name }}-{{ env }}">▼</span>
                            {% endif %}
                        </div>
                        
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
                        {% elif env != 'PROD' %}
                            <div class="no-commits">No new commits compared to baseline</div>
                        {% endif %}
                    </div>
                {% endif %}
            {% endfor %}
        </div>
    </div>
    {% endfor %}

    <script>
        function toggleCommits(id) {
            const commitsList = document.getElementById('commits-' + id);
            const icon = document.getElementById('icon-' + id);
            
            if (commitsList) {
                commitsList.classList.toggle('expanded');
                if (icon) {
                    icon.classList.toggle('rotated');
                }
            }
        }
    </script>
</body>
</html>
        '''
        return Template(template_str)