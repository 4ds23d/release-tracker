# Git Release Notifier

A Python command-line application for analyzing deployment states across different environments and generating HTML reports showing what changes are deployed where.

## Features

- Fetches version information from Spring Boot actuator endpoints
- Compares git commits between environments (DEV → TEST → PRE → PROD)
- Generates beautiful HTML reports with expandable commit details
- Supports multiple projects and repositories
- Automatic git repository cloning and updating

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your projects:**
   Edit `config.yaml` with your project details:
   ```yaml
   projects:
     - name: "my-project"
       repoUrl: "https://github.com/user/my-project.git"
       env:
         PROD: "https://prod-api.example.com"
         PRE: "https://pre-api.example.com"
         TEST: "https://test-api.example.com"
         DEV: "https://dev-api.example.com"
   ```

3. **Run the analysis:**
   ```bash
   python main.py --config config.yaml --output report.html
   ```

4. **Open the generated report:**
   Open `report.html` in your browser to see the deployment analysis.

## Usage

```bash
python main.py [OPTIONS]

Options:
  -c, --config PATH    Configuration file path [default: config.yaml]
  -o, --output PATH    Output HTML file path [default: release_report.html]
  -v, --verbose        Enable verbose logging
  --cleanup            Clean up cloned repositories after analysis
  --help               Show this message and exit
```

## How it Works

1. **Fetch Version Info**: Calls `/actuator/info` endpoint for each environment to get version and commit information
2. **Git Analysis**: Clones/updates repositories and compares commits between environments
3. **Report Generation**: Creates an HTML report showing:
   - PROD: Baseline environment (no commits shown)
   - PRE: Commits not yet deployed to PROD
   - TEST: Commits not yet deployed to PRE
   - DEV: Commits not yet deployed to TEST

## Configuration

The `config.yaml` file defines your projects and their environment URLs. Each project requires:

- `name`: Unique project identifier
- `repoUrl`: Git repository URL (HTTPS or SSH)
- `env`: Dictionary mapping environment names to their actuator URLs

## Requirements

- Python 3.7+
- Git installed and accessible
- Network access to configured APIs and repositories
- Spring Boot applications with `/actuator/info` endpoint enabled

## License

MIT License