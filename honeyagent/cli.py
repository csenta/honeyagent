"""
Command-Line Interface for HoneyAgent.
Autonomous Honeytoken & Decoy Injection Orchestrator for LLM Agents & RAG Pipelines.
"""

import argparse
import json
import os
import sys
from typing import Any
import urllib.request
import yaml

from honeyagent.core.generator import HoneytokenGenerator
from honeyagent.core.models import TokenType
from honeyagent.core.registry import HoneytokenRegistry
from honeyagent.engine.alerts import AlertDispatcher
from honeyagent.engine.seeder import RAGSeeder
from honeyagent.server.listener import create_tripwire_app


def load_config(config_path: str) -> dict[str, Any]:
    default_cfg = {
        "server": {
            "host": "0.0.0.0",
            "port": 8888,
            "public_url": "http://localhost:8888",
        },
        "security": {
            "hmac_secret": "honeyagent_default_master_secret",
            "token_prefix": "ht_",
        },
        "storage": {
            "registry_path": "honeyagent_registry.json",
            "incident_log_path": "honeyagent_incidents.jsonl",
        },
        "alerts": {
            "webhook_url": "",
            "log_level": "INFO",
        },
    }
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_cfg = yaml.safe_load(f) or {}
                # Recursive shallow merge
                for sec, vals in user_cfg.items():
                    if sec in default_cfg and isinstance(vals, dict):
                        default_cfg[sec].update(vals)
                    else:
                        default_cfg[sec] = vals
        except Exception as e:
            print(f"[WARN] Failed to load config from {config_path}: {e}. Using defaults.")
    return default_cfg


def handle_generate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    secret = os.environ.get("HONEYAGENT_SECRET", cfg["security"]["hmac_secret"])
    public_url = cfg["server"]["public_url"]
    registry_path = cfg["storage"]["registry_path"]

    generator = HoneytokenGenerator(hmac_secret=secret, public_url=public_url)
    registry = HoneytokenRegistry(registry_path=registry_path)

    try:
        t_type = TokenType(args.type)
    except ValueError:
        print(f"[ERROR] Invalid token type: {args.type}. Choices: {[t.value for t in TokenType]}")
        return 1

    token = generator.generate(
        token_type=t_type,
        provenance_tag=args.provenance,
        description=args.desc,
    )
    registry.register(token)

    if args.json:
        out = {
            "token_id": token.token_id,
            "token_type": token.token_type.value,
            "value": token.value,
            "provenance_tag": token.provenance_tag,
            "callback_url": token.callback_url,
            "created_at": token.created_at,
            "metadata": token.metadata,
        }
        print(json.dumps(out, indent=2))
    else:
        print("\n🍯 [HoneyAgent] Generated Honeytoken")
        print("=" * 60)
        print(f"  Token ID:       {token.token_id}")
        print(f"  Token Type:     {token.token_type.value}")
        print(f"  Provenance:     {token.provenance_tag}")
        print(f"  Value:          {token.value}")
        print(f"  Callback URL:   {token.callback_url}")
        if token.metadata:
            print(f"  Metadata:       {token.metadata}")
        print("=" * 60)
        print(f"Successfully registered in {registry_path}\n")

    return 0


def handle_seed(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    secret = os.environ.get("HONEYAGENT_SECRET", cfg["security"]["hmac_secret"])
    public_url = cfg["server"]["public_url"]
    registry_path = cfg["storage"]["registry_path"]

    generator = HoneytokenGenerator(hmac_secret=secret, public_url=public_url)
    registry = HoneytokenRegistry(registry_path=registry_path)

    try:
        t_type = TokenType(args.type)
    except ValueError:
        print(f"[ERROR] Invalid token type: {args.type}")
        return 1

    token = generator.generate(
        token_type=t_type,
        provenance_tag=args.provenance,
        description=f"Auto-seeded into {args.target}",
    )
    registry.register(token)

    target_path = args.target
    fmt = args.format.lower()
    if fmt == "auto":
        fmt = "json" if target_path.endswith(".json") else "markdown"

    if fmt == "json":
        RAGSeeder.seed_json_file(target_path, token)
    else:
        RAGSeeder.seed_markdown_file(target_path, token)

    print(f"✅ [HoneyAgent] Successfully seeded {token.token_type.value} token [{token.token_id}] into {target_path} (Format: {fmt})")
    return 0


def handle_list(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    registry_path = cfg["storage"]["registry_path"]
    registry = HoneytokenRegistry(registry_path=registry_path)
    tokens = registry.list_all()

    if args.json:
        out = [
            {
                "token_id": t.token_id,
                "token_type": t.token_type.value,
                "provenance_tag": t.provenance_tag,
                "value": t.value,
                "created_at": t.created_at,
            }
            for t in tokens
        ]
        print(json.dumps(out, indent=2))
        return 0

    print(f"\n🍯 [HoneyAgent] Registered Active Honeytokens ({len(tokens)})")
    print("=" * 80)
    if not tokens:
        print("  No tokens currently registered.")
    else:
        for t in tokens:
            val_display = t.value if len(t.value) <= 45 else t.value[:42] + "..."
            print(f"• ID: {t.token_id:<28} | Type: {t.token_type.value:<16} | Prov: {t.provenance_tag}")
            print(f"  Value: {val_display}")
            print(f"  Callback: {t.callback_url}")
            print("-" * 80)
    print()
    return 0


def handle_listen(args: argparse.Namespace) -> int:
    import uvicorn

    cfg = load_config(args.config)
    host = args.host or cfg["server"]["host"]
    port = args.port or cfg["server"]["port"]
    secret = os.environ.get("HONEYAGENT_SECRET", cfg["security"]["hmac_secret"])
    public_url = cfg["server"]["public_url"]
    registry_path = cfg["storage"]["registry_path"]
    incident_log_path = cfg["storage"]["incident_log_path"]
    webhook_url = cfg["alerts"].get("webhook_url", "")

    generator = HoneytokenGenerator(hmac_secret=secret, public_url=public_url)
    registry = HoneytokenRegistry(registry_path=registry_path)
    dispatcher = AlertDispatcher(incident_log_path=incident_log_path, webhook_url=webhook_url)

    app = create_tripwire_app(registry=registry, generator=generator, dispatcher=dispatcher)

    print(f"🍯 [HoneyAgent] Starting Tripwire Callback Listener on {host}:{port}")
    print(f"   Registry:       {registry_path} ({len(registry.tokens)} active tokens)")
    print(f"   Incident Log:   {incident_log_path}")
    print(f"   Public Base URL:{public_url}")
    print("   Ready for inbound deception probes.\n")

    uvicorn.run(app, host=host, port=port)
    return 0


def handle_test_probe(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    base_url = (args.url or cfg["server"]["public_url"]).rstrip("/")
    registry = HoneytokenRegistry(registry_path=cfg["storage"]["registry_path"])

    target_token = None
    if args.token_id:
        target_token = registry.get(args.token_id)
        if not target_token:
            print(f"[ERROR] Token ID '{args.token_id}' not found in registry.")
            return 1
    elif registry.tokens:
        target_token = list(registry.tokens.values())[0]
    else:
        # Create an ad-hoc token for testing
        generator = HoneytokenGenerator(hmac_secret="test_secret", public_url=base_url)
        target_token = generator.generate(TokenType.API_BEARER_TOKEN, "test:simulation")
        registry.register(target_token)

    print(f"🚀 [HoneyAgent] Simulating attacker probe against: {base_url}")
    print(f"   Target Token: {target_token.token_id} ({target_token.token_type.value})")

    try:
        if target_token.token_type == TokenType.CANARY_DOCUMENT:
            probe_url = f"{base_url}/beacon/{target_token.token_id}"
            req = urllib.request.Request(probe_url, headers={"User-Agent": "AttackerBrowser/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"   [Probe Response] Status: {resp.status}, Content-Type: {resp.headers.get('content-type')}")
        elif target_token.token_type == TokenType.API_BEARER_TOKEN:
            probe_url = f"{base_url}/api/v1/user"
            req = urllib.request.Request(
                probe_url,
                headers={"Authorization": f"Bearer {target_token.value}", "User-Agent": "AttackerCLI/2.0"},
            )
            try:
                urllib.request.urlopen(req, timeout=5)
            except urllib.error.HTTPError as e:
                print(f"   [Probe Response] Expected 401 Intercepted: {e.code}")
        elif target_token.token_type == TokenType.AWS_ACCESS_KEY:
            probe_url = f"{base_url}/aws-sts"
            req = urllib.request.Request(
                probe_url,
                data=f"Action=GetCallerIdentity&AWSAccessKeyId={target_token.value}".encode(),
                headers={"User-Agent": "aws-cli/2.11"},
            )
            try:
                urllib.request.urlopen(req, timeout=5)
            except urllib.error.HTTPError as e:
                print(f"   [Probe Response] Expected 403 Intercepted: {e.code}")
        else:
            probe_url = f"{base_url}/beacon/{target_token.token_id}"
            req = urllib.request.Request(probe_url, headers={"User-Agent": "SimulatedCrawler/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"   [Probe Response] Status: {resp.status}")

        print("✅ Simulated intrusion probe executed successfully. Check incident log and listener console!")
        return 0
    except Exception as e:
        print(f"❌ Probe failed: {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="honeyagent",
        description="HoneyAgent: Autonomous Honeytoken & Decoy Injection Orchestrator for LLM Agents & RAG Pipelines",
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Generate
    p_gen = subparsers.add_parser("generate", help="Generate and register an HMAC-signed honeytoken")
    p_gen.add_argument(
        "--type",
        choices=[t.value for t in TokenType],
        default=TokenType.AWS_ACCESS_KEY.value,
        help="Honeytoken type",
    )
    p_gen.add_argument("--provenance", default="rag:enterprise_kb", help="Provenance tracking tag")
    p_gen.add_argument("--desc", default="", help="Description")
    p_gen.add_argument("--config", default="config/default_config.yaml", help="Path to config file")
    p_gen.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Seed
    p_seed = subparsers.add_parser("seed", help="Generate honeytoken and inject into target document")
    p_seed.add_argument("--target", required=True, help="Target document path to inject decoy into")
    p_seed.add_argument(
        "--type",
        choices=[t.value for t in TokenType],
        default=TokenType.AWS_ACCESS_KEY.value,
        help="Honeytoken type",
    )
    p_seed.add_argument("--provenance", default="rag:corpus_injection", help="Provenance tracking tag")
    p_seed.add_argument("--format", choices=["auto", "markdown", "json"], default="auto", help="Injection format")
    p_seed.add_argument("--config", default="config/default_config.yaml", help="Path to config file")

    # List
    p_list = subparsers.add_parser("list", help="List all registered active honeytokens")
    p_list.add_argument("--config", default="config/default_config.yaml", help="Path to config file")
    p_list.add_argument("--json", action="store_true", help="Output in JSON format")

    # Listen
    p_listen = subparsers.add_parser("listen", help="Run the FastAPI tripwire callback listener")
    p_listen.add_argument("--host", default=None, help="Host to bind")
    p_listen.add_argument("--port", type=int, default=None, help="Port to bind")
    p_listen.add_argument("--config", default="config/default_config.yaml", help="Path to config file")

    # Test-probe
    p_probe = subparsers.add_parser("test-probe", help="Simulate an intrusion probe against tripwire listener")
    p_probe.add_argument("--token-id", default=None, help="Token ID to test")
    p_probe.add_argument("--url", default=None, help="Tripwire listener URL")
    p_probe.add_argument("--config", default="config/default_config.yaml", help="Path to config file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "generate":
        return handle_generate(args)
    elif args.command == "seed":
        return handle_seed(args)
    elif args.command == "list":
        return handle_list(args)
    elif args.command == "listen":
        return handle_listen(args)
    elif args.command == "test-probe":
        return handle_test_probe(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
