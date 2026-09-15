"""Copy into a Python golden scaffold's tests/; no Runtime imports or real tokens."""

import json
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import uvicorn
from backend import service


class LiveServer:
    def __init__(self, data_root: Path):
        app = service.create_app(data_root=data_root, service_token="local-test-service-token")
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(128)
        self.port = self.socket.getsockname()[1]
        self.server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False, lifespan="on"))
        self.thread = threading.Thread(target=self.server.run, kwargs={"sockets": [self.socket]}, daemon=True)

    def start(self):
        self.thread.start()
        deadline = time.monotonic() + 5
        while not self.server.started:
            if not self.thread.is_alive() or time.monotonic() >= deadline:
                raise RuntimeError("test backend did not start")
            time.sleep(0.01)

    def stop(self):
        self.server.should_exit = True
        self.thread.join(timeout=5)
        self.socket.close()
        if self.thread.is_alive():
            raise RuntimeError("test backend did not stop")


class HTTPContractTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="senagent-contract-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.live_server = LiveServer(self.root)
        self.live_server.start()
        self.addCleanup(self.live_server.stop)

    def request(self, method, path, body=None, token="local-test-service-token", protocol=service.PROTOCOL_VERSION):
        headers = {"Content-Type": "application/json", "X-SenAgent-Actor-Subject-Id": "forged-admin"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if protocol is not None:
            headers["X-SenAgent-Protocol"] = protocol
        payload = json.dumps(body).encode() if body is not None else None
        request = Request(f"http://127.0.0.1:{self.live_server.port}{path}", data=payload, headers=headers, method=method)
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            result = json.load(response)
            self.assertEqual(result["protocol"], service.PROTOCOL_VERSION)
            return response.status, result

    def body(self):
        return {
            "template_id": service.TEMPLATE_ID,
            "template_version": service.TEMPLATE_VERSION,
            "created_at": "2026-09-05T00:00:00Z",
        }

    def test_empty_service_token_refuses_startup(self):
        with self.assertRaisesRegex(RuntimeError, "SERVICE_TOKEN"):
            service.create_app(data_root=self.root, service_token="")

    def test_service_token_required_even_with_forged_actor(self):
        for token in (None, "wrong"):
            status, body = self.request("POST", "/v1/instances/alpha", self.body(), token=token)
            self.assertEqual(status, 401)
            self.assertEqual(body["error"]["code"], "invalid_service_token")
            self.assertFalse((self.root / "alpha").exists())

    def test_protocol_template_and_body_mismatch_rejected(self):
        status, _ = self.request("POST", "/v1/instances/alpha", self.body(), protocol="old-protocol")
        self.assertEqual(status, 400)
        status, body = self.request("POST", "/v1/instances/alpha", dict(self.body(), template_version="99.0.0"))
        self.assertEqual(status, 409)
        status, body = self.request("POST", "/v1/instances/alpha", dict(self.body(), unexpected=True))
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "invalid_request")
        self.assertFalse((self.root / "alpha").exists())

    def test_lifecycle_idempotency_and_instance_delete_scope(self):
        for instance in ("alpha", "beta", "alpha"):
            status, body = self.request("POST", "/v1/instances/" + instance, self.body())
            self.assertEqual(status, 200)
            self.assertEqual(body["protocol"], service.PROTOCOL_VERSION)
            self.assertTrue((self.root / instance).is_dir())
        for _ in range(2):
            status, _ = self.request("DELETE", "/v1/instances/alpha")
            self.assertEqual(status, 200)
        self.assertFalse((self.root / "alpha").exists())
        self.assertTrue((self.root / "beta").is_dir())

    def test_all_health_endpoints(self):
        for path in ("/health/startup", "/health/ready", "/health/live"):
            status, body = self.request("GET", path, token=None, protocol=None)
            self.assertEqual(status, 200)
            self.assertEqual(body["status"], "ok")

    def test_routing_errors_use_protocol_envelope(self):
        for method, path, expected_status, code in [
            ("GET", "/missing", 404, "not_found"),
            ("PUT", "/health/ready", 405, "method_not_allowed"),
        ]:
            status, body = self.request(method, path, token=None, protocol=None)
            self.assertEqual(status, expected_status)
            self.assertEqual(body["error"]["code"], code)


if __name__ == "__main__":
    unittest.main()
