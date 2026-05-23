# MCP Resources Specification

## Purpose

Read-only resources exposing DIAN codes, tax configuration, and configuration constants to prevent AI agent hallucinations.

## Requirements

### Requirement: DIAN Code Resources

The system MUST expose the following DIAN code mappings as MCP resources.

| URI Template | Content |
|-------------|---------|
| `factus://dian/document-types` | All DIAN document type codes |
| `factus://dian/identification-types` | Factus API identification type IDs |
| `factus://dian/tribute-codes` | Customer tribute codes |
| `factus://dian/unit-measures` | Unit of measure codes |
| `factus://dian/payment-forms` | Payment form codes (contado/crédito) |
| `factus://dian/payment-methods` | Payment method codes (efectivo, transferencia, etc.) |
| `factus://dian/standard-codes` | Product standard codes (UNSPSC, GTIN, etc.) |
| `factus://dian/allowance-charge-concepts` | Allowance/charge reason codes |
| `factus://dian/correction-codes` | Credit note correction concept codes |

#### Scenario: Resource returns correct DIAN codes

- GIVEN a client requests `factus://dian/document-types`
- WHEN the resource handler executes
- THEN it returns the full mapping (e.g. `{"cédula de ciudadanía": "13", "nit": "31", ...}`)

### Requirement: Tax Configuration Resources

| URI Template | Content |
|-------------|---------|
| `factus://config/uvt` | UVT value and thresholds for all withholding types |
| `factus://config/tax-rates` | All tax rates (IVA, ReteRenta, ReteIVA, ReteICA, ReteGMF) |
| `factus://config/reteica-rates` | Municipality-specific ReteICA rates |
| `factus://config/withholding-rules` | Rules per withholding type (who applies, thresholds) |

#### Scenario: UVT resource returns thresholds

- GIVEN a client requests `factus://config/uvt`
- WHEN the resource handler executes
- THEN it returns `{"uvt": 47000, "reterenta_goods_uvt": 27, "reterenta_services_uvt": 4, "rete_gmf_uvt": 100}`
