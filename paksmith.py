import shutil
import tempfile
import argparse
import os
from utils import load_yaml_file, render_template, initialize, validate_manifest

def log(verbose, message):
    if verbose:
        print(message)

def main(project_dir, verbose=False, destination=None):
    manifest_file = os.path.join(project_dir, "manifest.yml")
    vars_file = os.path.join(project_dir, "vars.yml")

    manifest = load_yaml_file(manifest_file)
    variables = load_yaml_file(vars_file)

    package_name = manifest['name']
    package_version = manifest['version']
    dependencies = manifest.get('dependencies', [])

    hooks = {
        'pre-install': [],
        'post-install': [],
        'pre-uninstall': [],
        'post-uninstall': []
    }

    assets_dir = os.path.join(project_dir, "assets")

    with tempfile.TemporaryDirectory() as package_root:
        for task in manifest['tasks']:
            log(verbose, f"Processing task: {task['name']}")

            # place files into the .deb filestructure according to their file['destination']
            # file permissions will be root:root by default and should be handled by
            # post-install hook scripts
            if 'files' in task:
                for file in task['files']:
                    local_file = os.path.join(assets_dir, "files", file['name'])
                    destination_file = os.path.join(package_root, file['destination'].lstrip('/'))
                    os.makedirs(os.path.dirname(destination_file), exist_ok=True)
                    shutil.copy(local_file, destination_file)

            # place files into the .deb filestructure according to their template['destination']
            # file permissions will be root:root by default and should be handled by
            # post-install hook scripts
            if 'templates' in task:
                for template in task['templates']:
                    local_template = os.path.join(assets_dir, "templates", template['name'])
                    
                    rendered_template = render_template(local_template, variables)
                    destination_template = os.path.join(package_root, template['destination'].lstrip('/'))
                    os.makedirs(os.path.dirname(destination_template), exist_ok=True)
                    with open(destination_template, 'w') as f:
                        f.write(rendered_template)

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
        fpm_command = f"fpm -s dir -t deb -n {package_name} -v {package_version}"
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
            deb_file = os.path.join(destination, f"{package_name}_{package_version}_amd64.deb")
            if os.path.isfile(deb_file):
                log(verbose, f"Overwriting existing .deb file: {deb_file}")
                os.remove(deb_file)
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
        log(verbose, f"Building .deb package with FPM...\n\n{fpm_command}")
        os.system(fpm_command)
        log(verbose, "Package built successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a .deb package from a manifest file")
    parser.add_argument('-d', '--destination', help="Specify the destination for the .deb package")
    parser.add_argument('-i', '--init', help="Initialize example project in the specified location")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('-p', '--project_dir', help="Path to the project directory containing vars.yml, manifest.yml, and assets")
    args = parser.parse_args()

    if args.init:
        initialize(args.init)
    elif args.project_dir:
        main(args.project_dir, verbose=args.verbose, destination=args.destination)
    else:
        parser.error("you must provide either '--init' or '--project_dir'.")

