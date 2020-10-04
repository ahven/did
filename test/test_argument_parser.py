from argparse import REMAINDER

import pytest

from did.argument_parser import ArgumentParser


@pytest.mark.parametrize(
    'input_args,expected_parsed',
    [
        ([''], ['']),
        (['-b'], ['-b']),
        (['-i', '5'], ['-i=5']),
        (['-i', '-5'], ['-i=-5']),
        (['-s', '-30..'], ['-s=-30..']),
        (['-s', '-b'], ['-s=-b']),
        (['--one-string', '-b'], ['--one-string=-b']),
        (['-k', '-30..'], ['-k', '-30..']),
    ]
)
def test_fix_args(input_args, expected_parsed):
    parser = ArgumentParser(description='foo')
    parser.add_argument('-b', '--bool-flag', action='store_true')
    parser.add_argument('-i', '--one-integer', type=int)
    parser.add_argument('-s', '--one-string', type=str)
    parser.add_argument('rest', nargs=REMAINDER)

    assert parser._fix_args(input_args) == expected_parsed
