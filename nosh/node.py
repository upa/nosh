from __future__ import annotations
from sre_constants import CATEGORY_UNI_DIGIT
from typing import Callable

import re
import sys
import ipaddress

import ifaddr


def pr_err(msg: str):
    print(msg, file=sys.stderr)


class Node:
    """Basic Node representing cli node"""

    def __init__(
        self,
        text: str,
        desc: str,
        indicator: str = "",
        indicator_desc: str = "",
        action: Callable[[list[str]]] | None = None,
    ):
        self.text = text
        self.desc = desc
        self.indicator = indicator
        self.indicator_desc = indicator_desc
        self.leafs: list[Node] = []
        self.action = action

        if self.indicator and not re.match(r"<.*>", self.indicator):
            raise ValueError("indicator must be <INDICATOR>")

    def __str__(self):
        return self.text

    def append_leaf(self, node: Node):
        """This method just appends the Node to as a leaf of this Node"""
        self.leafs.append(node)

    def compelte(self, linebuffer: str, text: str) -> list[tuple[str, str]]:
        """This method returns list of candidate values of leaf nodes
        and their help strings.

        """

        if self.match(text):
            """called with "prefix... text", not with "prefix... text
            ", which search the next node. So, returns this node as
            the candidate."""
            return [(text, self.desc)]

        candidates: list[tuple[str, str]] = []
        if self.action:
            candidates.append(("<[Enter]>", "Execute this command"))

        for leaf in self.leafs:
            candidates += leaf.complete_candidates(text)
        return candidates

    def complete_candidates(self, text: str) -> list[tuple[str, str]]:
        """This method returns list of candidate values of `THIS Node`
        and associated descriptions. This is the basic Node, so it
        retrurns just [(text, desc)] if matches. If the node is
        InterfaceNode, it may return [("<interface-name>", "Name of
        interface"), (ifname, ""), (ifname, ""), ...] matching `text`.

        """
        candidates: list[tuple[str, str]] = []

        if self.indicator:
            candidates.append((self.indicator, self.indicator_desc))

        if self.text.startswith(text):
            candidates.append((self.text, self.desc))

        return candidates

    def match(self, text: str) -> bool:
        """returns True if `text` extactly matches this Node."""
        return self.text == text

    def find_leaf(self, text) -> Node | None:
        for leaf in self.leafs:
            if leaf.match(text):
                return leaf
        return None


class InterfaceNode(Node):
    """Node representing interfaces"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            indicator="<interface-name>",
            indicator_desc="Name of interface",
            action=action,
        )

    def __str__(self):
        return "<Interface>"

    def complete_candidates(self, text: str) -> list[tuple[str, str]]:

        candidates: list[tuple[str, str]] = []
        if self.indicator:
            candidates.append((self.indicator, self.indicator_desc))

        for adapter in ifaddr.get_adapters():
            if adapter.name.startswith(text):
                candidates.append((adapter.name, ""))
        return candidates

    def match(self, text: str) -> bool:
        for adapter in ifaddr.get_adapters():
            if adapter.name == text:
                return True
        return False


class StringNode(Node):
    """Node representing string"""

    def __init__(
        self,
        indicator: str,
        indicator_desc: str,
        action: Callable[[list[str]]] | None = None,
    ):
        super().__init__(
            "", "", indicator=indicator, indicator_desc=indicator_desc, action=action
        )

    def __str__(self):
        return "<String>"

    def complete_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.indicator, self.indicator_desc)]

    def match(self, text: str) -> bool:
        if re.match(r"[0-9a-zA-Z_\-]+", text):
            return True
        return False


class IPv4AddressNode(Node):
    """Node representing IPv4Address"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            indicator="<ipv4-address>",
            indicator_desc="IPv4 Address",
            action=action,
        )

    def __str__(self):
        return "<IPv4Address>"

    def complete_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.indicator, self.indicator_desc)]

    def match(self, text: str) -> bool:
        try:
            ipaddress.IPv4Address(text)
            return True
        except ipaddress.AddressValueError:
            return False


class IPv6AddressNode(Node):
    """Node representing IPv6Address"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            indicator="<ipv6-address>",
            indicator_desc="IPv6 Address",
            action=action,
        )

    def __str__(self):
        return "<IPv6Address>"

    def complete_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.indicator, self.indicator_desc)]

    def match(self, text: str) -> bool:
        try:
            ipaddress.IPv6Address(text)
            return True
        except ipaddress.AddressValueError:
            return False


class InterfaceAddressNode(Node):
    """Node representing IPv6Address"""

    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__(
            "",
            "",
            indicator="<address>",
            indicator_desc="Interface address/prefix length",
            action=action,
        )

    def __str__(self):
        return "<InterfaceAddress>"

    def complete_candidates(self, text: str) -> list[tuple[str, str]]:
        return [(self.indicator, self.indicator_desc)]

    def match(self, text: str) -> bool:

        if not "/" in text:
            return False

        try:
            ipaddress.ip_interface(text)
            return True
        except ValueError:
            return False
