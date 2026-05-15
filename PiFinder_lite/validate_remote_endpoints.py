"""Validate PiFinder web remote endpoints without starting the full app.

This script starts the real PiFinder `Server` class with fake queues and shared
state, then checks the routes needed by PiFinder Lite:

- `/remote`
- `/image`
- `/key_callback`
- `/mobile/status`
- `/mobile/profile`
- `/mobile/gps`
- `/mobile/imu`
- `/mobile/camera_frame`

It is intentionally kept outside `python/PiFinder/` so it does not change the
classic application runtime.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import io
import json
import multiprocessing as mp
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


class FakeLocation:
    lock = False


class FakeSharedState:
    def screen(self):
        img = Image.new("RGB", (128, 128), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((4, 4, 123, 123), outline=(255, 0, 0))
        draw.text((12, 54), "PiFinder", fill=(255, 0, 0))
        return img

    def location(self):
        return FakeLocation()

    def solve_state(self):
        return False

    def solution(self):
        return None


def _server_process(host: str, port: int, keyboard_queue: mp.Queue) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    python_dir = repo_root / "python"
    os.chdir(python_dir)
    os.environ["PIFINDER_USE_FAKE_SYS_UTILS"] = "1"
    sys.path.insert(0, str(python_dir))

    from PiFinder import server as server_module

    original_run = server_module.run

    def run_on_test_port(app, *args, **kwargs):
        kwargs["host"] = host
        kwargs["port"] = port
        kwargs["quiet"] = True
        return original_run(app, *args, **kwargs)

    server_module.run = run_on_test_port
    server_module.Server(
        keyboard_queue=keyboard_queue,
        ui_queue=mp.Queue(),
        gps_queue=mp.Queue(),
        log_queue=mp.Queue(),
        shared_state=FakeSharedState(),
        is_debug=False,
    )


def _request(
    opener: urllib.request.OpenerDirector,
    url: str,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> urllib.response.addinfourl:
    req = urllib.request.Request(
        url=url,
        data=data,
        method=method,
        headers=headers or {},
    )
    return opener.open(req, timeout=5)


def _read_http_error(exc: urllib.error.HTTPError) -> tuple[int, str]:
    return exc.code, exc.read().decode("utf-8", errors="replace")


def _sample_jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    img = Image.new("RGB", (64, 48), color=(2, 3, 5))
    draw = ImageDraw.Draw(img)
    draw.point((12, 10), fill=(255, 255, 255))
    draw.point((44, 25), fill=(230, 230, 230))
    img.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _multipart_body(
    boundary: str,
    metadata: dict[str, object],
    frame_bytes: bytes,
) -> bytes:
    parts = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="metadata"\r\n',
        b"Content-Type: application/json; charset=utf-8\r\n\r\n",
        json.dumps(metadata).encode(),
        b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="frame"; filename="validator.jpg"\r\n',
        b"Content-Type: image/jpeg\r\n\r\n",
        frame_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(parts)


def _wait_for_server(opener: urllib.request.OpenerDirector, base_url: str) -> bool:
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            _request(opener, f"{base_url}/image").read()
            return True
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    return False


def serve(host: str, port: int) -> None:
    keyboard_queue: mp.Queue = mp.Queue()
    _server_process(host, port, keyboard_queue)


def run_validation(port: int) -> list[CheckResult]:
    keyboard_queue: mp.Queue = mp.Queue()
    server_thread = threading.Thread(
        target=_server_process,
        args=("127.0.0.1", port, keyboard_queue),
        daemon=True,
    )
    server_thread.start()

    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar)
    )
    base_url = f"http://127.0.0.1:{port}"
    results: list[CheckResult] = []

    try:
        if not _wait_for_server(opener, base_url):
            return [
                CheckResult(
                    "/image startup",
                    False,
                    f"Server did not respond on {base_url}",
                )
            ]

        image_response = _request(opener, f"{base_url}/image")
        image_bytes = image_response.read()
        results.append(
            CheckResult(
                "/image",
                image_bytes.startswith(b"\x89PNG\r\n\x1a\n"),
                f"{len(image_bytes)} bytes, content-type {image_response.headers.get('Content-Type')}",
            )
        )

        status_response = _request(opener, f"{base_url}/mobile/status")
        status_body = status_response.read().decode("utf-8")
        status_json = json.loads(status_body)
        results.append(
            CheckResult(
                "/mobile/status",
                status_json.get("ok") is True
                and status_json.get("api") == "mobile-bridge-v0"
                and status_json.get("mobile_bridge", {}).get("profile")
                == "implemented"
                and status_json.get("mobile_bridge", {}).get("gps")
                == "implemented"
                and status_json.get("mobile_bridge", {}).get("imu")
                == "implemented_debug_only"
                and status_json.get("mobile_bridge", {}).get("camera_frame")
                == "implemented_storage_only"
                and status_json.get("pifinder", {}).get("lx200_port") == 4030,
                f"api {status_json.get('api')}, server_time {status_json.get('server_time_utc')}",
            )
        )

        profile_payload = json.dumps(
            {
                "schema": "pifinder-mobile-profile-v0",
                "device": {"model": "validator"},
                "sensors": {},
                "cameras": [],
                "readiness": {"grade": "HIGH"},
            }
        ).encode()
        profile_response = _request(
            opener,
            f"{base_url}/mobile/profile",
            method="POST",
            data=profile_payload,
            headers={"Content-Type": "application/json"},
        )
        profile_body = profile_response.read().decode("utf-8")
        profile_json = json.loads(profile_body)
        results.append(
            CheckResult(
                "/mobile/profile",
                profile_json.get("ok") is True
                and profile_json.get("stored_as") == "profile_latest.json",
                f"stored_as {profile_json.get('stored_as')}, received {profile_json.get('received_utc')}",
            )
        )

        invalid_profile_payload = json.dumps(["not", "an", "object"]).encode()
        try:
            invalid_profile_response = _request(
                opener,
                f"{base_url}/mobile/profile",
                method="POST",
                data=invalid_profile_payload,
                headers={"Content-Type": "application/json"},
            )
            invalid_profile_status = invalid_profile_response.status
            invalid_profile_body = invalid_profile_response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            invalid_profile_status, invalid_profile_body = _read_http_error(exc)

        invalid_profile_json = json.loads(invalid_profile_body)
        results.append(
            CheckResult(
                "/mobile/profile invalid",
                invalid_profile_status == 400
                and invalid_profile_json.get("ok") is False
                and invalid_profile_json.get("error", {}).get("code")
                == "invalid_json",
                f"status {invalid_profile_status}, code {invalid_profile_json.get('error', {}).get('code')}",
            )
        )

        gps_payload = json.dumps(
            {
                "lat": 40.4168,
                "lon": -3.7038,
                "altitude_m": 667.0,
                "accuracy_m": 8.0,
                "time_utc": "2026-05-03T00:00:00Z",
                "source": "validator",
            }
        ).encode()
        gps_response = _request(
            opener,
            f"{base_url}/mobile/gps",
            method="POST",
            data=gps_payload,
            headers={"Content-Type": "application/json"},
        )
        gps_body = gps_response.read().decode("utf-8")
        gps_json = json.loads(gps_body)
        results.append(
            CheckResult(
                "/mobile/gps",
                gps_json.get("ok") is True
                and gps_json.get("stored_as") == "gps_latest.json",
                f"stored_as {gps_json.get('stored_as')}, received {gps_json.get('received_utc')}",
            )
        )

        invalid_gps_payload = json.dumps(
            {
                "lat": 120.0,
                "lon": -3.7038,
                "time_utc": "2026-05-03T00:00:00Z",
                "source": "validator",
            }
        ).encode()
        try:
            invalid_gps_response = _request(
                opener,
                f"{base_url}/mobile/gps",
                method="POST",
                data=invalid_gps_payload,
                headers={"Content-Type": "application/json"},
            )
            invalid_gps_status = invalid_gps_response.status
            invalid_gps_body = invalid_gps_response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            invalid_gps_status, invalid_gps_body = _read_http_error(exc)

        invalid_gps_json = json.loads(invalid_gps_body)
        results.append(
            CheckResult(
                "/mobile/gps invalid",
                invalid_gps_status == 400
                and invalid_gps_json.get("ok") is False
                and invalid_gps_json.get("error", {}).get("code")
                == "invalid_gps",
                f"status {invalid_gps_status}, code {invalid_gps_json.get('error', {}).get('code')}",
            )
        )

        imu_payload = json.dumps(
            {
                "schema": "pifinder-mobile-imu-batch-v0",
                "device_time_utc": "2026-05-03T00:00:01Z",
                "samples": [
                    {
                        "sensor": "rotation_vector",
                        "t_android_ns": 1234567890,
                        "values": [0.0, 0.0, 0.0, 1.0],
                        "accuracy": 3,
                    },
                    {
                        "sensor": "game_rotation_vector",
                        "t_android_ns": 1234567990,
                        "values": [0.0, 0.1, 0.0, 0.995],
                        "accuracy": 3,
                    },
                ],
            }
        ).encode()
        imu_response = _request(
            opener,
            f"{base_url}/mobile/imu",
            method="POST",
            data=imu_payload,
            headers={"Content-Type": "application/json"},
        )
        imu_body = imu_response.read().decode("utf-8")
        imu_json = json.loads(imu_body)
        results.append(
            CheckResult(
                "/mobile/imu",
                imu_json.get("ok") is True
                and imu_json.get("stored_as") == "imu_latest.json"
                and imu_json.get("sample_count") == 2,
                f"stored_as {imu_json.get('stored_as')}, samples {imu_json.get('sample_count')}",
            )
        )

        invalid_imu_payload = json.dumps(
            {
                "samples": [
                    {
                        "sensor": "rotation_vector",
                        "t_android_ns": 1234567890,
                        "values": [0.0, "bad", 0.0],
                    }
                ]
            }
        ).encode()
        try:
            invalid_imu_response = _request(
                opener,
                f"{base_url}/mobile/imu",
                method="POST",
                data=invalid_imu_payload,
                headers={"Content-Type": "application/json"},
            )
            invalid_imu_status = invalid_imu_response.status
            invalid_imu_body = invalid_imu_response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            invalid_imu_status, invalid_imu_body = _read_http_error(exc)

        invalid_imu_json = json.loads(invalid_imu_body)
        results.append(
            CheckResult(
                "/mobile/imu invalid",
                invalid_imu_status == 400
                and invalid_imu_json.get("ok") is False
                and invalid_imu_json.get("error", {}).get("code")
                == "invalid_imu",
                f"status {invalid_imu_status}, code {invalid_imu_json.get('error', {}).get('code')}",
            )
        )

        frame_bytes = _sample_jpeg_bytes()
        camera_boundary = f"PiFinderValidator{int(time.time() * 1000)}"
        camera_frame_response = _request(
            opener,
            f"{base_url}/mobile/camera_frame",
            method="POST",
            data=_multipart_body(
                camera_boundary,
                {
                    "schema": "pifinder-mobile-camera-frame-v0",
                    "source": "validator",
                    "storage_only": True,
                    "solver_requested": False,
                },
                frame_bytes,
            ),
            headers={
                "Content-Type": f"multipart/form-data; boundary={camera_boundary}",
            },
        )
        camera_frame_status = camera_frame_response.status
        camera_frame_body = camera_frame_response.read().decode("utf-8")
        camera_frame_json = json.loads(camera_frame_body)
        results.append(
            CheckResult(
                "/mobile/camera_frame",
                camera_frame_status == 200
                and camera_frame_json.get("ok") is True
                and camera_frame_json.get("bytes") == len(frame_bytes)
                and camera_frame_json.get("solver_invoked") is False
                and camera_frame_json.get("frame_id"),
                f"status {camera_frame_status}, frame_id {camera_frame_json.get('frame_id')}",
            )
        )

        login_payload = urllib.parse.urlencode(
            {"password": "pifinder", "origin_url": "/remote"}
        ).encode()
        login_response = _request(
            opener,
            f"{base_url}/login",
            method="POST",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        login_response.read()

        remote_response = _request(
            opener,
            f"{base_url}/remote",
            headers={"User-Agent": "PiFinder-Lite-Mobile-Validation"},
        )
        remote_html = remote_response.read().decode("utf-8", errors="replace")
        remote_ok = all(
            marker in remote_html
            for marker in ("PiFinder Screen", "fetchImage()", "buttonClicked")
        )
        results.append(
            CheckResult(
                "/remote",
                remote_ok,
                f"HTML length {len(remote_html)} chars",
            )
        )

        key_payload = json.dumps({"button": "A"}).encode()
        key_response = _request(
            opener,
            f"{base_url}/key_callback",
            method="POST",
            data=key_payload,
            headers={"Content-Type": "application/json"},
        )
        key_body = key_response.read().decode("utf-8")
        try:
            queued_key = keyboard_queue.get(timeout=2)
            queue_detail = f"queued key {queued_key!r}"
        except queue.Empty:
            queued_key = None
            queue_detail = "no queued key"

        results.append(
            CheckResult(
                "/key_callback",
                '"success"' in key_body and queued_key is not None,
                f"response {key_body.strip()}, {queue_detail}",
            )
        )
    finally:
        pass
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Serve the fake PiFinder remote until interrupted.",
    )
    args = parser.parse_args()

    if args.serve:
        print(f"Serving PiFinder remote validation on http://{args.host}:{args.port}")
        serve(args.host, args.port)
        return 0

    results = run_validation(args.port)
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status} {result.name}: {result.detail}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
