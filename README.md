# `paksmith`

This script is a tool for building .deb packages from a manifest file and a set of assets. It uses Jinja2 for templating and supports various hooks for running scripts at different stages of package installation or uninstallation.

## Requirements

* Python 3.6+
* Jinja2
* FPM

## Installation

1. Install Python 3.6 or higher if you don't have it already.
2. Install Jinja2: `pip install jinja2`
3. Install FPM: https://fpm.readthedocs.io/en/v1.15.1/installation.html

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
- `manifest.yml` contains the package information, tasks, files, templates, and scripts.
- `vars.yml` contains variables that can be used in Jinja2 templates.
- `assets/files/` contains files that will be included in the package.
- `assets/templates/` contains Jinja2 templates that will be rendered and included in the package.

2. Add `files` and `templates` as needed.

3. Edit the `manifest.yml` and `vars.yml` files as needed.

4. Build the .deb package:
```bash
python paksmith.py --project_dir /path/to/your/project [--destination /path/to/output] [--verbose]
```

This will generate a .deb package in the specified destination directory or in the current working directory if the destination is not provided. Note that file permissions (for both files and templates placed by the package) will be root:root by default. Appropriate permissions should be handled by hook scripts.

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
     destination: /opt/example/example.txt
 templates:
   - name: example.conf.j2
     destination: /etc/example/example.conf
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
### `manifest.yml` validation

You can validate the project by running:

```bash
python paksmith.py --validate /path/to/your/project
```

## vars.yml format

The `vars.yml` file contains variables that can be used in Jinja2 templates. Here's an example `vars.yml` file:

```yaml
variable1: value1
variable2: value2
```
# Considerations

To create a ```manifest.yml``` file for your packaging project, you'll need to follow a specific structure and include the necessary information to build the package. This file is crucial for defining how the package is built and the tasks involved in the process. 

Here's a step-by-step guide on how to create a ```manifest.yml``` file, including the different options and considerations to take into account:

## 1. Define basic package information:

At the beginning of the ```manifest.yml``` file, specify the package name and version:
```yaml
name: example-package
version: 1.0.0
```

## 2. Define tasks:

Tasks are the building blocks of your package. They are used to define the actions that need to be performed when building the package, such as placing files and templates or running scripts. Create a list of tasks under the ```tasks``` key:

```yaml
tasks:
  - name: Task 1
  - name: Task 2
```

Each task must have a unique name, which is specified under the ```name``` key.

## 3. Add files and templates:

For each task, you can specify the files to be placed (and templates to be rendered, then placed) in the package. To do this, use the ```files``` and ```templates``` keys under each task:

```yaml
tasks:
  - name: Task 1
    files:
      - name: file1.txt
        destination: /etc/file1.txt
    templates:
      - name: template1.j2
        destination: /etc/template1.conf
```

For each file or template, you need to provide the following information:
- ```name```: The name of the file or template (including its extension) as it appears in your project's assets directory.
- ```destination```: The path where the file or template should be placed in the package.

## 4. Specify optional file and template permissions:

You can also set optional owner, group, and mode permissions for files and templates. If you want to use these options, you must provide all three fields:

```yaml
tasks:
  - name: Task 1
    files:
      - name: file1.txt
        destination: /etc/file1.txt
        owner: user
        group: group
        mode: '644'
    templates:
      - name: template1.j2
        destination: /etc/template1.conf
        owner: user
        group: group
        mode: '644'
```

These fields will generate a post-install hook script that uses ```chown``` and ```chmod``` to apply the specified permissions.

## 5. Add scripts:

For each task, you can also include scripts that run during different stages of the package installation or uninstallation process. To add a script, use the ```scripts``` key under each task:

```yaml
tasks:
  - name: Task 1
    scripts:
      - hook: post-install
        content: |
          #!/bin/bash
          echo "Post-install script for Task 1"
```

For each script, you need to provide the following information:

- ```hook```: The stage at which the script should run. The possible values are ```pre-install```, ```post-install```, ```pre-uninstall```, and ```post-uninstall```.
- ```name```, ```template```, or ```content```: You can specify a script using one of these three keys. Use ```name``` if you have a script file in your project's assets directory, ```template``` if you have a script template that needs to be rendered using variables, or ```content``` if you want to provide the script content directly in the manifest file.

Make sure to use only one of these keys (```name```, ```template```, or ```content```) for each script.

## 6. Validate the manifest file:

Before using the manifest file to build the package, it's essential to validate its structure and content against the schema. You can validate the project by running:

```bash
python paksmith.py --validate /path/to/your/project
```

## 7. Considerations:

When creating a manifest file, keep the following considerations in mind:

- Ensure that the task names are unique and descriptive, as they help you identify the purpose of each task.
- Organize tasks in a logical order to reflect the flow of the package building process. This makes the manifest file more readable and maintainable.
- Be mindful of file and template destinations, as they determine where the files will be placed in the package. Ensure that these paths are valid and conform to the package's intended structure.
- Use the optional permissions (owner, group, and mode) consistently and appropriately. Double-check the permissions to avoid security issues or misconfigurations in the package.
- When defining scripts, ensure that the hooks are set correctly, and the scripts serve their intended purpose. Test the scripts to make sure they execute as expected during the package installation or uninstallation process.

By following these guidelines and including the necessary information in your ```manifest.yml``` file, you can create a well-structured and functional manifest that accurately defines your package's building process.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.
