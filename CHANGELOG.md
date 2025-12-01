# Changelog

## 2025-11-29
- Added Cigna-branded landing page with hero animation and CTA.
- Implemented registration and login flows with JWT via Secrets Manager.
- Added patient portal pages: profile, claims history, submit claim with S3 presigned upload.
- Secured claims routes with token-based identity and removed client-provided IDs.
- Implemented admin endpoints and dashboard for users and pending claim review.
- Refactored Lambda for modularity and future Bedrock integration.
- Added unit/integration tests and documentation.
