---
name: as-of-research
description: Cutoff-safe research workflow for Futurecast predictions. Use when searching, fetching, or citing web evidence for a forecast with an as-of date, target date, resolved event, recent data, or risk of post-cutoff leakage.
---

# Futurecast As-Of Research

Use this skill when gathering evidence for a forecast. The goal is to find priors and pre-cutoff
signals, not the realized answer.

## Query Rules

- Include the entity, metric/event, and cutoff-relevant date terms in the query.
- Prefer primary sources, official data, markets, odds, polling, and established aggregators.
- For local-language domains, search in the source language.
- Avoid queries that ask for the target-date result or the resolved outcome.

## Cutoff Discipline

- Treat the effective as-of date as "today".
- Reject sources published after the cutoff unless only pre-cutoff facts are clearly separable.
- In Claude/Futurecast MCP runs, rely on the tool guard but still reason as if leakage is possible.
- In Codex native-search runs, there is no Futurecast MCP fetch guard; source choice and query wording
  must enforce the cutoff.

## Evidence Synthesis

- Extract dates, values, poll field dates, market timestamps, and source authority.
- Keep the latest pre-cutoff value or prior as the anchor.
- Use additional sources only to adjust that anchor or resolve contradictions.
- Stop after enough evidence exists to answer; repeated searches usually add noise.
