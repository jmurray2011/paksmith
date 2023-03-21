#! /usr/bin/env python3

import shutil
import tempfile
import argparse
import os
from utils import load_yaml_file, render_template, initialize, render_manifest_template, validate_manifest, process_asset

def log(verbose, message):
    if verbose:
        print(message)

def create_parser():
    parser = argparse.ArgumentParser(description="Paksmith - A tool for building {package_type} packages from a manifest file and a set of assets")
    subparsers = parser.add_subparsers(title="commands", dest="command", help="Available commands", required=True)
    return parser, subparsers

def validate_project(project_dir):
    manifest_file = os.path.join(project_dir, "manifest.yml")
    vars_file = os.path.join(project_dir, "vars.yml")
    assets_dir = os.path.join(project_dir, "assets")

    try:
        manifest = load_yaml_file(manifest_file)
        variables = load_yaml_file(vars_file)
        validate_manifest(manifest)
        # validate_template_variables(manifest, variables, assets_dir)
        print("Project validation passed.")
    except Exception as e:
        print(f"Project validation failed: {e}")

def main(project_dir, verbose=False, destination=None):
    validate_project(project_dir)
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

    with tempfile.TemporaryDirectory() as package_root:
        for task in manifest['tasks']:
            log(verbose, f"Processing task: {task['name']}")



            # place files into the {package_type} filestructure according to their file['destination']
            if 'files' in task:
                for file in task['files']:
                    process_asset(file, "files", assets_dir, package_root, hooks)

            # place files into the {package_type} filestructure according to their template['destination']
            if 'templates' in task:
                for template in task['templates']:
                    process_asset(template, "templates", assets_dir, package_root, hooks, variables)

            if 'scripts' in task:
                for script in task['scripts']:
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
                log(verbose, f"Overwriting existing {package_type} file: {pkg_file}")
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
        log(verbose, f"Building {package_type} package with FPM...\n\n{fpm_command}")
        os.system(fpm_command)
        log(verbose, "Package built successfully.")

if __name__ == "__main__":
    parser, subparsers = create_parser()
    init_parser = subparsers.add_parser("init", help="Initialize a new project directory with example files")
    init_parser.add_argument("init_dir", metavar="DIR", help="Path to the directory where the project will be initialized")

    build_parser = subparsers.add_parser("build", help="Build a package from the project directory")
    build_parser.add_argument("project_dir", metavar="DIR", help="Path to the project directory containing manifest.yml and assets")
    build_parser.add_argument("-d", "--destination", metavar="DIR", help="Path to the directory where the package will be saved")
    build_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    validate_parser = subparsers.add_parser("validate", help="Validate the project structure and manifest file")
    validate_parser.add_argument("validate_dir", metavar="DIR", help="Path to the project directory to validate")


    args = parser.parse_args()

    if args.command == "init":
        initialize(args.init_dir)
    elif args.command == "validate":
        validate_project(args.validate_dir)
    elif args.command == "build":
        main(args.project_dir, verbose=args.verbose, destination=args.destination)
    else:
        print("No action specified. Use '-h' or '--help' for help.")
