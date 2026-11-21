from __future__ import annotations

import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ENGINE_RE = re.compile(r'^  - name:\s*(.+?)\s*$')
FLAG_RE = re.compile(r'^(\s+)(disabled|inactive):\s*(true|false)\s*$')

EXCLUDED = {
    "baidu",
    "baidu images",
    "baidu kaifa",
    "sogou",
    "sogou images",
    "sogou videos",
    "sogou wechat",
}

BROKEN = {
    "presearch",
    "presearch images",
    "presearch videos",
    "presearch news",
    "reddit",
    "svgrepo",
    "library of congress",
    "podcastindex",
    "torch",
    "seznam",
}

FOREIGN_PROBES = [
    ("google", "https://www.google.com/"),
    ("duckduckgo", "https://duckduckgo.com/"),
    ("brave", "https://search.brave.com/"),
]

DOMESTIC_PROBES = [
    ("bing", "https://www.bing.com/"),
    ("duckduckgo", "https://duckduckgo.com/"),
]
PROBE_URLS = dict(FOREIGN_PROBES + DOMESTIC_PROBES)

TIMEOUT = 5.0
ATTEMPTS = 3


def reachable(url: str) -> bool:
    for _ in range(ATTEMPTS):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                response.read(1)
                return True
        except Exception:
            continue
    return False


def probe_all(items: list[tuple[str, str]]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(reachable, url): key for key, url in items}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


def collect_engines(template: Path) -> list[str]:
    engines: list[str] = []
    for line in template.read_text(encoding="utf-8").splitlines():
        match = ENGINE_RE.match(line)
        if not match:
            continue
        engines.append(match.group(1).strip().strip('"').strip("'"))
    return engines


def domestic_key(name: str) -> str | None:
    lowered = name.lower()
    if "duckduckgo" in lowered:
        return "duckduckgo"
    if "bing" in lowered:
        return "bing"
    return None


def render(template: Path, disable: set[str]) -> str:
    lines = template.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    current: str | None = None
    has_flag = False
    for line in lines:
        match = ENGINE_RE.match(line)
        if match:
            if current is not None and current in disable and not has_flag:
                output.append("    disabled: true")
            current = match.group(1).strip().strip('"').strip("'")
            has_flag = False
        flag = FLAG_RE.match(line)
        if current is not None and flag:
            has_flag = True
            if flag.group(2) == "disabled":
                if current in disable:
                    line = f"{flag.group(1)}disabled: true"
                else:
                    continue
        output.append(line)
    if current is not None and current in disable and not has_flag:
        output.append("    disabled: true")
    return "\n".join(output) + "\n"


def generate_active_settings(template: Path, output: Path) -> tuple[str, int, int]:
    engines = collect_engines(template)
    disable = set(EXCLUDED) | BROKEN
    available = probe_all(list(PROBE_URLS.items()))
    if any(available.get(key) for key, _ in FOREIGN_PROBES):
        mode = "foreign"
    else:
        mode = "domestic"
        for name in engines:
            if name in disable:
                continue
            key = domestic_key(name)
            if key is None or not available.get(key, False):
                disable.add(name)
    active = [name for name in engines if name not in disable]
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(render(template, disable), encoding="utf-8")
    temporary.replace(output)
    return mode, len(active), len(disable)
