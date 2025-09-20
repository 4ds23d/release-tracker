import click
import logging
import re
from pathlib import Path
from typing import List

from .config import load_config
from .analyzer import ReleaseAnalyzer, ProjectAnalysis
from .report_generator import HTMLReportGenerator
from .release_manager import ReleaseManager


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
@click.option('--verbose', '-v',
              is_flag=True,
              help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose: bool):
    """Git Release Tracker - Manage releases and analyze deployments."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--config', '-c', 
              default='config.yaml',
              help='Configuration file path')
@click.option('--output', '-o',
              default='release_report.html',
              help='Output HTML file path')
@click.option('--cleanup',
              is_flag=True,
              help='Clean up cloned repositories after analysis')
@click.pass_context
def analyze(ctx, config: str, output: str, cleanup: bool):
    """
    Analyze deployment differences across environments.
    
    This command fetches version information from Spring Boot actuator endpoints,
    compares git commits between environments, and generates an HTML report
    showing what changes are deployed in each environment.
    """
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
        report_generator.generate_report(analyses, output, cfg.projects)
        
        # Cleanup if requested
        if cleanup:
            logger.info("Cleaning up cloned repositories...")
            analyzer.git_manager.cleanup_repos()
        
        click.echo(f"✅ Report generated successfully: {Path(output).absolute()}")
        click.echo(f"📊 Analyzed {len(analyses)} projects")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--config', '-c', 
              default='config.yaml',
              help='Configuration file path')
@click.argument('jira_ticket')
@click.pass_context
def release(ctx, config: str, jira_ticket: str):
    """
    Start a release process for all projects.
    
    JIRA_TICKET: The JIRA ticket name (e.g., BWD-123) that will be used for
    the release branch name and tag annotation.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Validate JIRA ticket format
        if not re.match(r'^[A-Z]{1,10}-\d+$', jira_ticket):
            raise click.ClickException(
                f"Invalid JIRA ticket format: {jira_ticket}. "
                "Expected format: LETTERS-DIGITS (e.g., BWD-123)"
            )
        
        # Load configuration
        logger.info(f"Loading configuration from {config}")
        if not Path(config).exists():
            raise click.ClickException(f"Configuration file not found: {config}")
        
        cfg = load_config(config)
        logger.info(f"Loaded {len(cfg.projects)} projects from configuration")
        
        # Initialize release manager
        release_manager = ReleaseManager()
        
        click.echo(f"🚀 Starting release process for JIRA ticket: {jira_ticket}")
        click.echo(f"📋 Processing {len(cfg.projects)} projects...")
        
        release_infos = []
        
        # Prepare releases for all projects
        for project in cfg.projects:
            click.echo(f"\n📦 Processing project: {project.name}")
            
            release_info = release_manager.prepare_release(project, jira_ticket)
            if release_info:
                release_infos.append(release_info)
                click.echo(f"   ✅ Release prepared: {release_info.release_branch}")
                click.echo(f"   🏷️  New version: {release_info.new_version}")
                click.echo(f"   📝 Commits to include: {release_info.commits_count}")
            else:
                click.echo(f"   ⏭️  Skipped (no changes or error)")
        
        if not release_infos:
            click.echo("\n❌ No releases were prepared. All projects may be up to date or have errors.")
            return
        
        # Show summary and ask for confirmation
        click.echo(f"\n📊 Release Summary:")
        click.echo(f"{'Project':<20} {'Branch':<25} {'Version':<10} {'Commits':<8}")
        click.echo("-" * 70)
        
        for info in release_infos:
            click.echo(f"{info.project_name:<20} {info.release_branch:<25} {info.new_version:<10} {info.commits_count:<8}")
        
        # Ask for push confirmations
        for info in release_infos:
            click.echo(f"\n🔄 Project: {info.project_name}")
            
            # Get repository path
            repo = release_manager.git_manager.get_or_update_repo(
                next(p.repoUrl for p in cfg.projects if p.name == info.project_name), 
                info.project_name
            )
            repo_path = Path(repo.working_dir)
            
            # Ask about branch push
            if click.confirm(f"   Push branch '{info.release_branch}' to remote?"):
                if release_manager.push_branch(repo_path, info.release_branch):
                    click.echo(f"   ✅ Branch pushed successfully")
                else:
                    click.echo(f"   ❌ Failed to push branch")
                    continue
            
            # Create and push tag
            tag_message = f"Release {info.new_version} for {info.jira_ticket}"
            if release_manager.create_annotated_tag(repo_path, str(info.new_version), tag_message):
                click.echo(f"   🏷️  Tag {info.new_version} created")
                
                if click.confirm(f"   Push tag '{info.new_version}' to remote?"):
                    if release_manager.push_tag(repo_path, str(info.new_version)):
                        click.echo(f"   ✅ Tag pushed successfully")
                    else:
                        click.echo(f"   ❌ Failed to push tag")
            else:
                click.echo(f"   ❌ Failed to create tag")
        
        click.echo(f"\n🎉 Release process completed for {jira_ticket}!")
        
    except Exception as e:
        logger.error(f"Release process error: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()