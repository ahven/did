"""
Copyright (C) 2020 Michał Czuczman

This file is part of Did.

Did is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

Did is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
Foobar; if not, write to the Free Software Foundation, Inc., 51 Franklin St,
Fifth Floor, Boston, MA  02110-1301  USA
"""
import re
from typing import Callable, List, Tuple, TypeVar


class UnhandledDispatchError(Exception):
    """Exception thrown when the dispatchers couldn't handle given input"""
    def __init__(self, dispatcher, item):
        super().__init__()
        self.dispatcher = dispatcher
        self.item = item

    def __str__(self):
        return "No function registered to handle given text"


ReturnType = TypeVar('ReturnType')
"""The type returned from a dispatching function"""

DispatchingFuncType = Callable[[Tuple[str, ...]], ReturnType]
"""The type of a dispatching function"""


class RegexDispatcher:
    """Decorator-based regex pattern dispatcher.
    Use this in cases when you need to dispatch an input string into one of
    several functions, depending on what regex the given string matches.
    Example usage:
      dispatcher = RegexDispatcher()

      @dispatcher.register("([0-9]+)")
      def numbers(groups):
          # called if input is digits
          return "it's a number"

      @dispatcher.register("([a-z]+)")
      def alpha(groups):
          # called if input is letters
          return "it's letters"

      def example(text):
          try:
              result = dispatcher(text)
          except UnhandledDispatchError:
              # input didn't match any of the registered functions
    """
    def __init__(self):
        self._patterns = []

    def register(self, pattern: str
                 ) -> Callable[[DispatchingFuncType], DispatchingFuncType]:
        """Return a decorator that will bind its function
        to the given regex pattern in this dispatcher"""
        regex = re.compile(pattern)

        def decorator(func: DispatchingFuncType) -> DispatchingFuncType:
            self._patterns.append((regex, func))
            return func

        return decorator

    def __call__(self, text: str) -> ReturnType:
        """Call the first registered function whose pattern matches given text.
        Return the result returned from that function.
        If there is no function registered that can handle the given input,
        then an UnhandledDispatchError is raised.
        """
        for regex, func in self._patterns:
            match = regex.search(text)
            if match:
                return func(match.groups())
        raise UnhandledDispatchError(self, text)


class TypeBasedDispatcher:
    """Decorator-based handler dispatcher based on item type.
    Use this in cases when you need to dispatch items to one of several methods
    depending on the type of the items.
    Example usage:
      class Foo: pass
      class Bar: pass

      class Example:
          dispatcher = TypeBasedDispatcher()

          @dispatcher.register(Foo)
          def handle_foo(foo: Foo):
              # called if input is Foo
              return "it's a foo"

          @dispatcher.register(Bar)
          def handle_bar(bar: Bar):
              # called if input is Bar
              return "it's a bar"

          def example(all_items):
              for item in all_items:
                  try:
                      result = self.dispatcher.handle(self, item)
                  except UnhandledDispatchError:
                      # input didn't match any of the registered functions
    """
    def __init__(self):
        self.handlers: List[Tuple[type, Callable]] = []

    def register(self, typ: type) -> Callable:
        def one_time_decorator(handler: Callable) -> Callable:
            assert typ not in self.handlers
            self.handlers.append((typ, handler))
            return handler
        return one_time_decorator

    def handle(self, obj, item):
        for typ, handler in self.handlers:
            if isinstance(item, typ):
                return handler(obj, item)
        raise UnhandledDispatchError(self, item)
