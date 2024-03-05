
# Nosh is Not a Shell

Nosh is a minimal python library to implement Character Line
Interfaces (CLIs) for networking devices.

## Nosh Basics

Nosh treats each text in CLI input as `token`. Let us consider a
following command line.

```
set interfaces eth0 address 10.0.0.1/24
```

`set`, `interfaces`, `eth0`, `address`, and `10.0.0.1/24`, are tokens.
Each token has one or more leaf tokens and may have `action`.  In this
example, token `set` may have leaf tokens of `show`, `clear`, and
`restart`. Token `10.0.0.1/24` may have an action that assign the
address to the interface `eth0`.

You usually type `tab`, `space`, or `?` to print possible completions
with descriptions. If you do this with command line `set interfaces`,
the CLI shows like:

```
prompt> set interfaces

Completions:
  <interface-name> Name to identify an interface
  eth0
  eth1
  eth2
  eth3
  lo
```

We call this possible completions *descriptions*.


Nosh provides Token classes to implement command lines, for example:

* `TextToken`: It has a static text appeared as a token, like `set`,
  `interface`, and `address`.

* `InterfaceToken`: It represents interface names, for example, `eth0`
  and `eth1`. It appears as `<interface-name>` in descriptions by
  default.
  
* `InterfaceAddressToken`: It represents interface addresses like
  `ADDRESS/PREFLEN`. It appears as `<address>` in descriptions by
  default.
  
So, the first example `set interfaces eth0 address 10.0.0.1/24` is now
represented by a series of tokens: `TextToken("set")`,
`TextToken("interfaces")`, `InterfaceToken`, `TextToken("address")`,
and `InterfaceAddressToken`.

Let's implement it as a CLI:

```
from nosh import CLI, TextToken, InterfaceToken, InterfaceAddressToken

tk_set = TextToken(text="set", desc="Set parameters")
tk_ifs = TextToken(text="interfaces", desc="Set interface parameters")
tk_int = InterfaceToken()
tk_adr = TextToken(text="address", desc="Set IP address")
tk_ifa = InterfaceAddressToken(action=lambda x,y: print(y))

tk_set.append(tk_ifs)
tk_ifs.append(tk_int)
tk_int.append(tk_adr)
tk_adr.append(tk_ifa)

cli = CLI()
cli.append(tk_set)
cli.cli()
```

This script starts your CLI that accepts the command line `set
interfaces eth0 address 10.0.0.1/24` (`eth0` may differ depending on
your environment).

```
> set interfaces eth0 

Completions:
  address          Set IP address

> set interfaces eth0 address 

Completions:
  <address>        Address/Prefixlen

> set interfaces eth0 address 10.0.0.1/24

['set', 'interfaces', 'eth0', 'address', '10.0.0.1/24']
> 

```

## More examples

Please see an example CLI [`cli.py`](/cli.py).


## Token Classes

We have implemented following token classes:

* `TextToken`: representing a static text.
* `InterfaceToekn`: interface names retrieved by `ifaddr`.
* `StringToken`: representing a string for user-defined parameters
  (e.g., route-map, policy-statement, and ACL).
* `IntToken`: representing an integer.
* `IPv4AddressToken`: representing an IPv4 Address.
* `IPv6AddressToken`: representing an IPv6 Address.
* `InterfaceAddressToken`: representing an IP (both v4 and v6) address
  with prefix length.
  

## Implement your Token class

You may want to implement new completions for specific cases depending
on configuration backend. For example, `<route-map>` token would give
a list of already-defined route-maps in a configuration as possible
completions. To do this, implement your own Token class.

InterfaceToken class in [nosh/token.py](/nosh/token.py) may help you.

Your new Token class should inherit `BasicToken` class, and overwrites
`completion_candidates()` and `match()` functions at
least. 

`completion_candidates()` receives `text`, which is a input token, and
returns list of possible completions as `list[tuple("text",
"description")]`. Not that `text` with the format `<.*>` (called
*mark* in the nosh implementation) appear in only descriptions, and
ignored from the completion.

`match()` function returns `True` if the argument `text` **exactly**
matches this token, otherwise False.


  
## Configuration backend

Nosh has **no configuration backend**. It is a library to implement
command line **interfaces**. You can implement your own configuration
mechanisms invoked through `action` of tokens.


