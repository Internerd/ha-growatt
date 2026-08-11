# Security Policy

## Scope and what "security" means here

This integration talks Modbus TCP to an inverter on your local network.
Modbus TCP has **no built-in authentication or encryption** - that's a
property of the protocol itself, not something this integration adds or
removes, and it's the same for the original `Growatt_ModbusTCP`
integration, the manufacturer's own dongle/app, and any other Modbus
client. Anyone who can already reach your inverter's IP:port on your
network could already read/write those registers directly; this
integration doesn't change that exposure. Keep your inverter's network
segment as trusted as you would any other device without its own
authentication (e.g. behind your home network, not port-forwarded to the
internet).

Reports about "Modbus has no auth" or "the writable controls could set a
bad value if misused" describe the protocol, not a bug in this code - see
above rather than opening an issue for that specifically.

## Reporting an actual vulnerability

If you find something that *is* specific to this integration's code (for
example: a way this integration itself exposes something it shouldn't,
processes untrusted input unsafely, or a dependency issue), please open a
[GitHub issue](https://github.com/Internerd/ha-growatt/issues) or, if you'd
rather not make it public immediately, use GitHub's
["Report a vulnerability"](https://github.com/Internerd/ha-growatt/security/advisories/new)
private disclosure feature on this repository instead.

This is a single-maintainer hobby project, not a funded security
program - there's no bug bounty and no guaranteed response time, but
reports will be looked at and a fix or explanation will follow as time
allows.

## Supported versions

Only the latest version on the `main` branch is supported. There are no
long-term-support branches for older releases.
