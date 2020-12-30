import datetime
import re
import shlex
from typing import Generator, List, Optional, Union

from pytimeparse.timeparse import timeparse

from did.worktime import PaidBreakConfig


def parse_timedelta(time_expression: str) -> datetime.timedelta:
    seconds: Optional[Union[int, float]] = timeparse(time_expression)
    if seconds is None:
        raise ValueError("Invalid time interval expression: {}"
                         .format(time_expression))
    else:
        return datetime.timedelta(seconds=seconds)


class LineParser:
    def __init__(self, pattern, action):
        self.regex = re.compile(pattern)
        self.action = action

    def match(self, line):
        return self.regex.match(line)


class Event:
    def __init__(self, timestamp: datetime.datetime, text: str):
        self.timestamp = timestamp
        self.text = text


class SetParam:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class DeletePaidBreak:
    def __init__(self, name):
        self.name = name


class InvalidLine(Exception):
    pass


class PaidBreakParseError(InvalidLine):
    def __init__(self, message):
        super().__init__('Error in \"config paid_break\": {}'.format(message))


class LineParserRegistry:
    def __init__(self):
        self.line_parsers = []  # type: List[LineParser]

    def register(self, pattern):
        def wrap(func):
            self.line_parsers.append(LineParser(pattern, func))
            return func
        return wrap


ParsedActionType = Optional[
    Union[Event, SetParam, PaidBreakConfig, DeletePaidBreak]]


class Parser:
    line_parsers = LineParserRegistry()

    @line_parsers.register(
        r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?: (.+)$")
    def _event_line(self, match) -> ParsedActionType:
        parts = list(match.groups())
        text = parts.pop()
        for i in range(len(parts)):
            if parts[i] is None:
                parts[i] = 0
            else:
                parts[i] = int(parts[i])
        year, month, day, hour, minute, second = parts
        dt = datetime.datetime(year, month, day, hour, minute, second)
        return Event(dt, text)

    @line_parsers.register(r"#|\s*$")
    def _ignore_line(self, match) -> ParsedActionType:
        del match
        return None

    @line_parsers.register(r"config\s+([a-z_][a-z0-9_]*)\s*=\s*(.*)$")
    def _set_config_param(self, match) -> ParsedActionType:
        name = match.group(1)
        value = match.group(2).strip()
        return SetParam(name, value)

    @line_parsers.register(r"config\s+paid_break\s+(.*)")
    def _paid_break_config(self, match) -> ParsedActionType:
        args = shlex.split(match.group(1))
        if len(args) == 0:
            raise PaidBreakParseError("No arguments")

        paid_break = PaidBreakConfig(name=args.pop(0))

        def set_uniquely(attr, new_value):
            if getattr(paid_break, attr) is not None:
                raise PaidBreakParseError(
                    "Repeated setting of {} (to {} and {})"
                    .format(attr, repr(getattr(paid_break, attr)),
                            repr(new_value)))
            setattr(paid_break, attr, new_value)

        if len(args) == 0:
            raise PaidBreakParseError("Too little arguments")

        if args[0] == 'delete':
            if len(args) > 1:
                raise PaidBreakParseError("Extra arguments")
            return DeletePaidBreak(paid_break.name)

        for arg in args:
            if arg == 'daily':
                set_uniquely("max_occurrences_per_day", 1)
            elif arg == 'splittable':
                set_uniquely("splittable", True)
            elif arg == 'one_chunk':
                set_uniquely("splittable", False)
            elif '=' in arg:
                variable, value = arg.split('=', maxsplit=1)
                if variable == 'min_day_work_time':
                    set_uniquely("min_day_total_work_time",
                                 parse_timedelta(value))
                elif variable == 'earn_work_time':
                    set_uniquely("earned_after_preceding_work_time",
                                 parse_timedelta(value))
                else:
                    raise PaidBreakParseError('Not recognized parameter "{}"'
                                              .format(variable))
            else:
                try:
                    set_uniquely("duration", parse_timedelta(arg))
                except ValueError:
                    raise PaidBreakParseError("Not recognized argument \"{}\""
                                              .format(arg))

        if paid_break.duration is None:
            raise PaidBreakParseError("Missing setting of duration")
        if paid_break.splittable is None:
            raise PaidBreakParseError("Missing setting of \"splittable\" or "
                                      "\"one_chunk\"")
        return paid_break

    def process_line(self, line) -> ParsedActionType:
        for line_parser in self.line_parsers.line_parsers:
            match = line_parser.match(line)
            if match:
                return line_parser.action(self, match)
        raise InvalidLine("Invalid line: {}".format(line))


def job_reader(path) -> Generator[ParsedActionType, None, None]:
    """
    Generator reading lines from a work log file.

    In each iteration the generator returns a (datetime, text) tuple.
    """
    try:
        with open(path, "r") as f:
            parser = Parser()
            for line in f:
                result = parser.process_line(line)
                if result is not None:
                    yield result
    except IOError as err:
        print("Error opening/reading from file '{0}': {1}"
              .format(err.filename, err.strerror))


class JobListWriter:
    def __init__(self, filename):
        self.filename = filename

    def append(self, date, name):
        try:
            with open(self.filename, "a") as f:
                f.write("%d-%02d-%02d %02d:%02d:%02d: %s\n" %
                        (date.year, date.month, date.day,
                         date.hour, date.minute, date.second, name))
        except IOError as err:
            print("Error opening/writing to file '{0}': {1}"
                  .format(err.filename, err.strerror))
