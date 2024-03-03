from __future__ import annotations

from typing import Callable, TextIO, Type

import re
import sys
import readline

from nosh.node import Node, StaticNode


class SyntaxError(Exception):
    pass


class CLI:
    def __init__(
        self,
        prompt_cb: Callable[[], str] | None = None,
        file: TextIO = sys.stdout,
        debug=False,
    ):
        self.root = StaticNode(token="__root__", desc="Root Node")
        self.prompt_cb = prompt_cb
        self.file = file
        self.debug = debug

    def print(self, msg, **kwargs):
        print(msg, file=self.file, **kwargs)

    @property
    def prompt(self) -> str:
        if self.prompt_cb:
            return self.prompt_cb()
        return ">"

    def longest_match(self, path: list[str]) -> tuple[Node, list[Node]]:
        """Retruns the Node most matching the path. This function is
        used for compleition.

        """
        visited = []
        node = self.root
        for i, token in enumerate(path):
            visited.append(node)
            next_node = node.match_leaf(token)
            if not next_node:
                break
            node = next_node

        if i + 1 != len(path):
            raise SyntaxError(f"{' '.join(path[:i])} < syntax error")

        return node, visited

    def find(self, path: list[str | Type[Node]]) -> Node:
        """Retruns the Node exactry matching the path."""
        node = self.root
        for idx, token in enumerate(path):
            next_node = node.find_leaf(token)
            if not next_node:
                if idx < (len(path) - 1):
                    raise ValueError(f"no node path '{path}'")
                break
            node = next_node
        return node

    def append(self, *args: Node):
        """Appends Node(s) to the top of this CLI."""
        self.root.append(*args)

    def insert(self, path: list[str | Type[Node]], *nodes: Node):
        """Inserts Node(s) as leaves of a Node exactily matching the
        path."""
        last = self.find(path)
        last.append(*nodes)

    def complete_readline(self, token: str, state: int):
        return self.complete(readline.get_line_buffer(), token, state)

    def complete(self, linebuffer: str, token: str, state: int):
        """The actual completer for readline."""
        path = re.split(r"\s+", linebuffer)
        try:
            node, visited = self.longest_match(path)
        except SyntaxError as e:
            self.print("\n")
            self.print(f"  {e}")
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            self.print(newbuffer, end="", flush=True)
            return

        candidates = node.complete(linebuffer, token, visited)

        if self.debug:
            visited_str = ", ".join(map(str, visited))
            print()
            print(f"linebuffer: '{linebuffer}'")
            print(f"token:      '{token}'")
            print(f"path:       '{path}'")
            print(f"visited:    '{visited_str}'")
            print(f"node:       '{node}'")
            print(f"candidates: '{candidates}'")

        if token == "":
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
        """Executes action of a Node matching the linebuffer"""
        args = re.split(r"\s+", linebuffer.strip())
        last = args[len(args) - 1]
        node, _ = self.longest_match(args)

        if node == self.root and linebuffer.strip() == "":
            # empty linebuffer.
            return

        if not node.action or not node.match(last):
            # Node to be executed must have action, and
            # the last argument must match the last node.
            self.print("")
            self.print(f"  {linebuffer} < invalid syntax")
            self.print("", flush=True)
            return

        node.action(args)

    def setup(self):
        """Setup readline completer and parse_and_bind. Call this
        function of other CLI instances can switch completions, namely
        modes.

        """
        readline.set_completer_delims(" ")
        readline.set_completer(self.complete_readline)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("space: complete")
        readline.parse_and_bind("?: complete")

    def cli(self):
        """Start to emulates a CLI."""
        self.setup()
        while True:
            try:
                line = input("{} ".format(self.prompt))
                self.execute(line)

            except KeyboardInterrupt:
                self.print("")
                continue
            except EOFError:
                break
