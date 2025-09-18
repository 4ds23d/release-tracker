import click
import logging
from pathlib import Path
from typing import List

from .config import load_config
from .analyzer import ReleaseAnalyzer, ProjectAnalysis
from .report_generator import HTMLReportGenerator


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.command()
@click.option('--config', '-c', 
              default='config.yaml',
              help='Configuration file path')
@click.option('--output', '-o',
              default='release_report.html',
              help='Output HTML file path')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Enable verbose logging')
@click.option('--cleanup',
              is_flag=True,
              help='Clean up cloned repositories after analysis')
def main(config: str, output: str, verbose: bool, cleanup: bool):
    """
    Git Release Notifier - Analyze deployment differences across environments.
    
    This tool fetches version information from Spring Boot actuator endpoints,
    compares git commits between environments, and generates an HTML report
    showing what changes are deployed in each environment.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {config}")
        if not Path(config).exists():
            raise click.ClickException(f"Configuration file not found: {config}")
        
        cfg = load_config(config)
        logger.info(f"Loaded {len(cfg.projects)} projects from configuration")
        
        # Initialize analyzer
        analyzer = ReleaseAnalyzer()
        
        # Analyze all projects
        analyses: List[ProjectAnalysis] = []
        for project in cfg.projects:
            logger.info(f"Analyzing project: {project.name}")
            analysis = analyzer.analyze_project(project)
            if analysis:
                analyses.append(analysis)
                logger.info(f"Successfully analyzed {project.name}")
            else:
                logger.warning(f"Failed to analyze {project.name}")
        
        if not analyses:
            raise click.ClickException("No projects could be analyzed successfully")
        
        # Generate report
        logger.info("Generating HTML report...")
        report_generator = HTMLReportGenerator()
        report_generator.generate_report(analyses, output)
        
        # Cleanup if requested
        if cleanup:
            logger.info("Cleaning up cloned repositories...")
            analyzer.git_manager.cleanup_repos()
        
        click.echo(f"✅ Report generated successfully: {Path(output).absolute()}")
        click.echo(f"📊 Analyzed {len(analyses)} projects")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    main()