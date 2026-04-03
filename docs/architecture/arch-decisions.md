# Architecture: Core Decisions & "Easier To Change" (ETC) Principles

## 1. Modular Monolith ("Arsenal Strategy")
- **Rule:** No Docker, no Kubernetes, no microservices.
- **ETC Justification:** Eliminates cross-boundary deployment complexity. Run locally, bare metal.
- **Constraint:** Logic exists in `lib/`. A module in `lib/` MUST be copy-pasteable into another project without rewrites.

## 2. No-Bloat Frontend
- **Rule:** Jinja2 + HTMX exclusively. Zero React, Vue, Angular, or Node.js.
- **ETC Justification:** Server-side state generation prevents client-side state sync bugs and reduces build steps to zero.
- **Constraint:** No `package.json` allowed.

## 3. Thin Routes
- **Rule:** FastAPI route handlers must contain NO BUSINESS LOGIC.
- **ETC Justification:** Enables swapping out FastAPI for another framework (e.g., Flask, or CLI execution) by keeping routing separate from execution.
- **Constraint:** Routes map request payload -> call `lib/` function -> format Jinja2 response.

## 4. Visual Compliance (Candlelight)
- **Rule:** UI must strictly follow `Candlelight Mode` hex codes. 
  - Bg: `#121212`, Text: `#EBD2BE`.
- **Constraint:** Vanilla CSS or CDN Tailwind only. No post-processing or CSS compilation pipelines.

## 5. Bare-Bones Authentication
- **Rule:** No complex Auth (OAuth/JWT), no User Accounts.
- **Constraint:** Basic script-level access only. Do not add Postgres or user management tables.
