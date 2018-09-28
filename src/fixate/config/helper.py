import json
import ruamel.yaml
import fixate.config


def load_dict_config(in_dict: dict, config_name: str = '') -> None:
    """
    :param in_dict:
     dictionary type storing configuration parameters
    :param config_name:
     optional way of grouping the config details
    :usage
     >>> my_config_dict = {"HI" :"WORLD"}
     config_name = None
     >>> import fixate.config
     >>> load_dict_config(my_config_dict)
     >>> print(fixate.config.HI)
     "WORLD"
     config_name = "My_Dict"
     >>> import fixate.config
     >>> load_dict_config(my_config_dict, "My_Dict")
     >>> print(fixate.config.My_Dict)
     {"HI": "WORLD"}
    """
    if config_name:
        fixate.config.__dict__.update({config_name: in_dict})
    else:
        fixate.config.__dict__.update(in_dict)


def load_json_config(in_file, config_name=None) -> None:
    """
    :param in_file:
     valid open file like such as
        open(in_file) as f:
            load_json_config(f)
     or stringio instance
    :param config_name:
     optional way of grouping the config details
    :usage
     my_json_file
     {
        "HI": "WORLD"
     }
     config_name = None
     >>> import fixate.config
     >>> with open("my_json_file") as f:
     >>>    load_json_config("my_json_file")
     >>> print(fixate.config.HI)
     "WORLD"
     config_name = "My_Json"
     >>> import fixate.config
     >>> with open("my_json_file") as f:
     >>>    load_json_config("my_json_file", "My_Json")
     >>> print(fixate.config.My_Json)
     {"HI": "WORLD"}
    """
    if config_name:
        fixate.config.__dict__.update({config_name: json.load(in_file)})
    else:
        fixate.config.__dict__.update(json.load(in_file))


def load_yaml_config(in_file, config_name=None) -> None:
    """
    :param in_file:
     valid open file like such as
        open(in_file) as f:
            load_json_config(f)
     or stringio instance
     or path to file
    :param config_name:
     optional way of grouping the config details
    :usage
     my_yaml_file
     HI: WORLD
     config_name = None
     >>> import fixate.config
     >>> with open("my_yaml_file") as f:
     >>>    load_yaml_config("my_yaml_file")
     >>> print(fixate.config.HI)
     "WORLD"
     config_name = "My_Json"
     >>> import fixate.config
     >>> with open("my_yaml_file") as f:
     >>>    load_yaml_config("my_yaml_file", "My_Yaml")
     >>> print(fixate.config.My_Yaml)
     {"HI": "WORLD"}
    """
    yaml = ruamel.yaml.YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    if config_name:
        fixate.config.__dict__.update({config_name: yaml.load(in_file)})
    else:
        fixate.config.__dict__.update(yaml.load(in_file))


def get_plugin_data(plugin: str) -> dict:
    tmp = fixate.config.__dict__
    tmp.update(fixate.config.plugins.get(plugin, {}))
    return tmp
