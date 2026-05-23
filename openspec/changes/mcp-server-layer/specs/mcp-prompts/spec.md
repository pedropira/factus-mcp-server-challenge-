# MCP Prompts Specification

## Purpose

Reusable prompt templates for end users: creation guides that structure document workflows, and analytical prompts that help users make decisions.

## Requirements

### Requirement: Creation Guide Prompts

The system MUST expose creation guide prompts that walk users through document creation.

| Prompt | Purpose |
|--------|---------|
| `crear-factura-guia` | Step-by-step invoice creation: customer → numbering → items → retentions → validate → send |
| `crear-nota-credito-guia` | Credit note creation: invoice reference → correction concept → items → validate |
| `crear-documento-soporte-guia` | Support document creation: provider → items → validate |
| `crear-nota-ajuste-guia` | Adjustment note creation: support doc reference → items → validate |

#### Scenario: Invoice guide structures the workflow

- GIVEN a user loads `crear-factura-guia`
- WHEN the prompt is rendered
- THEN it contains numbered steps: find/create customer, check numbering ranges, select products, review withholdings, validate and send
- THEN each step references the relevant MCP tools/resources

### Requirement: Analytical Prompts

The system MUST expose analytical prompts that help users make informed decisions.

| Prompt | Purpose |
|--------|---------|
| `analizar-obligaciones-tributarias` | Analyze customer tribute profile and determine applicable withholdings |
| `analizar-factura-antes-enviar` | Pre-submit analysis: validate payload, spot potential issues |
| `comparar-tipos-documento` | Help decide between invoice, credit note, support document, or adjustment note |
| `analizar-codigos-dian` | Given a concept, return relevant DIAN codes with explanations |
| `simular-retenciones` | Given items and customer, simulate withholding calculation breakdown |

#### Scenario: Tax analysis prompt guides user

- GIVEN a user loads `analizar-obligaciones-tributarias` with customer data
- WHEN the prompt is rendered
- THEN it analyzes tribute_code to determine if customer is Gran Contribuyente, Autorretenedor, or standard
- THEN it lists which withholdings apply and at what rates
