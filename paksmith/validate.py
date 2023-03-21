import os
import json
import jinja2
import logging
from jsonschema import Draft7Validator
from .utils import setup_logging, load_yaml_file

class ValidationError(Exception):
    pass

def validate_manifest(manifest_data, schema_file="schema.json"):
    # Load the schema
    with open(schema_file, "r") as f:
        schema = json.load(f)

    # Create a validator
    validator = Draft7Validator(schema)

    # Check if the manifest is valid
    logging.debug(f'Validating manifest...')
    errors = sorted(validator.iter_errors(manifest_data), key=lambda e: e.path)
    if errors:
        for error in errors:
            task_name = ""
            if "tasks" in error.absolute_path and isinstance(error.instance, dict) and "name" in error.instance:
                task_name = f" in task '{error.instance['name']}'"

            logging.error(f"Validation error{task_name}: {error.message}. Please modify your manifest file accordingly")
        exit(1)
    logging.debug('Manifest validated.')

def validate_templates(templates_dir, variables):
    undefined_variables = set()
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
    for template_name in env.list_templates():
        logging.debug(f'Validating {template_name}...')
        try:
            template = env.get_template(template_name)
            _ = template.render(variables)
        except jinja2.UndefinedError as e:
            undefined_variables.add(str(e))
        except Exception as e:
            continue
        logging.debug(f'{template_name} is valid.')

    if undefined_variables:
        raise ValueError(f"The following variables are undefined: {undefined_variables}")
    logging.debug(f'All templates validated.')

def validate_project(project_dir, verbose):
    setup_logging(verbose)
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
        raise ValidationError(f"Project validation failed: {e}")