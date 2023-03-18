# `paksmith`

This script is a tool for building .deb packages from a manifest file and a set of assets. It uses Jinja2 for templating and supports various hooks for running scripts at different stages of package installation or uninstallation.

## Requirements

* Python 3.6+
* Jinja2
* FPM

## Installation

1. Install Python 3.6 or higher if you don't have it already.
2. Install Jinja2: `pip install Jinja2`
3. Install FPM: https://fpm.readthedocs.io/en/latest/installing.html

## Usage

1. Initialize a new project directory with example files:

```bash
python paksmith.py --init /path/to/your/project
```

This will create a project directory with the following structure:
```bash
project/
├── assets/
│ ├── files/
│ └── templates/
├── manifest.yml
└── vars.yml
```
2. Add `files` and `templates` as needed.

3. Edit the `manifest.yml` and `vars.yml` files as needed.

4. Build the .deb package:
```bash
python paksmith.py --project_dir /path/to/your/project [--destination /path/to/output] [--verbose]
```

This will generate a .deb package in the specified destination directory or in the current working directory if the destination is not provided.

## manifest.yml format

The `manifest.yml` file defines the package information, tasks, files, templates, and scripts. Here's an example `manifest.yml` file:

```yaml
name: example-package
version: 1.0.0
dependencies:
- some-dependency
tasks:
- name: Task 1
 files:
   - name: example.txt
     destination: /opt/example/
 templates:
   - name: example.conf.j2
     destination: /etc/example/
 scripts:
   - hook: post-install
     content: echo "Task 1 post-install script"
- name: Task 2
 scripts:
   - hook: pre-install
     name: script1.sh
   - hook: post-install
     template: script2.sh.j2
```

## vars.yml format

The `vars.yml` file contains variables that can be used in Jinja2 templates. Here's an example `vars.yml` file:

```yaml
variable1: value1
variable2: value2
```

## Project structure
After initializing a new project directory with example files, you will have the following structure:

```bash
project/
├── assets/
│   ├── files/
│   └── templates/
├── manifest.yml
└── vars.yml
```

- `manifest.yml` contains the package information, tasks, files, templates, and scripts.
- `vars.yml` contains variables that can be used in Jinja2 templates.
- `assets/files/` contains files that will be included in the package.
- `assets/templates/` contains Jinja2 templates that will be rendered and included in the package.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.
