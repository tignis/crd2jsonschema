import pytest

import json
from pathlib import Path

from yaml import safe_load_all, safe_load
from jsonschema import validate

from crd2jsonschema import generate_filename


def test_generate_filenames():

    crd = """
    apiVersion: apiextensions.k8s.io/v1beta1
    kind: CustomResourceDefinition
    metadata:
      name: whatever.example.com
    spec:
      group: example.com
      names:
        kind: Thing
        listKind: ThingList
        plural: things
        singular: thing
      scope: Namespaced
      version: v1alpha2
      validation:
        openAPIV3Schema: {}
    """

    d = safe_load(crd)
    f = generate_filename(d)

    assert f == 'thing-example-v1alpha2.json'


valid_crd_metadata = [
    ({'spec': {'group': 'example.com', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-example-v1.json'),

    # Group
    ({'spec': {'group': 'sub.example.com', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-sub-example-v1.json'),
    ({'spec': {'group': 'UPPERcaseSUB.Example.COM', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-uppercasesub-example-v1.json'),
    ({'spec': {'group': 'nodots', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-nodots-v1.json'),
    ({'spec': {'group': 'two.subdomains.are.used.dexample.com', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-two-subdomains-v1.json'),
    ({'spec': {'group': 'double.dots.safe.after.first..example.com', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-double-dots-v1.json'),

    ({'spec': {'group': 'dots.before/slashes', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-dots-v1.json'),
    ({'spec': {'group': 'dots.sub.before.example.com/slashes', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-dots-sub-v1.json'),

    ({'spec': {'group': 'slashes/before.dots', 'names': {'singular': 'thing'}, 'version': 'v1'}}, 'thing-slashes-v1.json'),

    # Singular name, in arbitrary cases
    ({'spec': {'group': 'example.com', 'names': {'singular': 'CaSe'}, 'version': 'v1'}}, 'case-example-v1.json'),
]


@pytest.mark.parametrize("valid,expected", valid_crd_metadata)
def test_generate_good_filenames(valid, expected):
    assert expected == generate_filename(valid)


invalid_crd_metadata = [
    # Version
    {'spec': {'group': 'example.com', 'names': {'singular': 'thing'}, 'version': 'V1'}},  # uppercase version
    {'spec': {'group': 'example.com', 'names': {'singular': 'thing'}, 'version': 'extra % characters'}},

    {'spec': {'group': 'extra % characters', 'names': {'singular': 'thing'}, 'version': 'v1'}},
    {'spec': {'group': 'extra..dots.in.first.two.levels', 'names': {'singular': 'thing'}, 'version': 'v1'}},

    {'spec': {'group': 'example.com', 'names': {'singular': 'extra/characters'}, 'version': 'v1'}},
    {'spec': {'group': 'example.com', 'names': {'singular': 'thing'}, 'version': 'extra/characters'}},
]


@pytest.mark.parametrize("invalid", invalid_crd_metadata)
def test_generate_filenames_invalid_metadata(invalid):
    with pytest.raises((ValueError, TypeError)):
        r = generate_filename(invalid)
        print(r)


missing_crd_metadata = [
    {},
    {'spec': None},
    {'spec': {}},

    # Missing keys from dict
    {'spec': {'names': {'singular': 'thing'}, 'version': 'v1'}},
    {'spec': {'group': 'example.com', 'version': 'v1'}},
    {'spec': {'group': 'example.com', 'names': {'singular': 'CaSe'}}},

    # Names, but without singular.
    {'spec': {'group': 'example.com', 'names': {}, 'version': 'v1'}},
    {'spec': {'group': 'example.com', 'names': None, 'version': 'v1'}},
]


@pytest.mark.parametrize("missing", missing_crd_metadata)
def test_generate_filenames_missing_metadata(missing):
    with pytest.raises((KeyError, TypeError)):
        r = generate_filename(missing)
        print(r)
