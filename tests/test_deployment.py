from random import SystemRandom
import string
from unittest import TestCase
from unittest.mock import Mock

from nuvla.api.resources.deployment import Deployment


def rand_str(n):
    return ''.join(
        SystemRandom().choice(string.ascii_lowercase) for _ in range(n))


class DeploymentTest(TestCase):

    def test_set_data(self):
        def nuvla_get(_id: str):
            resp = Mock()
            fltr = 'filter {}'.format(rand_str(5))
            if _id == 'data-set/data-records':
                resp.data = {'data-record-filter': 'records ' + fltr}
                return resp
            elif _id == 'data-set/data-objects':
                resp.data = {'data-object-filter': 'objects ' + fltr}
                return resp
            elif _id == 'data-set/data-records-and-objects':
                resp.data = {'data-record-filter': 'records ' + fltr,
                             'data-object-filter': 'objects ' + fltr}
                return resp
            raise Exception('Wrong request.')

        nuvla = Mock()
        nuvla.get = nuvla_get
        dpl_api = Deployment(nuvla)

        # no data
        dpl = {}
        dpl_api._set_data(dpl, {}, [], [])
        self.assertEqual({}, dpl)

        # prepare data sets
        times = {'time-start': '2020-03-09T00:00:00Z',
                 'time-end': '2020-03-09T01:00:00Z'}
        data_set_records = {'id': 'data-set/data-records', **times}
        data_set_objects = {'id': 'data-set/data-objects', **times}
        data_set_recs_objs = {'id': 'data-set/data-records-and-objects', **times}

        def data_filters_in(_dpl, names):
            self.assertIn('data', _dpl)
            for name in names:
                self.assertIn(name, _dpl['data'])
                self.assertIn('filters', _dpl['data'][name])
                self.assertIsInstance(_dpl['data'][name]['filters'], list)

        def data_ids_in(_dpl, names, size):
            self.assertIn('data', _dpl)
            for name in names:
                ids = '{}-ids'.format(name)
                self.assertIn(name, _dpl['data'])
                self.assertIn(ids, _dpl['data'][name])
                self.assertIsInstance(_dpl['data'][name][ids], list)
                self.assertEqual(size, len(_dpl['data'][name][ids]))

        # single data set of data-record
        dpl = {}
        dpl_api._set_data(dpl, [data_set_records])
        data_filters_in(dpl, ['records'])
        self.assertEqual(1, len(dpl['data']['records']['filters']))

        # a number of data sets of data-record
        dpl = {}
        dpl_api._set_data(dpl, [data_set_records, data_set_objects])
        data_filters_in(dpl, ['records', 'objects'])
        self.assertEqual(1, len(dpl['data']['records']['filters']))
        self.assertEqual(1, len(dpl['data']['objects']['filters']))

        ids_size = 5
        ids = list(map(lambda x: str(x), range(ids_size)))

        # ids of data-record
        dpl = {}
        dpl_api._set_data(dpl, records=ids)
        data_ids_in(dpl, ['records'], ids_size)

        # ids of data-object
        dpl = {}
        dpl_api._set_data(dpl, objects=ids)
        data_ids_in(dpl, ['objects'], ids_size)

        # ids of data-record and data-object
        dpl = {}
        dpl_api._set_data(dpl, records=ids, objects=ids)
        data_ids_in(dpl, ['records', 'objects'], ids_size)

        # data sets of data-record, data-object; ids of records and objects
        dpl = {}
        data_sets = [data_set_records, data_set_records, data_set_objects]
        dpl_api._set_data(dpl, data_sets, records=ids, objects=ids)
        data_filters_in(dpl, ['records', 'objects'])
        self.assertEqual(2, len(dpl['data']['records']['filters']))
        self.assertEqual(1, len(dpl['data']['objects']['filters']))
        data_ids_in(dpl, ['records', 'objects'], ids_size)

        # data set of data-record and data-object
        dpl = {}
        data_sets = [data_set_recs_objs]
        dpl_api._set_data(dpl, data_sets)
        data_filters_in(dpl, ['records', 'objects'])

    def test_template_interpolation(self):
        # Empty inputs.
        assert '' == Deployment._template_interpolation('', {})
        assert '' == Deployment._template_interpolation('', {'foo': 'bar'})

        text = 'https://${foo}:${bar.baz}/?${baz-foo}'

        # No substitution keys.
        self.assertRaises(ValueError, Deployment._template_interpolation,
                          *(text, {}))

        # Missing substitution key in params.
        self.assertRaises(ValueError, Deployment._template_interpolation,
                          *(text, {'foo': 'FOO', 'bar.baz': 'BAR.BAZ'}))

        # All required keys, but one empty substitution key in params.
        params = {'foo': '', 'bar.baz': 'BAR.BAZ', 'baz-foo': 'BAZ-FOO'}
        assert '' == Deployment._template_interpolation(text, params)

        # Success.
        params = {'foo': 'FOO', 'bar.baz': 'BAR.BAZ', 'baz-foo': 'BAZ-FOO'}
        assert 'https://FOO:BAR.BAZ/?BAZ-FOO' == \
               Deployment._template_interpolation(text, params)
