from __future__ import annotations

from .node import *

import re
import readline


class Nosh:
    def __init__(self, prompt_cb: Callable[[], str] | None = None):
        self.root = Node("root", "Root Node")
        self.prompt_cb = prompt_cb

    @property
    def prompt(self) -> str:
        if self.prompt_cb:
            return self.prompt_cb()
        return ">"

    def longest_match(self, prefix: list[str]) -> Node:
        ptr = self.root
        for text in prefix:
            next_ptr = ptr.find_leaf(text)
            if not next_ptr:
                break
            ptr = next_ptr
        return ptr

    def complete(self, text: str, state: int):
        linebuffer = readline.get_line_buffer()
        prefix = re.split(r"\s+", linebuffer)
        node = self.longest_match(prefix)
        candidates = node.compelte(linebuffer, text)

        if len(candidates) == 0 and not node.action:
            print("\n")
            print("  no valid completion")
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            print(newbuffer, end="", flush=True)
            return

        if text == "":
            print("\n")
            if node.action:
                print("  {:16} {}".format("<[Enter]>", "Execute this command"))
            for v, h in candidates:
                print("  {:16} {}".format(v, h))
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            print(newbuffer, end="", flush=True)
            return

        if state < len(candidates):
            return candidates[state][0] + " "

    def execute(self, linebuffer):
        args = re.split(r"\s+", linebuffer.strip())
        last = args[len(args) - 1]
        node = self.longest_match(args)

        if node == self.root and linebuffer.strip() == "":
            return

        if not node.action or not node.match(last):
            # Node to be executed must have action, and
            # the last argument must match Node.
            print()
            print(f"  {linebuffer} < invalid syntax")
            print(flush=True)
            return
        node.action(args)

    def start_cli(self):
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
