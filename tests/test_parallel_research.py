import asyncio
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import httpx
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import parallel_search
from logger import RunLogger
from research_topic import research_topic
from search_topic import TopicExhaustedError, find_unique_topic
from write_post import generate_post_content


class ParallelResearchTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config.json").read_text())
        self.config["generation"]["research_provider"] = "parallel"
        self.config["generation"]["search_attempts"] = 1
        self.requests = []
        self.tool_calls = []
        self.sources = [
            {"title": "A fresh technical topic", "url": "https://example.org/article",
             "excerpts": ["Technical evidence", "Latest announcement"]},
            {"title": "Duplicate", "url": "https://example.org/article", "excerpts": ["duplicate"]},
            {"title": None, "url": "https://example.org/other", "excerpts": ["More evidence"]},
        ]
        self.tool_result = None
        self.failure = None
        self.slow = False
        real_client = httpx.AsyncClient

        async def respond(request):
            self.requests.append(request)
            if self.failure:
                raise self.failure
            body = json.loads(request.content)
            method = body["method"]
            if method == "notifications/initialized":
                return httpx.Response(202)
            if method == "initialize":
                result = {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}},
                          "serverInfo": {"name": "fixture", "version": "1"}}
            elif method == "tools/list":
                result = {"tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]}
            elif method == "tools/call":
                self.tool_calls.append(body["params"])
                if self.slow:
                    await asyncio.Event().wait()
                result = self.tool_result if self.tool_result is not None else {
                    "content": [], "structuredContent": {"results": self.sources}, "isError": False,
                }
            else:
                raise AssertionError(method)
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": result})

        def make_client(**kwargs):
            return real_client(transport=httpx.MockTransport(respond), **kwargs)

        self.client_patch = patch.object(parallel_search.httpx, "AsyncClient", side_effect=make_client)
        self.client_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_selection_to_research_to_writer_and_log(self):
        logger = RunLogger()
        topic, candidates = find_unique_topic(self.config, [], logger)
        self.assertEqual(topic, "A fresh technical topic")
        self.assertEqual(len(candidates), 2)
        bundle = research_topic(topic, self.config, logger)
        self.assertEqual(bundle["combined_text"], "Technical evidence\n\nLatest announcement\n\nMore evidence")
        self.assertEqual(bundle["sources"][1]["title"], "https://example.org/other")
        client = Mock(model_name="fixture-writer")
        client.generate.return_value = 'Post body\n```json\n{"title":"Post","slug":"post","tags":[]}\n```'
        with patch("write_post.get_ai_client", return_value=client):
            self.assertEqual(generate_post_content(bundle, self.config)["markdown_body"], "Post body")
        prompt = client.generate.call_args.args[1]
        self.assertIn("Technical evidence", prompt)
        self.assertIn("[A fresh technical topic](https://example.org/article)", prompt)
        self.assertEqual(logger.sources_count, 2)
        self.assertEqual(logger.sources[0]["url"], "https://example.org/article")
        self.assertEqual(len(self.tool_calls), 2)
        self.assertEqual(self.tool_calls[0]["name"], "web_search")
        args = self.tool_calls[1]["arguments"]
        self.assertEqual(len(args["search_queries"]), 3)
        self.assertIn(topic, args["objective"])
        self.assertEqual(args["session_id"], self.tool_calls[0]["arguments"]["session_id"])
        for request in self.requests:
            self.assertEqual(str(request.url), "https://search.parallel.ai/mcp")
            self.assertEqual(request.headers["User-Agent"], parallel_search.USER_AGENT)
            self.assertNotIn("Authorization", request.headers)

    def test_duplicate_topics_and_empty_research(self):
        with self.assertRaises(TopicExhaustedError):
            find_unique_topic(self.config, [{"title": s["title"] or s["url"]} for s in self.sources])
        self.sources = []
        with self.assertRaisesRegex(RuntimeError, "no research excerpts"):
            research_topic("topic", self.config)
        self.sources = [{"url": "https://example.org", "excerpts": ["  "]}]
        with self.assertRaisesRegex(RuntimeError, "no research excerpts"):
            research_topic("topic", self.config)

    def test_research_length_bound(self):
        self.sources[0]["excerpts"] = ["x" * 9000]
        self.assertEqual(len(research_topic("topic", self.config)["combined_text"]), 8000)

    def test_mcp_error_does_not_fall_back(self):
        self.tool_result = {"isError": True, "content": [{"type": "text", "text": "quota exceeded"}]}
        with patch("research_topic._research_with_tavily") as fallback:
            with self.assertRaisesRegex(RuntimeError, "quota exceeded"):
                research_topic("topic", self.config)
            fallback.assert_not_called()

    def test_malformed_response_stops_generation(self):
        for payload in ({}, {"results": "bad"}, {"results": [None]},
                        {"results": [{"url": "bad", "excerpts": []}]},
                        {"results": [{"url": "https://example.org", "excerpts": [1]}]}):
            with self.subTest(payload=payload):
                self.tool_result = {"content": [], "structuredContent": payload}
                with self.assertRaises(RuntimeError):
                    research_topic("topic", self.config)

    def test_http_failure_and_timeout(self):
        self.failure = httpx.ConnectError("connection failed")
        with self.assertRaisesRegex(RuntimeError, "connection failed"):
            research_topic("topic", self.config)
        self.failure = None
        self.slow = True
        with patch.object(parallel_search, "REQUEST_TIMEOUT", 0.05):
            with self.assertRaises(RuntimeError):
                research_topic("topic", self.config)

    def test_cancellation_propagates(self):
        self.slow = True

        async def cancel():
            task = asyncio.create_task(parallel_search._search("objective", ["query"]))
            while not self.tool_calls:
                await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        asyncio.run(cancel())

    def test_existing_routes_and_config_preserved(self):
        original = json.loads((ROOT / "config.json").read_text())
        self.assertEqual(original["generation"]["research_provider"], "gemini")
        for provider, has_key, expected in [(None, False, "tavily"), ("tavily", False, "tavily"),
                                             ("gemini", False, "tavily"), ("gemini", True, "gemini")]:
            with self.subTest(provider=provider, has_key=has_key):
                config = copy.deepcopy(self.config)
                if provider is None:
                    del config["generation"]["research_provider"]
                else:
                    config["generation"]["research_provider"] = provider
                env = {"GEMINI_API_KEY": "fixture"} if has_key else {}
                with patch.dict(os.environ, env, clear=True), \
                        patch("search_topic._search_with_gemini", return_value=[{"title": "New"}]) as gs, \
                        patch("search_topic._search_with_tavily", return_value=[{"title": "New"}]) as ts, \
                        patch("research_topic._research_with_gemini", return_value={}) as gr, \
                        patch("research_topic._research_with_tavily", return_value={}) as tr:
                    find_unique_topic(config, [])
                    research_topic("New", config)
                    self.assertEqual(gs.called, expected == "gemini")
                    self.assertEqual(gr.called, expected == "gemini")
                    self.assertEqual(ts.called, expected == "tavily")
                    self.assertEqual(tr.called, expected == "tavily")
        self.assertEqual(self.requests, [])

    def test_config_schema_accepts_opt_in(self):
        schema = json.loads((ROOT / "schemas/config.schema.json").read_text())
        jsonschema.validate(self.config, schema)


if __name__ == "__main__":
    unittest.main()
