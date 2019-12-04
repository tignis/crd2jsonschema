import pytest

import json
from pathlib import Path

from yaml import safe_load_all, safe_load
import jsonschema
from crd2jsonschema import process_yaml_file


FIXTURE_DIRECTORY = Path(__file__).resolve().parent # / 'fixtures' / 'cert-manager' / '13fcbb9384467ac871f3b031c3b4e5767ae46596'

@pytest.fixture
def crd_file():
    """
    This contains 1 custom resource definition, in a multipart yaml file.
    """
    with open(FIXTURE_DIRECTORY / 'flux-helm-release-crd.yaml') as f:
        yield f


def test_crd_fixture_sanity(crd_file):
    yaml_object = list([document for document in safe_load_all(crd_file) if document is not None])

    # The above file defines 1 CRD
    assert len(yaml_object) == 1

    for document in yaml_object:
        assert document['kind'] == 'CustomResourceDefinition'


def test_count_extracted_schemas(crd_file, tmpdir):
    assert len(tmpdir.listdir()) == 0

    extracted_schemas = process_yaml_file(crd_file, tmpdir)

    assert extracted_schemas == [
        'helmrelease-helm-fluxcd-v1.json',
    ]

    # Returned the list of files that were written.
    assert sorted(list(extracted_schemas)) == sorted([x.basename for x in tmpdir.listdir()])


def test_validate_issuer_schema(crd_file, tmpdir):
    """
    Use https://github.com/Julian/jsonschema to verify the custom resource is valid against the newly-written schema file.
    """
    extracted_schemas = process_yaml_file(crd_file, tmpdir)

    with open(tmpdir / 'helmrelease-helm-fluxcd-v1.json') as f:
        schema = json.load(f)

    with open(FIXTURE_DIRECTORY / 'example-helmrelease.yaml') as issuer_yaml_fh:
        issuer = safe_load(issuer_yaml_fh)

    # CRDs normally contain a metaschema 'http://json-schema.org/schema#', but jsonschema.validate() expects one of the various drafts instead.
    # Not specifying a validator class produces a warning and then uses the latest version. Look up the latest version ourselves, and use that.
    latest_validator_class = jsonschema.validators.validator_for(True)
    jsonschema.validate(issuer, schema=schema, cls=latest_validator_class)
