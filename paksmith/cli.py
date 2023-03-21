import click
import logging
from .build import build_package
from .utils import initialize, validate_project


def setup_logging(verbose):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)

@cli.command()
@click.argument('init_dir', metavar='DIR')
def init(init_dir):
    """Initialize a new project directory with example files."""
    initialize(init_dir)

@cli.command()
@click.argument('project_dir', metavar='DIR')
@click.option('-d', '--destination', metavar='DIR', help='Path to the directory where the package will be saved')
@click.pass_context
def build(ctx, project_dir, destination):
    """Build a package from the project directory."""
    verbose = ctx.obj['verbose']
    build_package(project_dir, destination=destination, verbose=verbose)

@cli.command()
@click.argument('validate_dir', metavar='DIR')
@click.pass_context
def validate(ctx, validate_dir):
    """Validate the project structure and manifest file."""
    verbose = ctx.obj['verbose']
    validate_project(validate_dir, verbose=verbose)
