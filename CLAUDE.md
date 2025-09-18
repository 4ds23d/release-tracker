# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Git Release Notifier is a Python command-line application that analyzes deployment states across different environments (DEV, TEST, PRE, PROD). It fetches version information from Spring Boot actuator endpoints, compares git commits between environments, and generates HTML reports showing deployment differences.

## Development Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Install in Development Mode
```bash
pip install -e .
```

### Run the Application
```bash
# Using the main script
python main.py --config config.yaml --output report.html

# Using the installed command
git-release-notifier --config config.yaml --output report.html
```

### Configuration
Edit `config.yaml` to configure projects and their environment URLs. Each project needs:
- `name`: Project identifier
- `repoUrl`: Git repository URL  
- `env`: Dictionary with PROD, PRE, TEST, DEV environment URLs

## Architecture

### Core Components

- **config.py**: Configuration management using YAML
- **api_client.py**: REST API client for Spring Boot actuator/info endpoints
- **git_manager.py**: Git repository operations (clone, update, commit comparison)
- **analyzer.py**: Main analysis logic comparing commits between environments
- **report_generator.py**: HTML report generation using Jinja2 templates
- **cli.py**: Click-based command-line interface

### Analysis Logic

The application follows this hierarchy for commit comparison:
- PROD is the baseline (shows no commits)
- PRE shows commits not yet in PROD
- TEST shows commits not yet in PRE  
- DEV shows commits not yet in TEST

### Dependencies

- `requests`: HTTP client for actuator endpoints
- `GitPython`: Git repository operations
- `click`: Command-line interface
- `pyyaml`: Configuration file parsing
- `jinja2`: HTML template rendering