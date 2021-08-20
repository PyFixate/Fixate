import ruamel.yaml
import pathlib
import fixate.config
import os
from string import Formatter


def load_dict_config(in_dict: dict, config_name: str = "") -> None:
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


def load_yaml_config(yaml_in: str) -> None:
    """
    :param in_file:
     string representing a valid file path to the yaml file
     >>> import fixate.config
     >>> with open("my_yaml_file.yml") as f:
     >>>    load_yaml_config("my_yaml_file.yml")
     >>> print(fixate.config.HI)
     "WORLD"
    """
    if not os.path.exists(yaml_in):
        raise FileNotFoundError("Config file {} not found".format(yaml_in))
    yaml = ruamel.yaml.YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    yaml_path = pathlib.Path(yaml_in)
    fixate.config.__dict__.update(yaml.load(yaml_path))


def get_plugins() -> dict:
    return {k: v for k, v in fixate.config.__dict__.items() if k.startswith("plg_")}


def get_plugin_data(plugin: str) -> dict:
    return get_plugins().get(plugin, {})


def get_config_dict() -> dict:
    return fixate.config.__dict__


class _UnseenFormatter(Formatter):
    """
    Renders string formats with invalid keys rendered as the key name
    """

    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            try:
                return kwargs[key]
            except KeyError:
                return "None"
        else:
            return Formatter.get_value(key, args, kwargs)


def render_template(_template: [str, list, tuple], *args, **kwargs):
    """
    :param template: Template string or list
    :param kwargs:
    :return:
    """
    if isinstance(_template, str):
        return _render.format(*args, **kwargs)
    renders = []
    for itm in _template:
        renders.append(_render.format(itm, *args, **kwargs))
    return renders


_render = _UnseenFormatter()
