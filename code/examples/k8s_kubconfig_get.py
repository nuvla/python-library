#!/usr/bin/env python

import yaml
import os
import sys
import base64


def read_config(fname) -> dict:
    with open(os.path.expanduser(fname)) as fh:
        config = yaml.safe_load(fh.read())
    return config


def get_cluster_and_user(config, context_name):
    cluster_n = None
    user_n = None
    for cx in config.get('contexts', []):
        if cx.get('name') == context_name:
            cluster_n = cx.get('context').get('cluster')
            user_n = cx.get('context').get('user')
    return cluster_n, user_n


def get_cluster_cacert(config, cluster_name):
    ca_cert = None
    for c in config.get('clusters'):
        if c.get('name') == cluster_name:
            ca_cert = c.get('cluster').get('certificate-authority-data')
    return ca_cert


def get_cluster_endpoint(config, cluster_name):
    endpoint = None
    for c in config.get('clusters'):
        if c.get('name') == cluster_name:
            endpoint = c.get('cluster').get('server')
    return endpoint


def get_client_creds(config, user_name):
    cert = None
    key = None
    for u in config.get('users'):
        if u.get('name') == user_name:
            cert = u.get('user').get('client-certificate-data')
            key = u.get('user').get('client-key-data')
    return cert, key


def main(config_fn, context):
    config = read_config(config_fn)

    cluster_name, user_name = get_cluster_and_user(config, context)
    if not cluster_name and not user_name:
        print('Failed to find cluster and user by context {0} in {1}'
              .format(context, config_fn))
        exit(1)

    ca_data = get_cluster_cacert(config, cluster_name)
    if not ca_data:
        print('Failed to find CA data by cluster name {0} in {1}'
              .format(cluster_name, config_fn))
        exit(1)
    else:
        print('::: certificate-authority-data')
        print(base64.b64decode(ca_data).decode())

    client_cert_data, client_key_data \
        = get_client_creds(config, user_name)
    if not client_cert_data and not client_key_data:
        print('Failed to find user cert and key by user name {0} in {1}'
              .format(user_name, config_fn))
        exit(1)
    else:
        print('::: client-certificate-data')
        print(base64.b64decode(client_cert_data).decode())
        print('::: client-key-data')
        print(base64.b64decode(client_key_data).decode())

    endpoint = get_cluster_endpoint(config, cluster_name)
    if not endpoint:
        print('Failed to find cluster endpoint cluster name {0} in {1}'
              .format(cluster_name, config_fn))
        exit(1)
    else:
        print('::: cluster endpoint')
        print(endpoint)


if __name__ == '__main__':
    config_file = '~/.kube/config'

    if len(sys.argv) < 2:
        print('Provide context.')
        exit(1)
    else:
        context = sys.argv[1]
        if len(sys.argv) == 3:
            config_file = sys.argv[2]

    main(config_file, context)
