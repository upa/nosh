from __future__ import annotations
from abc import ABC, abstractmethod, abstractproperty
from typing import Callable, Type

import re
import sys
import ipaddress

import ifaddr


def instantiate(tree: dict) -> Node:
    """ instantiates Node tree from the dict. The structure of dict is

    {
        "class": NodeClass,
        "args"
    }

    """
    

class Node(ABC):
    @property
    @abstractmethod
    def action(self) -> Callable[[list[str]]] | None:
        """Return action function if registered."""
        pass

    @property
    @abstractmethod
    def token(self) -> str:
        """Retrun token"""
        pass

    @abstractmethod
    def complete(slef, linebuffer: str, token: str) -> list[tuple[str, str]]:
        """Return candidates, list of ("token", "help") for completion
        of leaf Nodes.

        """
        pass

    @abstractmethod
    def completion_candidates(self, token: str) -> list[tuple[str, str]]:
        """Retrun candidates, list of ("token", "help") for this Node."""
        pass

    @abstractmethod
    def match(self, token: str) -> bool:
        """Return true if `token` exactly match this Node."""
        pass

    @abstractmethod
    def append(self, *args: Node):
        """Append Nodes as leaf Nodes to this Node."""
        pass

    @abstractmethod
    def match_leaf(self, token: str) -> Node | None:
        """Return Node, which matches token, from leaf Nodes, otherwise
        None."""
        pass

    @abstractmethod
    def find_leaf(self, p: str | type[Node]) -> Node | None:
        """Return Node, which matches p (token or Node class), from
        leaf Nodes, otherwise None.

        """
        pass


class BasicNode(Node):
    """Basic Node representing cli node. Concerent Node classes should
    inehrits this class, and implement their own match and
    compelete_candidates methods.

    """

    def __init__(
        self,
        token: str = "",
        desc: str = "",
        reference: str = "",
        reference_desc: str = "",
        action: Callable[[list[str]]] | None = None,
    ):
        self._token = token
        self.desc = desc
        self.reference = reference
        self.reference_desc = reference_desc
        self.leafs: list[Node] = []
        self._action = action

        if self.reference and not re.match(r"<.*>", self.reference):
            raise ValueError("reference must be <REFERENCE>")

    def __str__(self):
        return self.token

    @property
    def token(self) -> str:
        return self._token

    @property
    def action(self) -> Callable[[list[str]]] | None:
        if self._action:
            return self._action
        return None

    def complete(self, linebuffer: str, token: str) -> list[tuple[str, str]]:
        """This method returns list of candidate values of leaf nodes
        and their help strings.

        """

        if self.match(token):
            """linebuffer is "prefix token", not "prefix... token ",
            which search the next node. So, returns this node as the
            candidate."""
            return [(token, self.desc)]

        candidates: list[tuple[str, str]] = []
        if self.action:
            candidates.append(("<[Enter]>", "Execute this command"))

        for leaf in self.leafs:
            candidates += leaf.completion_candidates(token)
        return candidates

    def append(self, *args: Node):
        """Appends leaf nodes"""
        for arg in args:
            self.leafs.append(arg)

    def match_leaf(self, token: str) -> Node | None:
        """returns leaf Node most matching token"""
        for leaf in self.leafs:
            if leaf.match(token):
                return leaf
        return None

    def find_leaf(self, p: str | type[Node]) -> Node | None:
        """retruns leaf Node having the same token or the same Class"""
        if isinstance(p, str):
            for leaf in self.leafs:
                if leaf.token == p:
                    return leaf
            return None

        for leaf in self.leafs:
            if type(leaf) == p:
                return leaf
        return None


class StaticNode(BasicNode):
    """Static Node representing cli node"""

    def __init__(
        self,
        token: str,
        desc: str,
        reference: str = "",
        reference_desc: str = "",
        action: Callable[[list[str]]] | None = None,
    ):
        super().__init__(
            token,
            desc,
            reference=reference,
            reference_desc=reference_desc,
            action=action,
        )

        if self.reference and not re.match(r"<.*>", self.reference):
            raise ValueError("reference must be <REFERENCE>")

    def __str__(self):
        return self.token

    def completion_candidates(self, token: str) -> list[tuple[str, str]]:
        candidates: list[tuple[str, str]] = []

        if self.reference:
            candidates.append((self.reference, self.reference_desc))

        if self.token.startswith(token):
            candidates.append((self.token, self.desc))

        return candidates

    def match(self, token: str) -> bool:
        """returns True if `token` extactly matches this Node."""
        return self.token == token


class InterfaceNode(BasicNode):
    """Node representing interfaces"""

    def __init__(self, **kwargs):
        if "token" in kwargs:
            raise ValueError("InterfaceNode must not have token")

        kwargs.setdefault("reference", "<interface-name>")
        kwargs.setdefault("reference_desc", "Name to identify an interface")
        super().__init__(**kwargs)


    def __str__(self):
        return "<Interface>"

    def completion_candidates(self, token: str) -> list[tuple[str, str]]:

        candidates: list[tuple[str, str]] = []
        if self.reference:
            candidates.append((self.reference, self.reference_desc))

        for adapter in ifaddr.get_adapters():
            if adapter.name.startswith(token):
                candidates.append((adapter.name, ""))
        return candidates

    def match(self, token: str) -> bool:
        for adapter in ifaddr.get_adapters():
            if adapter.name == token:
                return True
        return False


class StringNode(BasicNode):
    """Node representing string"""

    def __init__(self, **kwargs):
        if "token" in kwargs:
            raise ValueError("StringNode must not have token")
        if not "reference" in kwargs:
            raise ValueError("StringNode must have reference")
        super().__init__(**kwargs)

    def __str__(self):
        return "<String>"

    def completion_candidates(self, token: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, token: str) -> bool:
        if re.match(r"[0-9a-zA-Z_\-]+", token):
            return True
        return False


class IntNode(BasicNode):
    """Node representing integer"""

    def __init__(self,**kwargs):
        kwargs.setdefault("reference", "<int>")
        kwargs.setdefault("reference_desc", "Integer")
        super().__init__(**kwargs)            

    def __str__(self):
        return "<Int>"

    def completion_candidates(self, token: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, token: str) -> bool:
        try:
            int(token)
            return True
        except ValueError:
            return False


class IPv4AddressNode(BasicNode):
    """Node representing IPv4Address"""

    def __init__(self, **kwargs):
        kwargs.setdefault("reference", "<ipv4-address>")
        kwargs.setdefault("reference_desc", "IPv4 address")
        super().__init__(**kwargs)

    def __str__(self):
        return "<IPv4Address>"

    def completion_candidates(self, token: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, token: str) -> bool:
        try:
            ipaddress.IPv4Address(token)
            return True
        except ipaddress.AddressValueError:
            return False


class IPv6AddressNode(BasicNode):
    """Node representing IPv6Address"""

    def __init__(self, **kwargs):
        kwargs.setdefault("reference", "<ipv6-address>")
        kwargs.setdefault("reference_desc", "IPv6 address")
        super().__init__(**kwargs)

    def __str__(self):
        return "<IPv6Address>"

    def completion_candidates(self, token: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, token: str) -> bool:
        try:
            ipaddress.IPv6Address(token)
            return True
        except ipaddress.AddressValueError:
            return False


class InterfaceAddressNode(BasicNode):
    """Node representing IPv6Address"""

    def __init__(self, **kwargs):
        kwargs.setdefault("reference", "<address>")
        kwargs.setdefault("reference_desc", "Address/Prefixlen")
        super().__init__(**kwargs)

    def __str__(self):
        return "<InterfaceAddress>"

    def completion_candidates(self, token: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, token: str) -> bool:

        if not "/" in token:
            return False

        try:
            ipaddress.ip_interface(token)
            return True
        except ValueError:
            return False
