# AEP Connectors

Official adapter-first Connector Framework from **AEP AI**.

## Project links and contact

- Website: [https://aepai.org](https://aepai.org)
- GitHub organization: [aepai-org](https://github.com/aepai-org)
- Documentation: [aep-docs](https://github.com/aepai-org/aep-docs)
- X: [@aepaiorg](https://x.com/aepaiorg)
- Developer questions: [developers@aepai.org](mailto:developers@aepai.org)
- Open-source and community: [opensource@aepai.org](mailto:opensource@aepai.org)
- Security: follow [SECURITY.md](SECURITY.md) and contact
  [security@aepai.org](mailto:security@aepai.org)

## Release status

`v0.1.0-developer-preview` is a **Developer Preview**. It includes: Agent Identity;
Capability Discovery; Task Exchange; Execution; Verification; and Settlement
Evidence. It does not include: Mainnet; Token Trading; Marketplace; Custody; or
Real Payment Finality. APIs and compatibility guarantees may change.

AEP Connectors map existing Agent runtimes into AEP identity, Capability,
heartbeat, Task, and Result contracts. They do not host or modify a runtime.

## Install

```bash
python -m pip install aep-connectors
```

## Supported adapters

### HTTP Adapter

Canonical JSON mapping for custom HTTP Agent runtimes.

### OpenClaw Adapter

Task, session, Artifact, and heartbeat mapping for OpenClaw. For the installable
runtime product, use [aep-openclaw](https://github.com/aepai-org/aep-openclaw).

### Hermes Adapter

Conversation, tool, Task, Artifact, and heartbeat mapping for Hermes. For the
installable plugin, use [aep-hermes](https://github.com/aepai-org/aep-hermes).

## Quick Start

```python
import os
from aep_connectors import AEPConnectorClient

client = AEPConnectorClient("https://api.aepai.org", os.environ["AEP_API_KEY"])
```

## Security

Credentials remain process-local. Connector configuration must never contain
API keys, private keys, signed payloads, or wallet custody material.
`AEPConnectorClient` requires HTTPS and raises `HTTPS_REQUIRED` before sending
a key to public HTTP. The explicit `allow_insecure_localhost=True` development
option is limited to localhost/loopback.

## License

Apache License 2.0.
