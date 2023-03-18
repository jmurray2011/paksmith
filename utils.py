import yaml
import os
import shutil
import jsonschema
import json
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
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML file '{file_path}' not found.")

    with open(file_path, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing YAML file '{file_path}': {exc}")

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
    os.makedirs(project_dir)
    assets_dir = os.path.join(project_dir, "assets")
    os.makedirs(os.path.join(assets_dir, "files"))
    os.makedirs(os.path.join(assets_dir, "templates"))

    # Save example manifest.yml
    example_manifest = '''
name: example-package
version: 1.0.0
tasks:
  - name: Task 1
    templates:
      - name: template1.j2
        destination: /etc/template1.conf
    scripts:
      - hook: post-install
        name: script1.sh
  - name: Task 2
    templates:
      - name: template2.j2
        destination: /etc/template2.conf
    scripts:
      - hook: post-install
        template: script2.j2
  - name: Task 3
    scripts:
      - hook: pre-install
        content: |
          #!/bin/bash
          echo "Pre-install script for Task 3"
'''
    with open(os.path.join(project_dir, "manifest.yml"), "w") as f:
        f.write(example_manifest)

    # Save example-vars.yml
    example_vars = '''
app_name: example-app
app_version: 1.0.0

server:
  host: example.com
  port: 8080

database:
  name: example-db
  username: dbuser
  password: dbpassword
  host: db.example.com
  port: 5432

email:
  smtp_host: smtp.example.com
  smtp_port: 587
  sender_email: noreply@example.com
  sender_password: emailpassword
'''
    with open(os.path.join(project_dir, "vars.yml"), "w") as f:
        f.write(example_vars)

def validate_manifest(manifest_data, schema_file="schema.json"):
    with open(schema_file, "r") as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=manifest_data, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}. Please modify your manifest file accordingly")
        print(f"Error in {list(e.absolute_path)}")
        exit(1)
    except jsonschema.SchemaError as e:
        print(f"Schema error: {e}")
        exit(1)

    print(f"schema passes validation")