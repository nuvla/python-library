# -*- coding: utf-8 -*-

import logging

try:
    __path__ = __import__('pkgutil').extend_path(__path__, __name__)
except Exception as e:
    logging.debug(f'Failed to create namespace package with pkgutil.extend_path: {e}')
    try:
        __import__('pkg_resources').declare_namespace(__name__)
    except Exception as ex:
        logging.debug(f'Failed to create namespace package with pkg_resources.declare_namespace: {ex}')
