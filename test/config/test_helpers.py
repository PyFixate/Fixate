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
    with pytest.raises(FileNotFoundError):
        conf.load_yaml_config("test_val1: Hello")


def test_config_yaml_loader_file_path(clean_config, tmpdir):
    conf = clean_config
    p = tmpdir.join('test1.yml')
    p.write("test_val1: Hello\n")
    conf.load_yaml_config(p.strpath)
    assert conf.test_val1 == "Hello"


def test_config_yaml_override_config(clean_config, tmpdir):
    conf = clean_config
    p1 = tmpdir.join('test1.yml')
    p1.write("test_val1: Hello\ntest_val2: World\n")
    p2 = tmpdir.join('test2.yml')
    p2.write("test_val1: Hi\ntest_val3: New\n")
    conf.load_yaml_config(p1.strpath)
    conf.load_yaml_config(p2.strpath)
    assert conf.test_val1 == "Hi"
    assert conf.test_val2 == "World"
    assert conf.test_val3 == "New"


def test_clean_config_fixture_working(clean_config):
    conf = clean_config
    with pytest.raises(AttributeError):
        conf.test_val1
