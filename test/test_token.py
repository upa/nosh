import pytest

from nosh.token import (
    TextToken,
    InterfaceToken,
    StringToken,
    IntToken,
    IPv4AddressToken,
    IPv6AddressToken,
    InterfaceAddressToken,
)


param_make_valid_token = [
    (TextToken, {"text": "text", "desc": "desc"}),
    (InterfaceToken, {}),
    (StringToken, {"mark": "<string>"}),
    (IntToken, {}),
    (IPv4AddressToken, {}),
    (IPv6AddressToken, {}),
    (InterfaceAddressToken, {}),
]


@pytest.mark.parametrize("cls, kwargs", param_make_valid_token)
def test_make_valid_token(cls, kwargs):
    cls(**kwargs)


param_make_invalid_token = [
    (TextToken, {}),  # must have text
    (TextToken, {"text": "text", "mark": "<mark>"}),  # must not have mark
    (InterfaceToken, {"text": "invalid"}),  # must not have text
    (StringToken, {"text": "text", "mark": "<string>"}),  # must not have text
    (StringToken, {}),  # must have mark
    (IntToken, {"text": "text"}),  # must not have text
    (IPv4AddressToken, {"text": "text"}),  # must not have text
    (IPv6AddressToken, {"text": "text"}),  # must not have text
    (InterfaceAddressToken, {"text": "text"}),  # must not have text
]


@pytest.mark.parametrize("cls, kwargs", param_make_invalid_token)
def test_make_invalid_token(cls, kwargs):
    with pytest.raises(ValueError):
        cls(**kwargs)


param_match_test = [
    (
        TextToken,
        {"text": "text"},
        ["text"],
        [],
    ),
    (
        StringToken,
        {"mark": "<mark>"},
        ["a", "asdf-asdf", "asdf_", "12345"],
        [" ", "*", "[]", "()"],
    ),
    (
        IntToken,
        {},
        ["10", "0", "-1"],
        ["asdf", "a10"],
    ),
]


@pytest.mark.parametrize("cls, kwargs, ok, ng", param_match_test)
def test_token_match(cls, kwargs, ok, ng):
    token = cls(**kwargs)

    for m in ok:
        assert token.match(m)

    for m in ng:
        assert not token.match(m)


def test_token_find():
    t0 = TextToken(text="root")
    t1 = TextToken(text="t1")
    t2 = TextToken(text="t2")
    s1 = StringToken(mark="<str>")
    t3 = TextToken(text="t3")
    i1 = InterfaceToken()

    t0.append(t1)
    t1.append(t2)
    t2.append(s1)
    s1.append(t3)
    t3.append(i1)

    assert t0.find(["t1"]) == t1
    assert t0.find(["t1", "t2"]) == t2
    assert t0.find(["t1", "t2", StringToken]) == s1
    assert t0.find(["t1", "t2", StringToken, "t3"]) == t3
