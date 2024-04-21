import pytest

from nosh.token import (
    IPAddressToken,
    TextToken,
    InterfaceToken,
    StringToken,
    IntToken,
    IPv4AddressToken,
    IPv6AddressToken,
    InterfaceAddressToken,
    IPv4NetworkToken,
    IPv6NetworkToken,
    ChoiceToken,
)


param_make_valid_token = [
    (TextToken, {"text": "text", "desc": "desc"}),
    (InterfaceToken, {}),
    (StringToken, {"mark": "<string>"}),
    (StringToken, {"mark": "<string>", "regex": r".[a-zA-Z]"}),
    (IntToken, {}),
    (IntToken, {"range": (1, 10)}),
    (IPv4AddressToken, {}),
    (IPv6AddressToken, {}),
    (IPAddressToken, {}),
    (InterfaceAddressToken, {}),
    (IPv4NetworkToken, {}),
    (IPv6NetworkToken, {}),
    (ChoiceToken, {"choices": ["choice1", "choice2"]}),
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
    (IntToken, {"range": "not-tuple"}),  # range must be tuple[int, int]
    (IntToken, {"range": ()}),  # range must be tuple[int, int]
    (IPv4AddressToken, {"text": "text"}),  # must not have text
    (IPv6AddressToken, {"text": "text"}),  # must not have text
    (IPAddressToken, {"text": "text"}),  # must not have text
    (InterfaceAddressToken, {"text": "text"}),  # must not have text
    (IPv4NetworkToken, {"text": "text"}),  # must not have text
    (IPv6NetworkToken, {"text": "text"}),  # must not have text
    (ChoiceToken, {"text": "text"}),  # must not have text
    (ChoiceToken, {}),  # must have choices
]


@pytest.mark.parametrize("cls, kwargs", param_make_invalid_token)
def test_make_invalid_token(cls, kwargs):
    with pytest.raises(ValueError):
        cls(**kwargs)


param_match_test = [
    (
        TextToken,  # class
        {"text": "text"},  # arguments for class
        ["text"],  # match ok
        [],  # match ng
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
    (
        IPv4AddressToken,
        {},
        ["10.0.0.1"],
        ["10.0.0.1/24", "2001:db8::1", "asdf"],
    ),
    (
        IPv6AddressToken,
        {},
        ["2001:db8::1"],
        ["10.0.0.1", "2001:db8::1/64", "asdf"],
    ),
    (
        IPAddressToken,
        {},
        ["10.0.0.1", "2001:db8::1"],
        ["10.0.0.1/32", "2001:db8::1/64", "asdf"],
    ),
    (
        InterfaceAddressToken,
        {},
        ["10.0.0.1/24", "10.0.0.0/24", "fe80::1/64", "2001:db8::1/128"],
        ["10.0.0.0", "2001:db8::1", "asdf"],
    ),
    (
        IPv4NetworkToken,
        {},
        ["10.0.0.0/24"],
        ["10.0.0.0", "10.0.0.1/24", "2001:db8::1", "2001:db8::1/64", "asdf"],
    ),
    (
        IPv6NetworkToken,
        {},
        ["2001:db8::/64"],
        ["10.0.0.0", "10.0.0.1/24", "2001:db8::1", "2001:db8::1/64", "asdf"],
    ),
    (
        ChoiceToken,
        {"choices": ["choice1", "choice2"]},
        ["choice1", "choice2"],
        ["choice", "not match"],
    ),
]


@pytest.mark.parametrize("cls, kwargs, ok, ng", param_match_test)
def test_token_match(cls, kwargs, ok, ng):
    token = cls(**kwargs)

    for m in ok:
        print(f"ok: {m}")
        assert token.match(m)

    for m in ng:
        print(f"ng: {m}")
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


def test_interface_token_regex():
    t = InterfaceToken(regex="e.*")  # ethernet ports on both macos and linux
    assert not t.match("lo0")
    assert t.completion_candidates("e")


def test_string_token_regex():
    t = StringToken(mark="<mark>")
    assert t.match("asdf")
    assert t.match("asdf/.-")
    assert not t.match("comma,")

    t = StringToken(mark="<mark>", regex=r"^[a-z,]$")
    assert not t.match("comma,")
    assert not t.match("X")


def test_int_token_range():
    t = IntToken(range=(1, 10))
    assert t.match("1")
    assert t.match("10")
    assert not t.match("0")
    assert not t.match("11")


def test_choice_token_completion():
    t = ChoiceToken(
        choices=["asdf", "qwer"],
    )
    assert t.completion_candidates("") == [(t.mark, t.desc), ("asdf", ""), ("qwer", "")]
    assert t.completion_candidates("a") == [("asdf", "")]
    assert t.completion_candidates("q") == [("qwer", "")]
