import unittest

from nuvla.api.util.filter import filter_or, filter_and


class TestSearchUtil(unittest.TestCase):

    def test_filter_or(self):
        self.assertEqual('', filter_or([]))
        self.assertEqual('', filter_or([None]))
        self.assertEqual('', filter_or([None, None]))
        self.assertEqual('a', filter_or(['a', '']))
        self.assertEqual('(a or b)', filter_or(['a', 'b']))
        self.assertEqual('attr^="hello"', filter_or(['attr^="hello"']))
        self.assertEqual('(attr="a" or attr!="b")',
                         filter_or(['attr="a"', 'attr!="b"']))

    def test_filter_and(self):
        self.assertEqual('', filter_and([]))

        self.assertEqual('', filter_and([None]))
        self.assertEqual('', filter_and([None, None]))
        self.assertEqual('a', filter_and(['a', '']))
        self.assertEqual('(a and b)', filter_and(['a', 'b']))
        self.assertEqual('(attr="a" and attr!="b")',
                         filter_and(['attr="a"', 'attr!="b"']))
        self.assertEqual('(attr="a" and attr!="b")',
                         filter_and(['attr="a"', 'attr!="b"']))

    def test_filter_combination(self):
        self.assertEqual('', filter_and([filter_or([])]))
        self.assertEqual('attr="a"', filter_and([filter_or(['attr="a"'])]))
        self.assertEqual('(attr1="a" or attr2="b")',
                         filter_and(
                             [filter_or(['attr1="a"', 'attr2="b"'])]))
        self.assertEqual('(attr1="a" or attr2="b")',
                         filter_and(
                             [filter_or(['attr1="a"', 'attr2="b"']), None]))
        self.assertEqual('((attr1="a" or attr2="b") and attr2="c")',
                         filter_and(
                             [filter_or(['attr1="a"', 'attr2="b"']),
                              'attr2="c"']))
