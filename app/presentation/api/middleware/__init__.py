"""
API middleware package.

What this is:
- The package for stage-2 API cross-cutting concerns.

What it does:
- Hosts auth, governance, and trace middleware implementations.

Why this is done this way:
- Middleware should be grouped under presentation because it shapes request and
  response behavior before control reaches route handlers.
"""
