from __future__ import annotations

import argparse
import json
import socket

import uvicorn


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) != 0


def find_available_port(host: str, preferred_port: int, limit: int = 20) -> int | None:
    for port in range(preferred_port, preferred_port + limit + 1):
        if port_is_available(host, port):
            return port
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the InfraGuard AI backend.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable uvicorn reload for development. Stable demo mode leaves this off.",
    )
    parser.add_argument(
        "--strict-port",
        action="store_true",
        help="Fail with a clean JSON message instead of moving to the next available port.",
    )
    return parser.parse_args()


def print_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2))


def main() -> None:
    args = parse_args()
    port = args.port

    if not port_is_available(args.host, port):
        if args.strict_port:
            print_json(
                {
                    "error": f"Port {port} already in use",
                    "suggestion": f"Kill existing process or use --port {port + 1}",
                }
            )
            raise SystemExit(1)

        next_port = find_available_port(args.host, port + 1)
        if next_port is None:
            print_json(
                {
                    "error": f"No available port found near {port}",
                    "suggestion": "Stop an existing backend process or pass --port manually.",
                }
            )
            raise SystemExit(1)

        print_json(
            {
                "warning": f"Port {port} already in use",
                "selected_port": next_port,
                "url": f"http://{args.host}:{next_port}",
            }
        )
        port = next_port

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=port,
        reload=args.reload,
        workers=1,
    )


if __name__ == "__main__":
    main()
