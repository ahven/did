import argparse
import sys


class ArgumentParser(argparse.ArgumentParser):
    """Wrapper of the standard ArgumentParser such that allows for command-line
    arguments starting with a dash. This is to workaround over a known bug in
    argparse: https://bugs.python.org/issue9334"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse_args(self, args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]

        args = self._fix_args(args)

        return super().parse_args(args, namespace)

    def _fix_args(self, args):
        index = 0
        fixed_args = []
        while index < len(args):
            arg = args[index]
            action = self._find_action(arg)
            if (action is not None and index + 1 < len(args) and
                    (action.nargs is None or action.nargs == 1)):
                fixed_args.append('{}={}'.format(args[index], args[index + 1]))
                index += 2
            else:
                fixed_args.append(args[index])
                index += 1
        return fixed_args

    def _find_action(self, arg):
        for action in self._actions:
            if arg in action.option_strings:
                return action
        return None
