from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Any

import re
import ipaddress

import ifaddr


class Token(ABC):
    """Abstract class for Token classes.
    """

    @property
    @abstractmethod
    def action(self) -> Callable[[Any, list[str]]] | None:
        """Return action function if registered."""
        pass

    @property
    @abstractmethod
    def text(self) -> str:
        """Retrun text."""
        pass

    @abstractmethod
    def complete(self, text: str, visited: list[Token]) -> list[tuple[str, str]]:
        """Return candidates, list of ("text", "desc"), for completion
        of leaf Tokens.

        """
        pass

    @abstractmethod
    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        """Retrun candidates, list of ("text", "desc"), for this
        Token. This function is called from ``complete()`` of the
        parent token."""
        pass

    @abstractmethod
    def match(self, text: str) -> bool:
        """Return true if `text` exactly match this Token."""
        pass

    @abstractmethod
    def append(self, *args: Token):
        """Append Tokens as leaf Tokens to this Token."""
        pass

    @abstractmethod
    def match_leaf(self, text: str) -> Token | None:
        """Return Token, which matches `text`, from leaf Tokens,
        otherwise None."""
        pass

    @abstractmethod
    def find_leaf(self, p: str | type[Token]) -> Token | None:
        """Return a Token, which matches `p` (`text` or `Token`
        class), from leaf Tokens, otherwise None.

        """
        
        pass


class BasicToken(Token):
    """Basic Token is a super class for a cli token. Concrete Token
    classes should inehrit this class, and implement their own
    ``match()`` and ``compelete_candidates()`` methods.

    :param text: token text of this token, e.g., `show`, `route-map`, etc.
    :param mark: like `<MARK>` that indicates what this token is (if text is not set).
    :param desc: description string.
    :param action: callback function if this token is executed.
    """

    def __init__(
        self,
        text: str = "",
        mark: str = "",
        desc: str = "",
        action: Callable[[Any, list[str]]] | None = None,
    ):
        self._text = text
        self.mark = mark
        self.desc = desc
        self.leaves: list[Token] = []
        self._action = action

        if self.mark and not re.match(r"<.*>", self.mark):
            raise ValueError("mark must be <TEXT> format")

    def __str__(self):
        return self.text

    @property
    def text(self) -> str:
        return self._text

    @property
    def action(self) -> Callable[[Any, list[str]]] | None:
        if self._action:
            return self._action
        return None

    @classmethod
    def must_have(cls, key: str, kwargs: dict):
        if not key in kwargs:
            raise ValueError(f"{cls.__name__} must have {key}")

    @classmethod
    def must_not_have(cls, key: str, kwargs: dict):
        if key in kwargs:
            raise ValueError(f"{cls.__name__} must not have {key}")

    def complete(self, text: str, visited: list[Token]) -> list[tuple[str, str]]:
        """This method returns list of candidate values of leaf tokens
        and their help strings.

        """

        if self.match(text) and not self in visited:
            """text matches this token. Thus, return the text as this
            token.

            Note that StringToken class matches any string, even when
            this complete() intend to complete leaf tokens. Consider a
            case where linebuffer is 'ping example.com', text is
            'example.com', and this object is
            StringToken. self.match(text) returns True although we
            need to returns candidates of leaf tokens, e.g., 'ping
            example.com count' <- we need to return 'count' as a
            candidate on this completion. Thus, we need to check (self
            in visited). If it is ture, it means that this StringToken
            is already matched, so we need to dig the leaf tokens."""
            return [(text, self.desc)]

        candidates: list[tuple[str, str]] = []
        if text == "" and self.action:
            candidates.append(("<[Enter]>", "Execute this command"))

        for leaf in self.leaves:
            if leaf in visited:
                continue
            candidates += leaf.completion_candidates(text)
        return candidates

    def append(self, *args: Token):
        """Appends leaf tokens"""
        for arg in args:
            self.leaves.append(arg)

    def match_leaf(self, text: str) -> Token | None:
        """returns leaf Token most matching text"""
        for leaf in self.leaves:
            if leaf.match(text):
                return leaf
        return None

    def find_leaf(self, p: str | type[Token]) -> Token | None:
        """retruns leaf Token having the same text or the same Class"""
        if isinstance(p, str):
            for leaf in self.leaves:
                if leaf.text == p:
                    return leaf
            return None

        for leaf in self.leaves:
            if type(leaf) == p:
                return leaf
        return None


class TextToken(BasicToken):
    """Token representing a static text.

    TextToken must have `text` and not have `mark`.
    """

    def __init__(self, **kwargs):
        self.must_have("text", kwargs)
        self.must_not_have("mark", kwargs)
        super().__init__(**kwargs)

    def __str__(self):
        return self.text

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        candidates: list[tuple[str, str]] = []

        if self.mark:
            candidates.append((self.mark, self.desc))

        if self.text.startswith(text):
            candidates.append((self.text, self.desc))

        return candidates

    def match(self, text: str) -> bool:
        """returns True if `text` extactly matches this Token."""
        return self.text == text


class InterfaceToken(BasicToken):
    """Token representing interfaces.

    InterfaceToken must not have `text`. Intead, it has `mark`
    ``<interface-name>`` by default. Completion candidates are
    interface names retrieved by ``ifaddr``.

    """

    def __init__(self, **kwargs):
        self.must_not_have("text", kwargs)
        kwargs.setdefault("mark", "<interface-name>")
        kwargs.setdefault("desc", "Name to identify an interface")
        super().__init__(**kwargs)

    def __str__(self):
        return "<Interface>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:

        candidates: list[tuple[str, str]] = []
        if self.mark:
            candidates.append((self.mark, self.desc))

        for adapter in ifaddr.get_adapters():
            if adapter.name.startswith(text):
                candidates.append((adapter.name, ""))
        return candidates

    def match(self, text: str) -> bool:
        for adapter in ifaddr.get_adapters():
            if adapter.name == text:
                return True
        return False


class StringToken(BasicToken):
    """Token representing a string.

    StringToken must not have `text`. Instead, it must have `mark`.
    For example. StringToken under TextToken(``route-map``) would have
    `mark` ``<route-map>``.

    """

    def __init__(self, **kwargs):
        self.must_not_have("text", kwargs)
        self.must_have("mark", kwargs)
        super().__init__(**kwargs)

    def __str__(self):
        return "<String>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.mark, self.desc)]

    def match(self, text: str) -> bool:
        if re.match(r"[0-9a-zA-Z_\-]+", text):
            return True
        return False


class IntToken(BasicToken):
    """Token representing integer.

    IntToekn must not have `text`. It have mark ``<int>`` by default.

    """

    def __init__(self, **kwargs):
        self.must_not_have("text", kwargs)
        kwargs.setdefault("mark", "<int>")
        kwargs.setdefault("desc", "Integer")
        super().__init__(**kwargs)

    def __str__(self):
        return "<Int>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.mark, self.desc)]

    def match(self, text: str) -> bool:
        try:
            int(text)
            return True
        except ValueError:
            return False


class IPv4AddressToken(BasicToken):
    """Token representing IPv4Address."""

    def __init__(self, **kwargs):
        self.must_not_have("text", kwargs)
        kwargs.setdefault("mark", "<ipv4-address>")
        kwargs.setdefault("desc", "IPv4 address")
        super().__init__(**kwargs)

    def __str__(self):
        return "<IPv4Address>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.mark, self.desc)]

    def match(self, text: str) -> bool:
        try:
            ipaddress.IPv4Address(text)
            return True
        except ipaddress.AddressValueError:
            return False


class IPv6AddressToken(BasicToken):
    """Token representing IPv6Address."""

    def __init__(self, **kwargs):
        self.must_not_have("text", kwargs)
        kwargs.setdefault("mark", "<ipv6-address>")
        kwargs.setdefault("desc", "IPv6 address")
        super().__init__(**kwargs)

    def __str__(self):
        return "<IPv6Address>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.mark, self.desc)]

    def match(self, text: str) -> bool:
        try:
            ipaddress.IPv6Address(text)
            return True
        except ipaddress.AddressValueError:
            return False


class InterfaceAddressToken(BasicToken):
    """Token representing InterfaceAddress.

    This token matches IPv4-ADDRESS/Preflen or IPv6-ADDRESS/preflen.
    """

    def __init__(self, **kwargs):
        self.must_not_have("text", kwargs)
        kwargs.setdefault("mark", "<address>")
        kwargs.setdefault("desc", "Address/Prefixlen")
        super().__init__(**kwargs)

    def __str__(self):
        return "<InterfaceAddress>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.mark, self.desc)]

    def match(self, text: str) -> bool:

        if not "/" in text:
            return False

        try:
            ipaddress.ip_interface(text)
            return True
        except ValueError:
            return False
