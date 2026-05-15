"""Validate PiFinder's existing SkySafari/LX200 position server.

The real `PiFinder.pos_server` binds to TCP port 4030, as expected by the
SkySafari workflow. This helper starts that server with fake shared state and
checks a few protocol commands over a socket.
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import queue
import socket
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


class FakeUIState:
    def __init__(self) -> None:
        self.recent = []
        self.new_pushto = False

    def add_recent(self, obj) -> None:
        self.recent.append(obj)

    def set_new_pushto(self, value: bool) -> None:
        self.new_pushto = value


class FakeSharedState:
    def __init__(self) -> None:
        self._ui_state = FakeUIState()

    def solution(self):
        return {"RA": 83.6331, "Dec": 22.0145}

    def datetime(self):
        return datetime(2026, 5, 2, 21, 30, tzinfo=timezone.utc)

    def ui_state(self):
        return self._ui_state


def _server_process(ui_queue: mp.Queue) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    python_dir = repo_root / "python"
    os.chdir(python_dir)
    sys.path.insert(0, str(python_dir))

    from PiFinder import pos_server

    pos_server.MultiprocLogging.configurer = lambda _log_queue: None
    pos_server.run_server(
        shared_state=FakeSharedState(),
        p_ui_queue=ui_queue,
        log_queue=mp.Queue(),
    )


def _connect(port: int) -> socket.socket:
    deadline = time.time() + 10
    last_error: OSError | None = None
    while time.time() < deadline:
        try:
            return socket.create_connection(("127.0.0.1", port), timeout=2)
        except OSError as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Could not connect to LX200 server: {last_error}")


def _send_command(sock: socket.socket, command: str) -> str:
    sock.sendall(command.encode())
    sock.settimeout(3)
    return sock.recv(1024).decode()


def run_validation(port: int = 4030) -> list[CheckResult]:
    ui_queue: mp.Queue = mp.Queue()
    process = mp.Process(target=_server_process, args=(ui_queue,))
    process.start()
    results: list[CheckResult] = []

    try:
        with _connect(port) as sock:
            product = _send_command(sock, ":GVP#")
            results.append(
                CheckResult(
                    "product",
                    product == "PiFinder#",
                    f":GVP# -> {product!r}",
                )
            )

            ra = _send_command(sock, ":GR#")
            results.append(
                CheckResult(
                    "ra",
                    ra.endswith("#") and len(ra) >= 8,
                    f":GR# -> {ra!r}",
                )
            )

            dec = _send_command(sock, ":GD#")
            results.append(
                CheckResult(
                    "dec",
                    dec.endswith("#") and ("*" in dec),
                    f":GD# -> {dec!r}",
                )
            )

            sr = _send_command(sock, ":Sr05:35:17#")
            sd = _send_command(sock, ":Sd+22*00:52#")
            try:
                queued = ui_queue.get(timeout=3)
            except queue.Empty:
                queued = None
            results.append(
                CheckResult(
                    "pushto",
                    sr == "1" and sd == "1" and queued == "push_object",
                    f":Sr# -> {sr!r}, :Sd# -> {sd!r}, ui_queue -> {queued!r}",
                )
            )
    except Exception as exc:
        results.append(CheckResult("server", False, str(exc)))
    finally:
        process.terminate()
        process.join(timeout=5)

    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4030)
    args = parser.parse_args()

    results = run_validation(args.port)
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status} {result.name}: {result.detail}")
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
