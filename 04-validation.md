# 04 — Validation, risks and roadmap

## Evidence versus acceptance

Confirmed by conversation: SQL connection, LAN access, management approval, successful database restore, PROD migration column checks and initial master-data presence. Latest code was inspected from the supplied V1.3 archive. No live SQL Server, browser session or complete test log was available for this documentation. Product and counterparty seed scripts were provided but final counts are unverified. The pilot has not been documented as completed.

## Acceptance matrix (pending unless noted)

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Single-rate purchase 100 × 20 | Total quantity 100; amount 2,000 |
| T02 | Dual purchase 60 × 30 + 40 × 35 | Quantity 100; amount 3,200 |
| T03 | Sell 50 × 40 against T02 | Cost 1,600; spread 400; remaining 50 |
| T04 | Sell 51 against remaining 50 | Rejected; no committed row |
| T05 | Two simultaneous sales of 30 against remaining 50 | At most one succeeds |
| T06 | Reduce purchase quantity below sold quantity | Rejected |
| T07 | Change product/unit of purchase with sales | Rejected |
| T08 | Sale date before purchase date | Rejected |
| T09 | Edit with stale rowversion | Rejected; no orphan audit |
| T10 | Valid correction with reason | Update and before/after audit committed together |
| T11 | Invalid date 1405/0/9/04 or month 13 | Rejected |
| T12 | Valid Persian digits and YYYY/MM/DD | Accepted; Gregorian invoice date stored |
| T13 | Empty office number | Rejected |
| T14 | Optional settlement date and notes | Round-trip through correction form |
| T15 | Category/subcategory/size selection | Correct product and ID selected |
| T16 | Sidebar collapse/reopen and dropdown contrast | Readable and accessible |
| T17 | Network failure during transaction | No partial commit; retry procedure verified |
| T18 | CSV report | Values reconcile to source; Persian text readable |
| T19 | Backup restore | Independent restored database verified |
| T20 | Double click/repeated submission | No duplicate transaction (currently no guaranteed protection) |
| T21 | Toggle dual pricing off | Single-rate purchase and sale persist successfully |
| T22 | Correct purchase rate after sales | Historical spread behavior matches approved policy |

## Code review findings / operational blockers

- V1.3 constructs Quantity2/Rate2 as None for single-rate entries only after the initial required-field check, so verify both single and dual paths. No runtime execution was performed here.
- Manual actor selection is not authenticated. Audit records identify the selected seller, not a verified user. New inserts do not create AuditV4 rows.
- No idempotency key or unique office invoice constraint. Repeated clicks can duplicate transactions; form state is not explicitly cleared after success.
- Product and unit are independently selectable. Validate their compatibility and establish monetary unit (rial/toman) before real use.
- Historical spread is recalculated from the current purchase price; correcting a purchase can change earlier reported spreads. Decide whether this is desired or snapshot costs.
- Settlement date is embedded in Notes and optional; no typed date or cash/credit consistency constraint. Credit rate is manual.
- Legacy OfficialRate is not updated by the current editor. Review historical data before migration or reuse.
- SQL computed expressions and Python Decimal previews can differ in precision/rounding; reconcile edge cases and define rounding policy.
- Connection uses TrustServerCertificate=yes and a hardcoded internal instance. Configure trusted TLS, least privilege and external configuration before production/publication.
- Host workstation availability is a single point of failure. Scheduled backups, recovery drill, monitoring, service startup and access control are not verified.
- CSS targets Streamlit internal selectors; UI fixes require browser verification. Do not treat hidden menus as security.
- POC and PROD schema drift was observed; migrate POC before future tests. Do not use live data for destructive tests.

## Parallel pilot exit criteria

Recommended duration: at least one complete commission cycle, subject to management agreement. Compare old process and new system daily by invoice, seller, party, product, quantity, purchase amount, sale amount and spread. Log discrepancies with owner, cause, correction and approval. Exit only when all unexplained discrepancies are zero, data loss is zero, access and recovery controls pass, and operators and management sign off. Do not claim productivity gains without measured baseline and post-pilot results.

## Roadmap

1. Stabilize purchase, sale and correction; finish acceptance tests and master-data cleanup.
2. Authentication, role-based permissions, duplicate prevention, backup automation, deployment hardening.
3. Typed settlement dates, payment tracking, service costs, returns and cancellations, multi-product invoices if required.
4. Formal cost allocation and commission rules, financial reconciliation, net profitability and ROI.
5. DWH integration, dimensional modeling, Power BI dashboards and automated data-quality monitoring.

These are proposed future stages, not delivered capabilities.
