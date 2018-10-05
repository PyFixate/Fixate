import os
import tempfile
import pytest
import fixate.config


def purge_test_values():
    purge_vals = []
    for k in fixate.config.__dict__:
        if k.startswith('test_val'):
            purge_vals.append(k)
    for k in purge_vals:
        del fixate.config.__dict__[k]


@pytest.fixture
def clean_config():
    purge_test_values()
    yield fixate.config
    purge_test_values()


def test_config_yaml_loader_string(clean_config):
    conf = clean_config
    conf.load_yaml_config("test_val1: Hello")
    assert conf.test_val1 == "Hello"


def test_config_yaml_loader_file_path(clean_config):
    conf = clean_config
    try:
        with tempfile.NamedTemporaryFile('w', delete=False) as f:
            f.write("test_val1: Hello")
            f.seek(0)
        conf.load_yaml_config(f.name)
    finally:
        os.remove(f.name)
    assert conf.test_val1 == "Hello"


def test_clean_config_fixture_working(clean_config):
    conf = clean_config
    with pytest.raises(AttributeError):
        conf.test_val1
