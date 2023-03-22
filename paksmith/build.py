import logging
from yaml import MarkedYAMLError
import yaml
import shutil
from jinja2 import Environment, FileSystemLoader, meta, Template, TemplateNotFound
import os
import tempfile
from .utils import load_yaml_file
from .validate import validate_project

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

def build_package(project_dir, destination=None, verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    validate_project(project_dir, verbose=verbose)
    manifest_template = os.path.join(project_dir, "manifest.yml.j2")
    vars_file = os.path.join(project_dir, "vars.yml")
    variables = load_yaml_file(vars_file)

    # Check for manifest template and render it
    manifest_file = os.path.join(project_dir, "manifest.yml")
    if os.path.exists(manifest_template):
        render_manifest_template(manifest_template, variables, manifest_file)

    manifest = load_yaml_file(manifest_file)
    assets_dir = os.path.join(project_dir, "assets")

    package_name = manifest['name']
    package_version = manifest['version']
    package_type = manifest['type']
    dependencies = manifest.get('dependencies', [])

    hooks = {
        'pre-install': [],
        'post-install': [],
        'pre-uninstall': [],
        'post-uninstall': []
    }
    
    # setup hook logging
    for hook in hooks:
        hooks[hook].append(f'#!/bin/bash\n\nexec > >(tee -a /var/log/{package_name}-{hook}.log) 2>&1')

    assets_dir = os.path.join(project_dir, "assets")

    logging.info(f"Processing {project_dir}")
    with tempfile.TemporaryDirectory() as package_root:
        for task in manifest['tasks']:
            logging.debug(f"Processing task: {task['name']}")

            # place files into the filestructure according to their file['destination']
            if 'files' in task:
                for file in task['files']:
                    logging.debug(f'Adding file {file}')
                    process_asset(file, "files", assets_dir, package_root, hooks)

            # place rendered templates into the filestructure according to their template['destination']
            if 'templates' in task:
                for template in task['templates']:
                    logging.debug(f'Processing template {template}')
                    process_asset(template, "templates", assets_dir, package_root, hooks, variables)

            if 'scripts' in task:
                for script in task['scripts']:
                    logging.debug(f'Processing script {script}')
                    hook = script['hook']
                    script_content = None

                    # "normal" method, a script residing in path `script['name']`
                    if 'name' in script:
                        script_content = script['name']
                    
                    # "template" method, render a script template
                    elif 'template' in script:
                        local_template = os.path.join(assets_dir, "templates", script['template'])
                        script_content = render_template(local_template, variables)

                    # "inline" method, render a script from inline yml in manifest.yml
                    elif 'content' in script:
                        script_content = script['content']

                    # add script data to corresponding hook (pre/post install/uninstall)
                    if script_content:
                        hooks[hook].append(script_content)

        # build the fpm command
        fpm_command = f"fpm -s dir -t {package_type} -n {package_name} -v {package_version}"
        for hook, scripts in hooks.items():
            if scripts:
                hook_script = os.path.join(package_root, f"{hook}.sh")
                with open(hook_script, 'w') as f:
                    for script in scripts:
                        f.write(f"{script}\n")
                fpm_command += f" --{hook} {hook_script}"

        # add dependencies if present
        if dependencies:
            for dep in dependencies:
                fpm_command += f" -d {dep}"
        
        # if specified via cli argument, direct fpm to place the file in a specific directory
        if destination:
            if package_type == 'deb':
                pkg_file = os.path.join(destination, f"{package_name}_{package_version}_amd64.{package_type}")
            else:
                pkg_file = os.path.join(destination, f"{package_name}-{package_version}-1.x86_64.{package_type}")

            if os.path.isfile(pkg_file):
                logging.info(f"Overwriting existing {package_type} file: {pkg_file}")
                os.remove(pkg_file)
            fpm_command += f" -p '{destination}'"

        fpm_command += f" -C {package_root}"
        for task in manifest['tasks']:
            if 'files' in task:
                for file in task['files']:
                    destination_file = file['destination'].lstrip('/')
                    fpm_command += f" {destination_file}"
            if 'templates' in task:
                for template in task['templates']:
                    destination_template = template['destination'].lstrip('/')
                    fpm_command += f" {destination_template}"
        logging.debug(f"Building {package_type} package with FPM...\n\n{fpm_command}")
        os.system(fpm_command)
