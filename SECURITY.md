# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Asuq AI, please report it responsibly.

**Do not** open a public GitHub issue for security vulnerabilities.

Instead, please email the maintainers directly with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment

We will acknowledge receipt within 48 hours and provide a timeline for resolution.

## Security Measures

### Input Security
- Prompt injection detection (13+ regex patterns + LLM verification)
- Content moderation pipeline (4 layers: blocklist, toxic classifier, LLM judge, human review)

### Output Security
- Leak detection for API keys, JWT tokens, credentials, and phone numbers (13 regex patterns + LLM verification)

### Authentication
- JWT-based authentication via Supabase Auth
- Dual admin auth: API key header + JWT role check
- All admin operations logged to audit trail

### Infrastructure
- HTTPS enforced via HSTS headers
- Content Security Policy (CSP) headers
- Rate limiting on all endpoints
- Row-Level Security (RLS) on all user-specific database tables

## Scope

This security policy applies to the Asuq AI application code in this repository. It does not cover:
- Third-party dependencies (report upstream)
- Infrastructure/hosting security (contact your provider)
