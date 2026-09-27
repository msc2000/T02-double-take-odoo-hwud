# OdooPulse

**AI-powered business decision assistant for SMEs, built on Odoo.**

OdooPulse analyses business data from Odoo, identifies potential problems, predicts what may happen next, recommends an action, and helps the business execute that action within Odoo.

> **Odoo already knows what happened. OdooPulse helps businesses understand what is likely to happen, what they should do next, and act on that decision.**

## Hackathon

**Odoo × HW Tech Club BuildOdoo 2026**

* **Team:** T02 Double Take
* **Track:** AI for SMEs
* **Platform:** Odoo 19
* **Project:** OdooPulse

## The Problem

SMEs often have business information spread across different areas of their ERP system. While Odoo stores data about sales, inventory, purchasing, and other business operations, business owners may still need to manually interpret that information to decide what action to take.

OdooPulse aims to turn this existing business data into actionable decisions.

## Our Solution

OdooPulse follows a simple workflow:

```text
Odoo Business Data
        ↓
     Analysis
        ↓
     Prediction
        ↓
   Risk Detection
        ↓
 Recommendation
        ↓
 Human Approval
        ↓
   Odoo Action
```

The goal is to move from:

**Descriptive → Predictive → Prescriptive → Actionable**

## Current MVP

### Inventory Stockout Prediction

OdooPulse currently analyses:

* Current product stock
* Confirmed sales
* Units sold
* Average daily sales
* Estimated days until stockout

It then classifies inventory risk as:

* 🔴 High
* 🟡 Medium
* 🟢 Low

Based on the risk level, OdooPulse generates a recommendation for the business user.

### Example

```text
Product: Wireless Mouse

Current Stock:          25
Units Sold:             25
Average Daily Sales:    25
Days Until Stockout:    1
Stockout Risk:          HIGH

Recommendation:
High stockout risk. Estimated stock remaining:
1.0 days. Reorder stock soon.
```

## Technology

* Odoo 19
* Python
* Odoo ORM
* XML views
* Odoo Inventory
* Odoo Sales
* Odoo Purchase

## How It Works

The current MVP uses Odoo's ORM to retrieve business data directly from Odoo.

For each selected product, OdooPulse calculates:

1. Current inventory stock
2. Total confirmed units sold
3. Average daily sales
4. Estimated days until stockout
5. Stockout risk level

The system then generates a recommendation based on the predicted stockout risk.

The current prototype uses deterministic business logic for the prediction and recommendation layer. AI-driven explanations and additional predictive capabilities are planned as the project develops.

## How to Run

1. Install and run Odoo 19.
2. Add the `odoo_business_ai` module to Odoo's addons path.
3. Restart Odoo.
4. Update the Apps list.
5. Install **OdooPulse**.
6. Create a Business AI analysis and select a product with inventory and sales data.

## 📁 Project Structure

```text
T02-double-take-odoo-hwud/
├── .gitignore
├── README.md
└── odoo_business_ai/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   └── business_ai.py
    ├── security/
    │   └── ir.model.access.csv
    └── views/
        ├── business_ai_views.xml
        └── business_ai_menus.xml
```

## Features

- [x] OdooPulse custom Odoo module
- [x] Odoo Inventory and Sales data integration
- [x] Current stock calculation
- [x] Confirmed units sold calculation
- [x] Average daily sales calculation
- [x] Estimated days until stockout
- [x] High / Medium / Low stockout risk classification
- [x] Automated business recommendation
- [x] Odoo list and form views
- [x] Synthetic business data testing
- [x] Recommended reorder quantity
- [x] Create Purchase Order from recommendation
- [x] OdooPulse business risk dashboard
- [x] Multiple products and risk levels
- [ ] AI-generated business explanations
- [ ] Additional SME risk indicators

## Demo Data

The prototype uses synthetic business data inside a local Odoo environment.

No real customer or company data is required for the prototype. In a real deployment, OdooPulse would analyse the company's existing Odoo data.

## Team

**T02 Double Take**

Built for the Odoo × HW Tech Club BuildOdoo 2026 Hackathon.