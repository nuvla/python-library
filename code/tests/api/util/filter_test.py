import unittest

from nuvla.api.util.filter import filter_or, filter_and


class TestSearchUtil(unittest.TestCase):

    attr_a = 'attr="a"'
    attr_b = 'attr="b"'
    attr_not_b = 'attr!="b"'

    def test_filter_or(self):
        self.assertEqual('', filter_or([]))
        self.assertEqual('', filter_or([None]))
        self.assertEqual('', filter_or([None, None]))
        self.assertEqual('a', filter_or(['a', '']))
        self.assertEqual('(a or b)', filter_or(['a', 'b']))
        self.assertEqual('attr^="hello"', filter_or(['attr^="hello"']))
        self.assertEqual(f'({self.attr_a} or {self.attr_not_b})',
                         filter_or([self.attr_a, self.attr_not_b]))

    def test_filter_and(self):
        self.assertEqual('', filter_and([]))

        self.assertEqual('', filter_and([None]))
        self.assertEqual('', filter_and([None, None]))
        self.assertEqual('a', filter_and(['a', '']))
        self.assertEqual('(a and b)', filter_and(['a', 'b']))
        self.assertEqual('attr^="hello"', filter_and(['attr^="hello"']))
        self.assertEqual(f'({self.attr_a} and {self.attr_not_b})',
                         filter_and([self.attr_a, self.attr_not_b]))

    def test_filter_combination(self):
        self.assertEqual('', filter_and([filter_or([])]))
        self.assertEqual(self.attr_a, filter_and([filter_or([self.attr_a])]))
        self.assertEqual(f'({self.attr_a} or {self.attr_b})',
                         filter_and(
                             [filter_or([self.attr_a, self.attr_b])]))
        self.assertEqual(f'({self.attr_a} or {self.attr_b})',
                         filter_and(
                             [filter_or([self.attr_a, self.attr_b]), None]))
        self.assertEqual(f'(({self.attr_a} or {self.attr_b}) and attr2="c")',
                         filter_and(
                             [filter_or([self.attr_a, self.attr_b]),
                              'attr2="c"']))
