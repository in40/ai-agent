import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import playwright.async_api as pw

SEARXNG_URL = os.getenv("SEARXNG_ENGINE_API_BASE_URL", "http://searxng-core:8080/search")
SEARXNG_CONFIG_URL = os.getenv("SEARXNG_CONFIG_URL", "http://searxng-core:8080/config")

YANDEX_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 YaBrowser/26.4.0.2182 Yowser/2.5 Safari/537.36"

JS_INDICATORS = ["Please enable JavaScript", "enable JS", "Возникла проблема при открытии сайта"]

app: FastAPI
http_client: Optional[httpx.AsyncClient] = None
playwright_browser: Optional[pw.Browser] = None
session_id: str = str(uuid.uuid4())
_enabled_engines: list[dict] = []


async def searxng_search(query: str, category: str = "general", engines: str | None = None, safesearch: str | None = None, time_range: str | None = None, pageno: str = "1") -> str:
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=120.0)

    params = {"q": query, "format": "json", "pageno": 1, "categories": category}
    if engines:
        params["engines"] = engines
    if safesearch and safesearch in ["0", "1", "2"]:
        params["safesearch"] = safesearch
    if time_range and time_range in ["day", "month", "year"]:
        params["time_range"] = time_range
    if pageno:
        try:
            params["pageno"] = max(1, int(pageno))
        except ValueError:
            pass

    try:
        resp = await http_client.get(f"{SEARXNG_URL}", params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"SearXNG search failed: {e}"

    results = data.get("results", [])
    if not results:
        return "No results found."

    top_urls = [r.get("url", "") for r in results[:10] if r.get("url")]
    scraped = await asyncio.gather(*[fetch_page_text(u) for u in top_urls], return_exceptions=True)

    output_parts = []
    for i, result in enumerate(results[:10]):
        if i > 0:
            output_parts.append("\n====================\n")
        output_parts.append(f"**Title:** {result.get('title', 'N/A')}")
        output_parts.append(f"**URL:** {result.get('url', 'N/A')}")
        snippet = result.get("content")
        if snippet:
            output_parts.append(f"\n**Snippet:** {snippet}")
        if i < len(scraped) and isinstance(scraped[i], str) and scraped[i]:
            output_parts.append(f"\n**Full text:** {scraped[i][:5500]}")

    return "\n".join(output_parts)


async def fetch_page_text(url: str, text_only: bool = True) -> str:
    global http_client, playwright_browser
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=120.0, headers={"User-Agent": YANDEX_UA})

    try:
        resp = await http_client.get(url, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)[:6000]
        if not any(indicator.lower() in text.lower() for indicator in JS_INDICATORS):
            return text
    except Exception:
        pass

    if playwright_browser:
        try:
            ctx = await playwright_browser.new_context(
                user_agent=YANDEX_UA,
                viewport={"width": 1920, "height": 1080}
            )
            page = await ctx.new_page()
            try:
                await page.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>undefined})')
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(1)
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                text = soup.get_text(separator=" ", strip=True)[:6000]
                return text
            except Exception:
                return ""
            finally:
                await page.close()
                await ctx.close()
        except Exception:
            return ""
    return ""


async def scrape_website(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    text = await fetch_page_text(url)
    if text:
        soup = BeautifulSoup(f"<html><body>{text[:500]}</body></html>", "html.parser")
        return f"**URL:** {url}\n\n**Content:**\n{text[:3000]}"
    return f"Error fetching {url}: content unavailable"


async def get_current_datetime() -> str:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return f"The current date and time is {now.strftime('%A, %B %d, %Y at %I:%M %p UTC')}"


def build_engines_description() -> str:
    if not _enabled_engines:
        return "No enabled engines found. Call list_search_engines to discover available engines."
    lines = ["Available engines (use full name or shortcut):"]
    for eng in _enabled_engines:
        name = eng.get("name", "?")
        categories = ", ".join(eng.get("categories", []))
        shortcut = eng.get("shortcut", "")
        shortcut_str = f" ({shortcut})" if shortcut else ""
        lines.append(f"  - {name}{shortcut_str} [{categories}]")
    return "\n".join(lines)


async def refresh_enabled_engines():
    global _enabled_engines
    try:
        resp = await http_client.get(SEARXNG_CONFIG_URL)
        resp.raise_for_status()
        data = resp.json()
        _enabled_engines = [e for e in data.get("engines", []) if e.get("enabled")]
        print(f"Loaded {len(_enabled_engines)} enabled engines", file=sys.stderr)
    except Exception as e:
        print(f"Failed to fetch engines: {e}", file=sys.stderr)
        _enabled_engines = []


@asynccontextmanager
async def lifespan(server_app: FastAPI):
    global http_client, playwright_browser
    http_client = httpx.AsyncClient(timeout=120.0, headers={"User-Agent": YANDEX_UA})
    await refresh_enabled_engines()
    try:
        p = await pw.async_playwright().start()
        playwright_browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        print("Playwright browser started", file=sys.stderr)
    except Exception as e:
        print(f"Playwright failed to start: {e}", file=sys.stderr)
        playwright_browser = None
    print("MCP bridge: initialized", file=sys.stderr)
    yield
    if playwright_browser:
        await playwright_browser.close()
    if http_client:
        await http_client.aclose()
    print("MCP bridge: stopped", file=sys.stderr)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "mcp": "connected"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
        )

    method = data.get("method")
    params = data.get("params", {})
    rid = data.get("id")

    # Handle notifications (no id) - just acknowledge them
    if rid is None and method and method.startswith("notifications/"):
        return JSONResponse(
            content={"jsonrpc": "2.0", "result": None},
            headers={"Mcp-Session-Id": session_id}
        )

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "searxng-mcp", "version": "1.0.0"},
                "capabilities": {
                    "tools": {}
                }
            }
        elif method == "tools/list":
            engines_desc = build_engines_description()
            result = {
                "tools": [
                    {
                        "name": "search_web",
                        "description": "Search the web using SearXNG. Returns up to ~20 results per page.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query (supports operators like site:, filetype:, etc. depending on engine)."},
                                "engines": {"type": "string", "description": f"Comma-separated engine names to restrict search to specific engines. Leave empty to search all enabled engines.\n\n{engines_desc}"},
                                "category": {"type": "string", "description": "Search category. Use 'news' for current events/news articles, 'images' for pictures, 'videos' for video content, 'general' for broad web search. Default: 'general'.", "default": "general"},
                                "safesearch": {"type": "string", "description": "Safe search level: 0=off (include explicit), 1=moderate (filter explicit), 2=strict (safe only). Default depends on instance settings.", "enum": ["0", "1", "2"]},
                                "time_range": {"type": "string", "description": "Time range filter. Use 'day' for very recent/breaking news, 'month' for current events/past month, 'year' for research/historical context. Leave unset for no time restriction. Only works with engines that support it.", "enum": ["day", "month", "year"]},
                                "pageno": {"type": "string", "description": "Page number for pagination (1 = first page, 2 = second, etc.). Default: 1."},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "get_website",
                        "description": "Scrape content from web pages.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "description": "The URL of the website."},
                            },
                            "required": ["url"],
                        },
                    },
                    {
                        "name": "get_current_datetime",
                        "description": "Get the current date and time.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})

            if tool_name == "search_web":
                text = await searxng_search(
                    query=tool_args["query"],
                    category=tool_args.get("category", "general"),
                    engines=tool_args.get("engines"),
                    safesearch=tool_args.get("safesearch"),
                    time_range=tool_args.get("time_range"),
                    pageno=tool_args.get("pageno", "1"),
                )
                result = {"content": [{"type": "text", "text": text}], "isError": False}
            elif tool_name == "get_website":
                text = await scrape_website(tool_args["url"])
                result = {"content": [{"type": "text", "text": text}], "isError": False}
            elif tool_name == "get_current_datetime":
                text = await get_current_datetime()
                result = {"content": [{"type": "text", "text": text}], "isError": False}
            else:
                result = {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}
        elif method == "ping":
            result = {}
        else:
            result = {}

        response = {"jsonrpc": "2.0", "id": rid, "result": result}
        return JSONResponse(
            content=response,
            headers={"Mcp-Session-Id": session_id}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_response = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": rid}
        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={"Mcp-Session-Id": session_id}
        )


@app.delete("/mcp")
async def mcp_delete(request: Request):
    return Response(status_code=204)


@app.get("/mcp")
async def mcp_get(request: Request):
    return Response(status_code=200)


if __name__ == "__main__":
    import uvicorn
    print("Starting MCP server...", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=8082)
