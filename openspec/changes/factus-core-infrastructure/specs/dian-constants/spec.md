# DIAN Constants Specification

## Purpose

Define the resolution requirements for DIAN (Colombia) reference codes and constants.

## Requirements

### Requirement: CONSTANTS_RESOLUTION

The system MUST expose dictionaries containing DIAN reference codes and resolve human-readable keys to codes.

#### Scenario: Successfully Resolving Document Type

- GIVEN the constants module is imported
- WHEN resolving the code for "Cédula de ciudadanía"
- THEN the system MUST return "13"

#### Scenario: Successfully Resolving Payment Method

- GIVEN the constants module is imported
- WHEN resolving the code for "Efectivo"
- THEN the system MUST return "10"

#### Scenario: Successfully Resolving Municipality Code

- GIVEN the constants module is imported
- WHEN resolving the code for "Bogotá"
- THEN the system MUST return "11001"

#### Scenario: Invalid Constant Lookup

- GIVEN the constants module is imported
- WHEN resolving the code for an unknown municipality "Atlantis"
- THEN the system MUST raise a lookup error or return `None` depending on strict flag
