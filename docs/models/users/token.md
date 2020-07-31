# Tokens

A token is a unique identifier that identifies a user to the API. Each user in
Peering Manager can have one or more tokens to authenticate to the API. To
create a token, navigate to the API tokens page at `/user/api-tokens/`.

Each token contains a 160-bit key represented as 40 hexadecimal characters.
When creating a token, leaving the key field blank will automatically generate
a random key.

By default, a token can be used for all operations available via the API. It
can be restricted only to read operations by deselecting the "write enable"
options.

A token can also be programmed to expire at a specific time. This can be
useful if an external client needs to be granted temporary access.
