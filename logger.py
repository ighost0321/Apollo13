"""A factory of log"""
import logging
import logging.config
import yaml

def get_log(yaml_file: str):
    """Return a logger object"""
    if not yaml_file:
        raise FileNotFoundError("Can not find yaml file!")
    
    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            log_cfg = yaml.safe_load(f.read())
    except FileNotFoundError:
        print(f'file_not_found_error {yaml_file}')
    except Exception as e:
        print("Failed to open log config!")
    else:
        try:
            logging.config.dictConfig(log_cfg)
        except Exception as e:
            print(e)
        else:
            log = logging.getLogger(' ')
            log.setLevel(logging.INFO)
    return log

