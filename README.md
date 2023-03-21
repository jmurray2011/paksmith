# `paksmith`

This script is a tool for building packages (for now, .deb and .rpm are supported) from a manifest file and a set of assets. It uses Jinja2 for templating and supports various hooks for running scripts at different stages of package installation or uninstallation.

## Installation

### Prerequisites

- Python 3.6 or higher
- `rpm`
- `fpm` (see https://fpm.readthedocs.io/en/v1.15.1/installation.html)

### Install Virtualenv
First, make sure you have `virtualenv` installed. If you don't have it installed, you can install it using `pip`:

```bash
pip install virtualenv
```
### Set up a virtual environment

Navigate to the project directory and create a new virtual environment:

```bash
Copy code
cd /path/to/paksmith
virtualenv .venv
```

#### Activate the virtual environment:

For `bash` or `zsh`:
```bash
source .venv/bin/activate
```

### Install the project

Install the project in the virtual environment:
````bash
pip install --editable .
````

### Add the virtual environment's bin directory to PATH (Optional)
If you want to use the paksmith command without activating the virtual environment every time, you can add the virtual environment's bin directory to your PATH.

For bash or zsh, add the following line to your ~/.bashrc or ~/.zshrc file:

````bash
export PATH="/path/to/paksmith/.venv/bin:$PATH"
````

## Usage

````bash
Usage: paksmith [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose  Enable verbose output
  -h, --help     Show this message and exit.

Commands:
  build     Build a package from the project directory.
  init      Initialize a new project directory with example files.
  validate  Validate the project structure and manifest file.
  ````

### Example usage

1. Initialize a new project directory with example files:

```bash
paksmith [--verbose] init /path/to/your/project
```

This will create a project directory with the following structure:
```bash
project/
├── assets
│   ├── files
│   │   └── index.html
│   └── templates
│       └── hello_world.conf.j2
├── manifest.yml
├── manifest.yml.j2
└── vars.yml
```
- This is a working project that can be used via `paksmith build /path/to/your/project`
- `manifest.yml` contains the package information, tasks, files, templates, and scripts.
- `manifest.yml.j2` is an example `manifest.yml` template. If this file is present it will be automatically rendered with variables from `vars.yml`, and any existing `manifest.yml` will be overwritten.
- `vars.yml` contains variables that can be used in Jinja2 templates.
- `assets/files/` contains files that will be included in the package.
- `assets/templates/` contains Jinja2 templates that will be rendered and included in the package.



2. Add `files` and `templates` as needed.

3. Edit the `manifest.yml` and `vars.yml` files as needed.

4. Validate the package:
````bash
paksmith [--verbose] validate /path/to/your/project
````

5. Build the package:
```bash
paksmith [--verbose] build [--destination /path/to/output] /path/to/your/project 
```

This will generate a package in the specified destination directory or in the current working directory if the destination is not provided. Note that file permissions (for both files and templates placed by the package) will be `root:root` by default.

## The Manifest

The `manifest.yml` file defines the package information, tasks, files, templates, and scripts. Here's an example `manifest.yml` file that sets up an Apache "Hello, World!" site:

```yaml
name: hello-world-webserver
version: 1.0.0
type: deb
dependencies:
  - apache2
tasks:
  - name: Setup Apache site
    files:
      - name: index.html
        destination: /var/www/index.html
        owner: www-data
        group: www-data
        mode: g+rwx
    templates:
      - name: hello_world.conf.j2
        destination: /tmp/hello_world.conf
    scripts:
      - hook: post-install
        content: |
          #!/bin/bash
          
          a2dissite 000-default
          sudo cp /tmp/hello_world.conf /etc/apache2/sites-available/
          a2ensite hello_world
          systemctl reload apache2
          echo "Hello, world! webserver is now up and running."
```

Note the optional:
```yaml
    owner: www-data
    group: www-data
    mode: g+rwx
```

When these are present (all three must be to pass validation), `paksmith` will automatically create an additional `post-install` script that sets permissions you've specified. These options are available for both `files` and `templates`.

## vars.yml format

The `vars.yml` file contains variables that can be used in Jinja2 templates. Here's an example `vars.yml` file:

```yaml
variable1: value1
variable2: value2
```

# Creating `manifest.yml`

To create a ```manifest.yml``` file for your packaging project, you'll need to follow a specific structure and include the necessary information to build the package. This file is crucial for defining how the package is built and the tasks involved in the process. 

Here's a step-by-step guide on how to create a ```manifest.yml``` file, including the different options and considerations to take into account:

## 1. Define basic package information:

At the beginning of the ```manifest.yml``` file, specify the package name, version, type (`deb` or `rpm`), and dependencies:
```yaml
name: example-package
version: 1.0.0
type: deb
dependencies:
  - curl
  - vim

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
- `name`: The name of the file or template (including its extension) as it appears in your project's assets directory.
- `destination`: The path where the file or template should be placed in the package.

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
paksmith [--verbose] validate /path/to/your/project
```

## 7. Considerations:

When creating a manifest file, keep the following considerations in mind:
- Determine whether you need a `manifest.yml.j2` template. By default if this file exists it will be rendered at runtime using variables in `vars.yml`. It will overwrite any existing `manifest.yml`
- Ensure that the task names are unique and descriptive, as they help you identify the purpose of each task.
- Organize tasks in a logical order to reflect the flow of the package building process. This makes the manifest file more readable and maintainable.
- Be mindful of file and template destinations, as they determine where the files will be placed in the package. Ensure that these paths are valid and conform to the package's intended structure.
- Use the optional permissions (owner, group, and mode) consistently and appropriately. Double-check the permissions to avoid security issues or misconfigurations in the package.
- When defining scripts, ensure that the hooks are set correctly, and the scripts serve their intended purpose. Test the scripts to make sure they execute as expected during the package installation or uninstallation process.

By following these guidelines and including the necessary information in your ```manifest.yml``` file, you can create a well-structured and functional manifest that accurately defines your package's building process.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.
