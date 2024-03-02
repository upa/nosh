from __future__ import annotations
import typing

from .node import *

import io
import re
import sys
import readline


class Nosh:
    def __init__(self, prompt_cb: Callable[[], str] | None = None,
                 file: typing.TextIO = sys.stdout):
        self.root = Node("__root__", "Root Node")
        self.prompt_cb = prompt_cb
        self.file = file

    def print(self, msg, **kwargs):
        print(msg, file = self.file, **kwargs)

    @property
    def prompt(self) -> str:
        if self.prompt_cb:
            return self.prompt_cb()
        return ">"

    def longest_match(self, prefix: list[str]) -> Node:
        node = self.root
        for text in prefix:
            next_node = node.match_leaf(text)
            if not next_node:
                break
            node = next_node
        return node

    def find(self, path: list[str|Node]) -> Node:
        node = self.root
        for p in path:
            next_node = node.find_leaf(p)
            if not next_node:
                break
            node = next_node
        if node == self.root:
            raise ValueError(f"path {path} does not exist")
        return node
        
    def append(self, *args: Node):
        self.root.append(*args)

    def complete(self, text: str, state: int):
        linebuffer = readline.get_line_buffer()
        prefix = re.split(r"\s+", linebuffer)
        node = self.longest_match(prefix)
        candidates = node.compelte(linebuffer, text)

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
        ) # omit indicators of <INDICATOR> from candidates

        if state < len(compeletion_candidates):
            return compeletion_candidates[state][0] + " "

    def execute(self, linebuffer):
        args = re.split(r"\s+", linebuffer.strip())
        last = args[len(args) - 1]
        node = self.longest_match(args)

        if node == self.root and linebuffer.strip() == "":
            return

        if not node.action or not node.match(last):
            # Node to be executed must have action, and
            # the last argument must match the last node.
            self.print("")
            self.print(f"  {linebuffer} < invalid syntax")
            self.print("", flush=True)
            return

        node.action(args)

    def start_cli(self):
        readline.set_completer_delims(" ")
        readline.set_completer(self.complete)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("space: complete")
        readline.parse_and_bind("?: complete")

        while True:
            try:
                line = input("{} ".format(self.prompt))
                self.execute(line)

            except EOFError:
                break
