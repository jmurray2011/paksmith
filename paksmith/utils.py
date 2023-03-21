import logging
import yaml
from yaml import MarkedYAMLError

def setup_logging(verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as stream:
            return yaml.safe_load(stream)
    except MarkedYAMLError as exc:
        logging.error(f"YAML error on line {exc.problem_mark.line + 1}: {exc.problem}")
        exit(1)
    except Exception as exc:
        logging.error(f"Error while loading YAML file: {exc}")
        exit(1)