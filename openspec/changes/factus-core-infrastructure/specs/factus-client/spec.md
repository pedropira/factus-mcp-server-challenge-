# Factus Client Specification

## Purpose

Define the requirements for the Factus API asynchronous HTTP client and its transparent authentication mechanism.

## Requirements

### Requirement: CLIENT_OAUTH_AUTHENTICATION

The client MUST implement transparent, on-demand OAuth2 authentication via a custom `httpx.AsyncAuth` implementation.

#### Scenario: First Request - No Token in Memory

- GIVEN the Factus client is initialized
- AND no access token exists in memory
- WHEN a business request is sent to the client
- THEN the authenticator MUST execute a POST request to `/oauth/token` using the configured credentials
- AND store the resulting `access_token`, `refresh_token`, and calculated expiration time in memory
- AND append the `Authorization: Bearer <token>` header to the original request
- AND proceed to execute the business request

#### Scenario: Subsequent Request - Valid Token in Memory

- GIVEN the Factus client has a valid, non-expired access token in memory
- WHEN a business request is sent to the client
- THEN the authenticator MUST NOT request a new token
- AND append the existing `Authorization: Bearer <token>` header to the request
- AND execute the business request

#### Scenario: Expired Token Refresh

- GIVEN the Factus client has an expired access token in memory
- WHEN a business request is sent to the client
- THEN the authenticator MUST execute a POST request to `/oauth/token` to refresh/fetch a new token
- AND update the token and expiration in memory
- AND append the new `Authorization: Bearer <token>` header to the request
- AND execute the business request

#### Scenario: Authentication Request Fails

- GIVEN invalid credentials configured
- WHEN a business request is sent to the client
- THEN the OAuth request MUST fail
- AND the client MUST raise an authentication exception
- AND the original business request MUST NOT be sent
