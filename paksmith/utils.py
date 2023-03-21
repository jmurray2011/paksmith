import json
import yaml
import jinja2
from jsonschema import Draft7Validator
import shutil
import tempfile
import logging
import os

class InitializationError(Exception):
    pass

def initialize(project_dir, verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    if os.path.exists(project_dir):
        raise InitializationError(f"Directory '{project_dir}' already exists. Cannot initialize project there.")
    
    # Get the path to the example_project folder
    example_project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'example_project')
    
    try:
        # Copy the entire example_project folder to the specified project directory
        shutil.copytree(example_project_dir, project_dir)
    except FileNotFoundError as e:
        logging.error(f"Error: {e}\nMake sure the example_project directory exists in the script's folder.")
    except shutil.Error as e:
        logging.error(f"Error while copying files: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

def validate_manifest(manifest_data, schema_file="schema.json"):
    # Load the schema
    with open(schema_file, "r") as f:
        schema = json.load(f)

    # Create a validator
    validator = Draft7Validator(schema)

    # Check if the manifest is valid
    errors = sorted(validator.iter_errors(manifest_data), key=lambda e: e.path)
    if errors:
        for error in errors:
            task_name = ""
            if "tasks" in error.absolute_path and isinstance(error.instance, dict) and "name" in error.instance:
                task_name = f" in task '{error.instance['name']}'"

            logging.error(f"Validation error{task_name}: {error.message}. Please modify your manifest file accordingly")
        exit(1)

def validate_templates(templates_dir, variables):
    undefined_variables = set()
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
    for template_name in env.list_templates():
        try:
            template = env.get_template(template_name)
            _ = template.render(variables)
        except jinja2.UndefinedError as e:
            undefined_variables.add(str(e))
        except Exception as e:
            continue

    if undefined_variables:
        raise ValueError(f"The following variables are undefined: {undefined_variables}")

def validate_project(project_dir, verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    manifest_file = os.path.join(project_dir, "manifest.yml")
    vars_file = os.path.join(project_dir, "vars.yml")
    assets_dir = os.path.join(project_dir, "assets")
    templates_dir = os.path.join(assets_dir, "templates")

    try:
        manifest = load_yaml_file(manifest_file)
        variables = load_yaml_file(vars_file)
        validate_manifest(manifest)
        validate_templates(templates_dir, variables)
        logging.info("Project validation passed.")
    except Exception as e:
        logging.error(f"Project validation failed: {e}")