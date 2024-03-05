from __future__ import annotations

from typing import Callable, TextIO, Type, Any

import re
import sys
import readline

from nosh.token import Token, TextToken


def instantiate(tree: dict) -> Token:
    """instantiates Token tree from the dict. The structure of dict is

    {
        "class": TokenClass,
        "text": Text,
        "mark": <Mark>,
        "desc": Description,
        "action": Action,
        "leaves": [ {...}, ... ]
    }
    """

    keys = ["text", "mark", "desc", "action"]

    def _instantiate(obj: dict) -> Token:
        kwargs = {}
        for k, v in obj.items():
            if k in keys:
                kwargs[k] = v
        token: Token = obj["class"](**kwargs)
        return token

    root = _instantiate(tree)

    def _instatiate_recusive(subtree: dict, parent: Token):
        token = _instantiate(subtree)
        parent.append(token)
        if "leaves" in subtree:
            for leaf_obj in subtree["leaves"]:
                _instatiate_recusive(leaf_obj, token)

    if "leaves" in tree:
        for subtree in tree["leaves"]:
            _instatiate_recusive(subtree, root)

    return root


class SyntaxError(Exception):
    pass


class CLI:
    """CLI represents a Command Line Interface.

    CLI object holds a token tree as its completion-able commands,
    initialize completion by readline (`setup()`), and provides a
    wrapper to execute CLI (`cli()`).

    :param prombpt_cb: Callback function that returns prompt..
    :param file: TextIO object to write command descriptions.
    :param private: Any object passed to action.
    :param debug: Enable debug output.

    """
    def __init__(
        self,
        prompt_cb: Callable[[], str] | None = None,
        file: TextIO = sys.stdout,
        private: Any = None,
        debug=False,
    ):

        self.root = TextToken(text="__root__", desc="Root Token")
        self.prompt_cb = prompt_cb
        self.file = file
        self.private = private
        self.debug = debug

        # prefix acehives `edit`. If prefix_insert_index > 0,
        # self.prefix is inserted into the path with the index.
        self.prefix: list[str] = []
        self.prefix_insert_index = 0

    def _pr(self, msg, **kwargs):
        print(msg, file=self.file, **kwargs)

    @property
    def prompt(self) -> str:
        """A function set by `prompt_cb` argument of CLI."""
        if self.prompt_cb:
            return self.prompt_cb()
        return ">"

    def longest_match(self, path: list[str]) -> tuple[Token, list[Token]]:
        """Retruns the Token most matching the path, and visted
        Toekn(s) as a list.

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
        """Retruns the Token exactry matching `path`. `path` can
        consists of String and `Token` classes, e.g., InterfaceToken.

        """
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
        """Inserts Token(s) as leaves of the Token exactily matching
        the `path`.

        """
        last = self.find(path)
        last.append(*tokens)

    def set_prefix(self, prefix: list[str]):
        """Set `prefix` for linebuffer. If prefix is set, completion
        inserts the prefix into the next to the first token. For
        example, prefix is ``interface ge-0/0/0`` and linebuffer is
        ``show address``, completion runs for ``show interface
        ge-0/0/0 address``. Namely prefix exists for the `edit`
        feature.

        """
        self.prefix = prefix

    def clear_prefix(self):
        """Clear `prefix`."""
        self.prefix = []

    def complete_readline(self, text: str, state: int):
        """Wrapper to be called from readline."""
        return self.complete(readline.get_line_buffer(), text, state)

    def complete(self, linebuffer: str, text: str, state: int) -> str | None:
        """The actual completer for readline."""
        path = re.split(r"\s+", linebuffer)

        if self.debug:
            print()
            print(f"linebuffer: '{linebuffer}'")
            print(f"text:       '{text}'")
            print(f"state:      '{state}'")
            print(f"prefix:     '{self.prefix}'")
            print(f"path:       '{path}'")

        if linebuffer and self.prefix and 1 < len(path):
            path = path[:1] + self.prefix + path[1:]
            if self.debug:
                print(f"---prefix inserted---")
                print(f"path:       '{path}'")
        try:
            token, visited = self.longest_match(path)
        except SyntaxError as e:
            self._pr("\n")
            self._pr(f"  {e}")
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            self._pr(newbuffer, end="", flush=True)
            return

        candidates = token.complete(text, visited)

        if self.debug:
            visited_str = ", ".join(map(str, visited))
            print(f"visited:    '{visited_str}'")
            print(f"token:      '{token}'")
            print(f"candidates: '{candidates}'")

        if text == "":
            self._pr("\n")
            self._pr("Completions:")
            for v, h in sorted(candidates, key=lambda x: x[0]):
                self._pr("  {:16} {}".format(v, h))
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            self._pr(newbuffer, end="", flush=True)
            return

        if len(candidates) == 0:
            self._pr("\n")
            self._pr("  no valid completion")
            newbuffer = "\n{} {}".format(self.prompt, linebuffer)
            self._pr(newbuffer, end="", flush=True)
            return

        compeletion_candidates = list(
            filter(lambda x: not re.match(r"<.*>", x[0]), candidates)
        )  # omit mark of <TEXT>

        if state < len(compeletion_candidates):
            return compeletion_candidates[state][0] + " "

    def execute(self, linebuffer: str):
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
            self._pr(f"  {linebuffer} < invalid syntax")
            self._pr("", flush=True)
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
                self._pr("")
                self.execute(line)

            except KeyboardInterrupt:
                self._pr("")
                self._pr("")
                continue

            except EOFError:
                break