# The de-press site / landing — documentation

> Repository: **separate** (the landing is not part of the app repository).
> This section documents the landing; the working code lives in its own repository with its own stack and visual engine.

## The landing's role

- The outer, presentational surface: the project's idea, the rules of use, "about the project," FAQ answers, storytelling.
- **NOT** the app's interface. No TG ergonomics — this is not the app.
- It keeps the app free of "showcase" pages: all public information is served through the landing, not through the interface.

## The only connection to the app

**A transition link** to the browser app, for example:

```
https://depress.co → https://app.depress.co
```

Nothing else in common. Their own stacks, their own deploys, their own visual engines.

## What is served through the app, not through the landing

> Decision (2026-08): **all** public/literary pages move to the landing: the idea, help, guides, "about the project," etc.
> Information about the project will be served **through the app itself** — through its features and interface. That is separate work (see `../app/DESIGN_V2.md`).

## Landing documents (placeholders)

The landing briefs will appear here: content, pages, the entry point, style. For now — a skeleton:

- [ ] Landing brief (goals, audience, page structure)
- [ ] Contents: the idea, the rules, "about the project," FAQ
- [ ] The transition link into the app (URL, CTA, transition rules)
