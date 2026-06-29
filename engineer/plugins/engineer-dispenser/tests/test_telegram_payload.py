import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _DummyAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        raise RuntimeError("post should not be called in this test")


from unittest import mock

def _load_dispenser():
    httpx_stub = types.ModuleType("httpx")
    httpx_stub.AsyncClient = _DummyAsyncClient

    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None

    module_path = Path(__file__).resolve().parents[1] / "__init__.py"
    module_spec = importlib.util.spec_from_file_location(
        "engineer_dispenser",
        module_path,
        submodule_search_locations=[str(module_path.parent)],
    )
    dispenser = importlib.util.module_from_spec(module_spec)
    with mock.patch.dict(sys.modules, {"httpx": httpx_stub, "dotenv": dotenv_stub}):
        sys.modules[module_spec.name] = dispenser
        module_spec.loader.exec_module(dispenser)
    return dispenser

dispenser = _load_dispenser()


class TelegramPayloadTests(unittest.TestCase):
    def test_build_telegram_payload_escapes_dynamic_html_content(self):
        payload = dispenser._build_telegram_payload(
            chat_id="-100123",
            text="<b>Title</b>\nSummary with <tag> & special chars",
        )

        self.assertEqual(payload["chat_id"], "-100123")
        self.assertEqual(payload["parse_mode"], "HTML")
        self.assertEqual(
            payload["text"],
            "&lt;b&gt;Title&lt;/b&gt;\nSummary with &lt;tag&gt; &amp; special chars",
        )

    def test_log_task_exception_logs_async_failures(self):
        loop = asyncio.new_event_loop()
        try:
            task = loop.create_future()
            task.set_exception(RuntimeError("broadcast failed"))

            with self.assertLogs(dispenser.logger, level="ERROR") as logs:
                dispenser._log_task_exception(task)

            self.assertTrue(any("broadcast failed" in message for message in logs.output))
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
