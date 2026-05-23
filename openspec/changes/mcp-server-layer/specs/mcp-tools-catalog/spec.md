# MCP Tools — Catalog Domain Specification

## Purpose

MCP tools for local DB CRUD operations on customers, products, establishments, numbering ranges, and company info.

## Requirements

### Requirement: Customer Tools

| Tool | Service Method |
|------|----------------|
| `create_customer` | `CustomerService.create()` |
| `get_customer` | `CustomerService.get_by_id()` |
| `search_customers` | `CustomerService.search()` |
| `update_customer` | `CustomerService.update()` |
| `delete_customer` | `CustomerService.delete()` |

#### Scenario: Create and retrieve customer

- GIVEN valid customer data
- WHEN `create_customer` executes
- THEN a new `Customer` is persisted and returned
- THEN `get_customer` with the returned ID retrieves it

### Requirement: Product Tools

| Tool | Service Method |
|------|----------------|
| `create_product` | `ProductService.create()` |
| `get_product` | `ProductService.get_by_id()` |
| `get_product_by_code` | `ProductService.get_by_code()` |
| `search_products` | `ProductService.search()` |
| `update_product` | `ProductService.update()` |
| `delete_product` | `ProductService.delete()` |

### Requirement: Establishment Tools

| Tool | Service Method |
|------|----------------|
| `create_establishment` | `EstablishmentService.create()` |
| `get_establishment` | `EstablishmentService.get_by_id()` |
| `list_establishments` | `EstablishmentService.list()` |
| `update_establishment` | `EstablishmentService.update()` |
| `delete_establishment` | `EstablishmentService.delete()` |

### Requirement: Numbering Range Tools

| Tool | Service Method |
|------|----------------|
| `create_numbering_range` | `NumberingRangeService.create()` |
| `get_active_numbering_ranges` | `NumberingRangeService.get_active()` |
| `get_default_numbering_range` | `NumberingRangeService.get_default_for_document_type()` |
| `fetch_numbering_ranges_from_factus` | `NumberingRangeService.fetch_from_factus()` |

### Requirement: Company Tool

| Tool | Service Method |
|------|----------------|
| `get_company_info` | `CompanyService.get_info()` |

#### Scenario: Company info returns valid data

- GIVEN the server has Factus credentials
- WHEN `get_company_info` executes
- THEN it returns the company data from Factus API
