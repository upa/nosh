from __future__ import annotations

from typing import Callable, TextIO, Type, Any

import re
import sys
import readline

from nosh.token import Token, StaticToken


class SyntaxError(Exception):
    pass


class CLI:
    def __init__(
        self,
        prompt_cb: Callable[[], str] | None = None,
        file: TextIO = sys.stdout, private: Any = None,
        debug=False,
    ):
        self.root = StaticToken(text="__root__", desc="Root Token")
        self.prompt_cb = prompt_cb
        self.file = file
        self.private = private
        self.debug = debug

    def print(self, msg, **kwargs):
        print(msg, file=self.file, **kwargs)

    @property
    def prompt(self) -> str:
        if self.prompt_cb:
            return self.prompt_cb()
        return ">"

    def longest_match(self, path: list[str]) -> tuple[Token, list[Token]]:
        """Retruns the Token most matching the path. This function is
        used for compleition.

        """
        visited = []
        token = self.root
        for i, text in enumerate(path):
            visited.append(token)
            next_token = token.match_leaf(text)
            if not next_token:
                break
            token = next_token

        if i + 1 != len(path):
            raise SyntaxError(f"{' '.join(path[:i])} < syntax error")

        return token, visited

    def find(self, path: list[str | Type[Token]]) -> Token:
        """Retruns the Token exactry matching the path."""
        token = self.root
        for idx, text in enumerate(path):
            next_token = token.find_leaf(text)
            if not next_token:
                if idx < (len(path) - 1):
                    raise ValueError(f"no token path '{path}'")
                break
            token = next_token
        return token

    def append(self, *args: Token):
        """Appends Token(s) to the top of this CLI."""
        self.root.append(*args)

    def insert(self, path: list[str | Type[Token]], *tokens: Token):
        """Inserts Token(s) as leaves of a Token exactily matching the
        path."""
        last = self.find(path)
        last.append(*tokens)

    def complete_readline(self, text: str, state: int):
        return self.complete(readline.get_line_buffer(), text, state)

    def complete(self, linebuffer: str, text: str, state: int):
        """The actual completer for readline."""
        path = re.split(r"\s+", linebuffer)
        try:
            token, visited = self.longest_match(path)
        except SyntaxError as e:
            self.print("\n")
            self.print(f"  {e}")
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            self.print(newbuffer, end="", flush=True)
            return

        candidates = token.complete(linebuffer, text, visited)

        if self.debug:
            visited_str = ", ".join(map(str, visited))
            print()
            print(f"linebuffer: '{linebuffer}'")
            print(f"text:       '{text}'")
            print(f"path:       '{path}'")
            print(f"visited:    '{visited_str}'")
            print(f"token:      '{token}'")
            print(f"candidates: '{candidates}'")

        if text == "":
            self.print("\n")
            for v, h in candidates:
                self.print("  {:16} {}".format(v, h))
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            self.print(newbuffer, end="", flush=True)
            return

        if len(candidates) == 0:
            self.print("\n")
            self.print("  no valid completion")
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            self.print(newbuffer, end="", flush=True)
            return

        compeletion_candidates = list(
            filter(lambda x: not re.match(r"<.*>", x[0]), candidates)
        )  # omit references of <REFERENCE>

        if state < len(compeletion_candidates):
            return compeletion_candidates[state][0] + " "

    def execute(self, linebuffer):
        """Executes action of a Token matching the linebuffer"""
        args = re.split(r"\s+", linebuffer.strip())
        last = args[len(args) - 1]
        token, _ = self.longest_match(args)

        if token == self.root and linebuffer.strip() == "":
            # empty linebuffer.
            return

        if not token.action or not token.match(last):
            # Token to be executed must have action, and
            # the last argument must match the last token.
            self.print("")
            self.print(f"  {linebuffer} < invalid syntax")
            self.print("", flush=True)
            return

        token.action(self.private, args)

    def setup(self):
        """Setup readline completer and parse_and_bind. Call this
        function of other CLI instances overwrites completions. It
        whould enable changing modes (global <-> configure), for
        example.
        """
        readline.set_completer_delims(" ")
        readline.set_completer(self.complete_readline)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("space: complete")
        readline.parse_and_bind("?: complete")

    def cli(self):
        """Start to emulates shell interactions."""
        self.setup()
        while True:
            try:
                line = input("{} ".format(self.prompt))
                self.print("")
                self.execute(line)

            except KeyboardInterrupt:
                self.print("")
                self.print("")
                continue

            except EOFError:
                break
