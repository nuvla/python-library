# -*- coding: utf-8 -*-
from typing import List, Optional


def __filter_join(list_comparison: List[Optional[str]],
                  join_logic: str = 'or') -> str:
    list_comparison_filtered = [x for x in list_comparison if x]
    if list_comparison_filtered:
        separator = f' {join_logic} '
        result = separator.join(list_comparison_filtered)
        return f'({result})' if len(list_comparison_filtered) > 1 else result
    else:
        return ''


def filter_or(list_comparison: List[Optional[str]]) -> str:
    return __filter_join(list_comparison, 'or')


def filter_and(list_comparison: List[Optional[str]]) -> str:
    return __filter_join(list_comparison, 'and')
