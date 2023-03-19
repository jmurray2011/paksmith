import yaml
import os
import shutil
import jsonschema
import json
from yaml import MarkedYAMLError
from jinja2 import Environment, FileSystemLoader, meta, Template
from jsonschema import Draft7Validator

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

class InitializationError(Exception):
    pass

class TemplateRenderingError(Exception):
    pass

def generate_permission_script(file_path, owner, group, mode):
    script = f"chown {owner}:{group} {file_path}\nchmod {mode} {file_path}"
    return script

# processes files and templates
def process_asset(asset, asset_type, assets_dir, package_root, hooks, variables=None):
    local_asset = os.path.join(assets_dir, asset_type, asset['name'])

    if asset_type == "templates":
        content = render_template(local_asset, variables)
    elif asset_type == "files":
        content = None

    destination_asset = os.path.join(package_root, asset['destination'].lstrip('/'))
    os.makedirs(os.path.dirname(destination_asset), exist_ok=True)

    if content is not None:
        with open(destination_asset, 'w') as f:
            f.write(content)
    else:
        shutil.copy(local_asset, destination_asset)

    if {'owner', 'group', 'mode'} <= set(asset.keys()):
        permission_script = generate_permission_script(asset['destination'], asset['owner'], asset['group'], asset['mode'])
        hooks['post-install'].append(permission_script)

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as stream:
            return yaml.safe_load(stream)
    except MarkedYAMLError as exc:
        print(f"YAML error on line {exc.problem_mark.line + 1}: {exc.problem}")
        exit(1)
    except Exception as exc:
        print(f"Error while loading YAML file: {exc}")
        exit(1)

def render_manifest_template(manifest_template, variables, output_file):
    with open(manifest_template, "r") as template_file:
        template_content = template_file.read()
    rendered_content = Template(template_content).render(variables)
    with open(output_file, "w") as manifest_file:
        manifest_file.write(rendered_content)

def render_template(template_path, variables):
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file '{template_path}' not found.")

    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    
    env = Environment(loader=FileSystemLoader(template_dir))
    
    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        raise TemplateRenderingError(f"Template '{template_name}' not found in '{template_dir}'")
    
    return template.render(**variables)

def initialize(project_dir):
    if os.path.exists(project_dir):
        raise InitializationError(f"Directory '{project_dir}' already exists. Cannot initialize project there.")
    
    # Get the path to the example_project folder
    example_project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'example_project')
    
    try:
        # Copy the entire example_project folder to the specified project directory
        shutil.copytree(example_project_dir, project_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}\nMake sure the example_project directory exists in the script's folder.")
    except shutil.Error as e:
        print(f"Error while copying files: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

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

            print(f"Validation error{task_name}: {error.message}. Please modify your manifest file accordingly")
        exit(1)

def validate_template_variables(manifest_data, vars_data, assets_dir):
  env = Environment(loader=FileSystemLoader(assets_dir))

  for task in manifest_data['tasks']:
      if 'templates' in task:
          for template in task['templates']:
              template_name = template['name']
              try:
                  # Load the template
                  tmpl = env.get_template(template_name)

                  # Find the variables used in the template
                  ast = env.parse(tmpl.source)
                  used_vars = meta.find_undeclared_variables(ast)

                  # Check if all used variables are present in the vars_data
                  for var in used_vars:
                      if not is_var_in_data(var, vars_data):
                          raise ValueError(f"Variable '{var}' in template '{template_name}' is not defined in vars.yml")

              except Exception as e:
                  print(f"Error validating template '{template_name}': {e}")
                  exit(1)

def is_var_in_data(var, data):
    if isinstance(data, dict):
        if var in data:
            return True
        for key, value in data.items():
            if is_var_in_data(var, value):
                return True
    elif isinstance(data, (list, tuple)):
        for item in data:
            if is_var_in_data(var, item):
                return True
    return False