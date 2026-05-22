# Core Configuration Specification

## Purpose

Define the requirements and validation behavior for global environment settings.

## Requirements

### Requirement: CONFIG_LOAD_AND_VALIDATE

The system MUST load configurations from the environment or a `.env` file and validate their existence and formats.

#### Scenario: Successful Configuration Load

- GIVEN a valid `.env` file containing:
  - `ENV=sandbox`
  - `FACTUS_CLIENT_ID=test_client_id`
  - `FACTUS_CLIENT_SECRET=test_client_secret`
  - `FACTUS_USERNAME=user@example.com`
  - `FACTUS_PASSWORD=test_password`
  - `MCP_EVALUATION_KEY=test_evaluation_key`
  - `DATABASE_URL=sqlite+aiosqlite:///factus.db`
- WHEN the configuration helper is initialized
- THEN the system MUST successfully parse all values
- AND `ENV` MUST equal "sandbox"

#### Scenario: Missing Required Parameter

- GIVEN a `.env` file where `FACTUS_CLIENT_ID` is missing
- WHEN the configuration helper is initialized
- THEN the system MUST raise a validation error
- AND prevent application startup

#### Scenario: Invalid Email Format

- GIVEN a `.env` file where `FACTUS_USERNAME` is "not-an-email"
- WHEN the configuration helper is initialized
- THEN the system MUST raise a validation error
- AND prevent application startup
