from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Callable

import re
import sys
import ipaddress

import ifaddr


def pr_err(msg: str):
    print(msg, file=sys.stderr)


class Node(metaclass=ABCMeta):
    @property
    @abstractmethod
    def action(self) -> Callable[[list[str]]] | None:
        """Return action function if registered. """
        pass

    @abstractmethod
    def complete(slef, linebuffer: str, text: str) -> list[tuple[str, str]]:
        """Return candidates, list of ("text", "help") for completion
        of leaf Nodes.

        """
        pass

    @abstractmethod
    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        """Retrun candidates, list of ("text", "help") for this Node."""
        pass

    @abstractmethod
    def match(self, text: str) -> bool:
        """Return true if `text` exactly match this Node."""
        pass

    @abstractmethod
    def append(self, *args: Node):
        """Append Nodes as leaf Nodes to this Node."""
        pass

    @abstractmethod
    def match_leaf(self, text: str) -> Node | None:
        """Return Node, which matches text, from leaf Nodes, otherwise
        None."""
        pass

    @abstractmethod
    def find_leaf(self, p: str | Node) -> Node | None:
        """Retru Nodee, which matches p (text or Class), from leaf
        Nodes, othersize None."""
        pass


class BasicNode(Node):
    """Basic Node representing cli node. Concerent Node classes should
    inehrits this class, and implement their own match and
    compelete_candidates methods.

    """

    def __init__(
        self,
        text: str,
        desc: str,
        reference: str = "",
        reference_desc: str = "",
        action: Callable[[list[str]]] | None = None,
    ):
        self.text = text
        self.desc = desc
        self.reference = reference
        self.reference_desc = reference_desc
        self.leafs: list[Node] = []
        self.exec_action = action

        if self.reference and not re.match(r"<.*>", self.reference):
            raise ValueError("reference must be <REFERENCE>")

    def __str__(self):
        return self.text

    @property
    def action(self) -> Callable[[list[str]]] | None:
        if self.exec_action:
            return self.exec_action
        return None

    def complete(self, linebuffer: str, text: str) -> list[tuple[str, str]]:
        """This method returns list of candidate values of leaf nodes
        and their help strings.

        """

        if self.match(text):
            """ linebuffer is "prefix text", not "prefix... text ",
            which search the next node. So, returns this node as the
            candidate."""
            return [(text, self.desc)]

        candidates: list[tuple[str, str]] = []
        if self.action:
            candidates.append(("<[Enter]>", "Execute this command"))

        for leaf in self.leafs:
            candidates += leaf.completion_candidates(text)
        return candidates

    def append(self, *args: Node):
        """Appends leaf nodes"""
        for arg in args:
            self.leafs.append(arg)

    def match_leaf(self, text: str) -> Node | None:
        """returns leaf Node most matching text"""
        for leaf in self.leafs:
            if leaf.match(text):
                return leaf
        return None

    def find_leaf(self, p: str | Node) -> Node | None:
        """retruns leaf Node having the same text or the same Class"""
        if isinstance(p, str):
            for leaf in self.leafs:
                if leaf.text == p:
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
        text: str,
        desc: str,
        reference: str = "",
        reference_desc: str = "",
        action: Callable[[list[str]]] | None = None,
    ):
        super().__init__(
            text,
            desc,
            reference=reference,
            reference_desc=reference_desc,
            action=action,
        )

        if self.reference and not re.match(r"<.*>", self.reference):
            raise ValueError("reference must be <REFERENCE>")

    def __str__(self):
        return self.text

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        candidates: list[tuple[str, str]] = []

        if self.reference:
            candidates.append((self.reference, self.reference_desc))

        if self.text.startswith(text):
            candidates.append((self.text, self.desc))

        return candidates

    def match(self, text: str) -> bool:
        """returns True if `text` extactly matches this Node."""
        return self.text == text


class InterfaceNode(BasicNode):
    """Node representing interfaces"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            reference="<interface-name>",
            reference_desc="Name of interface",
            action=action,
        )

    def __str__(self):
        return "<Interface>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:

        candidates: list[tuple[str, str]] = []
        if self.reference:
            candidates.append((self.reference, self.reference_desc))

        for adapter in ifaddr.get_adapters():
            if adapter.name.startswith(text):
                candidates.append((adapter.name, ""))
        return candidates

    def match(self, text: str) -> bool:
        for adapter in ifaddr.get_adapters():
            if adapter.name == text:
                return True
        return False


class StringNode(BasicNode):
    """Node representing string"""

    def __init__(
        self,
        reference: str,
        reference_desc: str,
        action: Callable[[list[str]]] | None = None,
    ):
        super().__init__(
            "", "", reference=reference, reference_desc=reference_desc, action=action
        )

    def __str__(self):
        return "<String>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, text: str) -> bool:
        if re.match(r"[0-9a-zA-Z_\-]+", text):
            return True
        return False


class IPv4AddressNode(BasicNode):
    """Node representing IPv4Address"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            reference="<ipv4-address>",
            reference_desc="IPv4 Address",
            action=action,
        )

    def __str__(self):
        return "<IPv4Address>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, text: str) -> bool:
        try:
            ipaddress.IPv4Address(text)
            return True
        except ipaddress.AddressValueError:
            return False


class IPv6AddressNode(BasicNode):
    """Node representing IPv6Address"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            reference="<ipv6-address>",
            reference_desc="IPv6 Address",
            action=action,
        )

    def __str__(self):
        return "<IPv6Address>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, text: str) -> bool:
        try:
            ipaddress.IPv6Address(text)
            return True
        except ipaddress.AddressValueError:
            return False


class InterfaceAddressNode(BasicNode):
    """Node representing IPv6Address"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            reference="<address>",
            reference_desc="Interface address/prefix length",
            action=action,
        )

    def __str__(self):
        return "<InterfaceAddress>"

    def completion_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.reference, self.reference_desc)]

    def match(self, text: str) -> bool:

        if not "/" in text:
            return False

        try:
            ipaddress.ip_interface(text)
            return True
        except ValueError:
            return False
