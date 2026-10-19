Carrier tooltips used native weapon getters that bypassed the generic tooltip hook. QA37 connects the two pinned Carrier-only calls to the existing owner weapon cache, preserving the native research contribution. This changes presentation; owner-isolated missile damage remains the combat authority.

Fleet manuals now add +1 per Interceptor, Wraith ground/air +6/+12, and Scout ground +6 and air +6 per missile (+12 per salvo), per rank. Other profiles and four-rank caps are retained.

Materialized Hallucinations explode once on death or expiry. Damage is half their maximum health plus shields, capped at 150, against every enemy within 128 pixels. Enemy ownership, generation reuse, expiry duplication, range boundaries and both Carrier tooltip relays are covered by native host checks. All 63 campaign maps remain byte-identical. Actual QA37 gameplay remains for player verification.
