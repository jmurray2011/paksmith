import os
import shutil
import logging
from .utils import setup_logging

class InitializationError(Exception):
    pass

def initialize(project_dir, verbose=False):
    setup_logging(verbose)

    if os.path.exists(project_dir):
        raise InitializationError(f"Directory '{project_dir}' already exists. Cannot initialize project there.")
    
    # Get the path to the example_project folder
    parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    example_project_dir = os.path.join(parent_directory, 'example_project')
    
    try:
        # Copy the entire example_project folder to the specified project directory
        shutil.copytree(example_project_dir, project_dir)
    except FileNotFoundError as e:
        raise InitializationError(f"Error: {e}\nMake sure the example_project directory exists in the script's folder.")
    except shutil.Error as e:
        raise InitializationError(f"Error while copying files: {e}")
    except Exception as e:
        raise InitializationError(f"Unexpected error: {e}")
    logging.info(f'Project initialized: {project_dir}')