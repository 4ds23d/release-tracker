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
        .search-container {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 10px;
            align-items: center;
        }
        #jira-search {
            padding: 10px 15px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 25px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 1em;
            width: 300px;
            outline: none;
            transition: all 0.3s ease;
        }
        #jira-search::placeholder {
            color: rgba(255,255,255,0.7);
        }
        #jira-search:focus {
            border-color: rgba(255,255,255,0.6);
            background: rgba(255,255,255,0.2);
            box-shadow: 0 0 10px rgba(255,255,255,0.2);
        }
        #clear-search {
            padding: 10px 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 20px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s ease;
            outline: none;
        }
        #clear-search:hover {
            background: rgba(255,255,255,0.2);
            border-color: rgba(255,255,255,0.5);
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
        .search-hidden {
            display: none !important;
        }
        .search-highlight {
            background: #fff3cd !important;
            border-left: 4px solid #ffc107 !important;
            animation: highlightPulse 1.5s ease-in-out;
        }
        @keyframes highlightPulse {
            0% { background: #fff3cd; }
            50% { background: #ffeaa7; }
            100% { background: #fff3cd; }
        }
        .jira-ticket-highlight {
            background: #ffc107 !important;
            color: #212529 !important;
            font-weight: bold;
            animation: ticketPulse 1s ease-in-out;
        }
        @keyframes ticketPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Release Tracker</h1>
        <div class="timestamp">Generated: {{ generated_at }}</div>
        <div class="search-container">
            <input type="text" id="jira-search" placeholder="Search by JIRA ticket (e.g., AUTH-123)" />
            <button id="clear-search">Clear</button>
        </div>
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
        
        function searchJiraTickets() {
            const searchTerm = document.getElementById('jira-search').value.trim().toLowerCase();
            const allProjects = document.querySelectorAll('.project');
            const upToDateSection = document.querySelector('.up-to-date-section');
            const changesSection = document.querySelector('.changes-section');
            
            // Clear previous highlights
            clearHighlights();
            
            if (!searchTerm) {
                // Show all projects when search is empty
                showAllProjects();
                return;
            }
            
            let hasVisibleProjects = false;
            let hasVisibleChangesProjects = false;
            
            // Search in projects with changes
            allProjects.forEach(project => {
                const environments = project.querySelectorAll('.environment');
                let projectHasMatch = false;
                
                environments.forEach(env => {
                    const jiraTickets = env.querySelectorAll('.jira-ticket');
                    let envHasMatch = false;
                    
                    jiraTickets.forEach(ticket => {
                        const ticketText = ticket.textContent.toLowerCase();
                        if (ticketText.includes(searchTerm)) {
                            envHasMatch = true;
                            projectHasMatch = true;
                            ticket.classList.add('jira-ticket-highlight');
                        }
                    });
                    
                    if (envHasMatch) {
                        env.classList.add('search-highlight');
                        // Auto-expand JIRA tickets when found
                        const jiraSection = env.querySelector('.jira-tickets');
                        if (jiraSection && !jiraSection.classList.contains('expanded')) {
                            const envId = env.querySelector('.jira-count')?.getAttribute('onclick')?.match(/toggleJiraTickets\\('([^']+)'\\)/)?.[1];
                            if (envId) {
                                toggleJiraTickets(envId);
                            }
                        }
                    }
                });
                
                if (projectHasMatch) {
                    project.style.display = 'block';
                    hasVisibleProjects = true;
                    hasVisibleChangesProjects = true;
                } else {
                    project.style.display = 'none';
                }
            });
            
            // Hide up-to-date section during search (they don't have JIRA tickets visible)
            if (upToDateSection) {
                upToDateSection.style.display = 'none';
            }
            
            // Show/hide changes section based on results
            if (changesSection) {
                if (hasVisibleChangesProjects) {
                    changesSection.style.display = 'block';
                } else {
                    changesSection.style.display = 'none';
                    // Show "no results" message
                    showNoResultsMessage();
                }
            }
        }
        
        function clearSearch() {
            document.getElementById('jira-search').value = '';
            clearHighlights();
            showAllProjects();
            hideNoResultsMessage();
        }
        
        function clearHighlights() {
            // Remove search highlights
            document.querySelectorAll('.search-highlight').forEach(el => {
                el.classList.remove('search-highlight');
            });
            
            // Remove ticket highlights
            document.querySelectorAll('.jira-ticket-highlight').forEach(el => {
                el.classList.remove('jira-ticket-highlight');
            });
        }
        
        function showAllProjects() {
            // Show all projects
            document.querySelectorAll('.project').forEach(project => {
                project.style.display = 'block';
            });
            
            // Show both sections
            const upToDateSection = document.querySelector('.up-to-date-section');
            const changesSection = document.querySelector('.changes-section');
            
            if (upToDateSection) upToDateSection.style.display = 'block';
            if (changesSection) changesSection.style.display = 'block';
        }
        
        function showNoResultsMessage() {
            // Remove existing no-results message
            hideNoResultsMessage();
            
            // Create and show no results message
            const noResults = document.createElement('div');
            noResults.id = 'no-results-message';
            noResults.style.cssText = `
                text-align: center;
                padding: 40px;
                color: #666;
                font-style: italic;
                font-size: 1.1em;
                background: white;
                border-radius: 10px;
                margin: 20px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            `;
            noResults.innerHTML = '🔍 No JIRA tickets found matching "' + document.getElementById('jira-search').value + '"';
            
            const changesSection = document.querySelector('.changes-section');
            if (changesSection) {
                changesSection.appendChild(noResults);
            }
        }
        
        function hideNoResultsMessage() {
            const noResults = document.getElementById('no-results-message');
            if (noResults) {
                noResults.remove();
            }
        }
        
        // Initialize search functionality when page loads
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('jira-search');
            const clearButton = document.getElementById('clear-search');
            
            // Real-time search as user types
            searchInput.addEventListener('input', searchJiraTickets);
            
            // Clear search button
            clearButton.addEventListener('click', clearSearch);
            
            // Allow Enter key to trigger search
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchJiraTickets();
                }
            });
        });
    </script>
</body>
</html>
        '''
        return Template(template_str)