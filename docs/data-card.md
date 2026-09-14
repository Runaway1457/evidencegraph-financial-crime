# Data card — Project Meridian synthetic fixture

## Summary

Project Meridian is a fictional cross-border transaction network created solely for
engineering demonstrations, tests, UI development, and evaluation. No person, company,
bank account, wallet, document, or transaction represents a real subject.

## Modalities

The fixture models legal entities, people, accounts, crypto wallets, jurisdictions,
relationships, transaction records, registry extracts, invoices, SWIFT-like records,
and page/bounding-box source locators.

## Provenance contract

Each evidence object carries a content SHA-256, storage key, media type, size, source,
ingestion actor, timestamp, and optional document locator. Relationship and finding
citations are normalized through join tables with same-case composite foreign keys.

## Intended use

- deterministic regression tests;
- graph traversal and entity-resolution UI development;
- policy and four-eyes workflow tests;
- grounding and provenance evals;
- safe public demonstrations.

## Prohibited use

The fixture must not train or evaluate a real AML model, estimate real-world performance,
make claims about named people or organizations, or support regulatory filings.

## Limitations

It intentionally over-represents a compact suspicious path so the demo remains legible.
It does not reproduce class imbalance, reporting bias, data quality drift, regional
regulation, or the distribution of a production financial institution.
