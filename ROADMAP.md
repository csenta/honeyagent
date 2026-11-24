# HoneyAgent Engineering Roadmap

## Milestones

### Milestone 1: Core Deception Engine & Tripwire (v1.0 - Current)
- [x] Cryptographic HMAC-signed Honeytoken Generator (`AWS_KEY`, `DB_DSN`, `API_TOKEN`, `CANARY_DOC`).
- [x] Local JSON/SQLite Honeytoken Registry with provenance tracking.
- [x] Lightweight FastAPI Tripwire callback server.
- [x] RAG / Vector collection document seeder.
- [x] Webhook, JSONL, and Slack-compatible alert dispatcher.
- [x] CLI for generating tokens, seeding files, running tripwire server.
- [x] Full automated test suite (Generator, Registry, Tripwire, Alerting).
- [x] Dockerfile & GitHub Actions CI pipeline.

### Milestone 2: Cloud & Enterprise Integration (v1.1)
- [ ] Direct Pinecone, Qdrant, Chroma, and Milvus vector collection auto-seeding.
- [ ] AWS CloudTrail / GuardDuty canary token auto-registration.
- [ ] DNS canary token listener (interception via authoritative nameserver callbacks).

### Milestone 3: Adversarial AI Deception Fabric (v2.0)
- [ ] Adaptive honey-persona responding dynamically to conversational exfiltration attacks.
- [ ] Automated attacker attribution and MITRE ATT&CK mapping.
