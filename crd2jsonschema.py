#!/usr/bin/env python

import yaml  # https://pyyaml.org/wiki/PyYAMLDocumentation
import json
import os
import re


DNS_1123_REGEX = re.compile('[a-z0-9]([-a-z0-9]*[a-z0-9])?')


def generate_filename(crd_dictionary):
    """
    Given a dictionary loaded from a CRD yaml, extract the resource group, version, kind. Return a filename matching kubeval's expectations.
    https://github.com/instrumenta/kubeval/blob/8c40ed5d2110c5dd7fe45d6a429f16170c9910d1/kubeval/kubeval.go#L40

    >>> s = '''
    ... apiVersion: apiextensions.k8s.io/v1beta1
    ... kind: CustomResourceDefinition
    ... metadata:
    ...   name: whatever.example.com
    ... spec:
    ...   group: example.com
    ...   names:
    ...     kind: Thing
    ...     listKind: ThingList
    ...     plural: things
    ...     singular: thing
    ...   scope: Namespaced
    ...   version: v1alpha2
    ...   validation:
    ...     openAPIV3Schema: {}
    ... '''
    >>> d = yaml.safe_load(s)
    >>> generate_filename(d)
    'thing-example-v1alpha2.json'

    >>> d['spec']['version'] = 'v1/v2'
    >>> generate_filename(d)
    Traceback (most recent call last):
       ...
    ValueError: ('Invalid version', 'v1/v2')

    :param crd_dictionary: a dictionary from yaml.safe_load_all(f)[]
    :return: A proposed filename.
    """

    try:
        kind = crd_dictionary['spec']['names']['singular'].lower()
    except KeyError:
        kind = crd_dictionary['spec']['names']['kind'].lower()
    group_parts = crd_dictionary['spec']['group'].split('/')[0].split('.')
    version_part = crd_dictionary['spec']['version']

    kind_suffix = group_parts[0].lower()
    if len(group_parts)>2:
        kind_suffix += "-" + group_parts[1].lower()

    if not DNS_1123_REGEX.fullmatch(kind):
        raise ValueError('Invalid kind', kind)
    if not DNS_1123_REGEX.fullmatch(kind_suffix):
        raise ValueError('Invalid group', kind_suffix)
    if not DNS_1123_REGEX.fullmatch(version_part):
        raise ValueError('Invalid version', version_part)

    return '%s-%s-%s.json' % (
        kind,
        kind_suffix,
        version_part
    )


def process_yaml_file(yaml_in, output_directory):
    yaml_object = yaml.safe_load_all(yaml_in) # yaml_object will be a list or a dict

    wrote_filenames = []

    for document in yaml_object:
        if document is None: continue  # skip empty yaml document

        filename = generate_filename(document)
        schema_part = document['spec']['validation']['openAPIV3Schema']

        # Patch the schema with kubernetes extensions
        schema_part['x-kubernetes-group-version-kind'] = [{
            'kind': [document['spec']['names']['kind']],
            'version': document['spec']['version'],
            'group': document['spec']['group'],
        }]

        # This is json-schema, even though the CRD didn't state that explicitly.
        schema_part['$schema'] = 'http://json-schema.org/schema#'

        with open(os.path.join(output_directory, filename), 'x') as json_out:
            json.dump(schema_part, json_out, indent=2)

        wrote_filenames.append(filename)

    return wrote_filenames


def main():
    import argparse

    parser = argparse.ArgumentParser(description=(
        'Given a list of yaml files containing Kubernetes Custom Resource Definitions (CRDs), '
        'extract the embedded openAPIV3Schema into a standalone file usable by http://kubeval.instrumenta.dev'
    ))
    parser.add_argument('--output-directory', default=os.getcwd(), help="write json-schema files to this directory")
    parser.add_argument('-q', target='quiet', action='store_true', help="emit less output")
    parser.add_argument('yaml_files', metavar='crd.yaml', nargs='+', type=argparse.FileType('r'))


    args = parser.parse_args()

    for yaml_file_handle in args.yaml_files:
        r = process_yaml_file(yaml_file_handle, args.output_directory)

        if not args.quiet:
            for fn in r:
                print(fn)


if __name__ == '__main__':
    main()
