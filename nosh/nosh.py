
from __future__ import annotations

from .node import *

import re
import readline


class Nosh():
    def __init__(self):
        self.root = Node("root", "Root Node")

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
        prefix = re.split(r'\s+', linebuffer)
        node = self.longest_match(prefix)
        candidates = node.compelte(linebuffer, text)

        if len(candidates) == 0 and not node.action:
            print("\n")
            print("  no valid completion")
            newbuffer = "\n> {}".format(linebuffer)
            print(newbuffer, end="", flush=True)
            return 

        if text == "":
            print("\n")
            if node.action:
                print("  {:16} {}".format("<[Enter]>", "Execute this command"))
            for v, h in candidates:
                print("  {:16} {}".format(v, h))
            newbuffer = "\n> {}".format(linebuffer)
            print(newbuffer, end="", flush=True)
            return

        if state < len(candidates):
            return candidates[state][0] + " "

    def execute(self, linebuffer):
        prefix = re.split(r'\s+', linebuffer.strip())
        node = self.longest_match(prefix)
        if node == self.root:
            return
        if not node.action:
            print(f"{linebuffer} < invalid syntax")
            return
        node.action(prefix)

    
    def start_cli(self):
        readline.set_completer(self.complete)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("space: complete")
        readline.parse_and_bind("?: complete")

        while True:
            try:
                line = input("> ")
                self.execute(line)

            except EOFError:
                break
