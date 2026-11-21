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

PROBES: list[tuple[str, str]] = [
    ("google", "https://www.google.com/"),
    ("duckduckgo", "https://duckduckgo.com/"),
    ("brave", "https://search.brave.com/"),
    ("bing", "https://www.bing.com/"),
    ("yandex", "https://yandex.com/"),
    ("startpage", "https://www.startpage.com/"),
    ("qwant", "https://www.qwant.com/"),
    ("seznam", "https://www.seznam.cz/"),
    ("aol", "https://search.aol.com/"),
    ("wikipedia", "https://en.wikipedia.org/"),
    ("wikidata", "https://www.wikidata.org/"),
    ("wikinews", "https://wikinews.wikipedia.org/"),
    ("wiktionary", "https://en.wiktionary.org/"),
    ("wikicommons", "https://commons.wikimedia.org/"),
    ("arch linux wiki", "https://wiki.archlinux.org/"),
    ("arxiv", "https://arxiv.org/"),
    ("github", "https://github.com/"),
    ("mdn", "https://developer.mozilla.org/"),
    ("stackoverflow", "https://stackoverflow.com/"),
    ("askubuntu", "https://askubuntu.com/"),
    ("superuser", "https://superuser.com/"),
    ("reuters", "https://www.reuters.com/"),
    ("yahoo", "https://news.yahoo.com/"),
    ("youtube", "https://www.youtube.com/"),
    ("dailymotion", "https://www.dailymotion.com/"),
    ("vimeo", "https://vimeo.com/"),
    ("flickr", "https://www.flickr.com/"),
    ("pinterest", "https://www.pinterest.com/"),
    ("pexels", "https://www.pexels.com/"),
    ("unsplash", "https://unsplash.com/"),
    ("openverse", "https://api.openverse.org/"),
    ("deviantart", "https://www.deviantart.com/"),
    ("bandcamp", "https://bandcamp.com/"),
    ("soundcloud", "https://soundcloud.com/"),
    ("mastodon", "https://joinmastodon.org/"),
    ("lemmy", "https://join-lemmy.org/"),
    ("piratebay", "https://thepiratebay.org/"),
    ("bt4g", "https://bt4g.org/"),
    ("solidtorrents", "https://solidtorrents.to/"),
    ("kickass", "https://kickasstorrents.to/"),
    ("torrent", "https://thepiratebay.org/"),
    ("docker hub", "https://hub.docker.com/"),
    ("pypi", "https://pypi.org/"),
    ("pubmed", "https://pubmed.ncbi.nlm.nih.gov/"),
    ("semantic scholar", "https://www.semanticscholar.org/"),
    ("openaire", "https://explore.openaire.eu/"),
    ("pdbe", "https://www.ebi.ac.uk/pdbe/"),
    ("etymonline", "https://www.etymonline.com/"),
    ("wordnik", "https://www.wordnik.com/"),
    ("lingva", "https://lingva.ml/"),
    ("dictzone", "https://dictzone.com/"),
    ("mymemory", "https://mymemory.translated.net/"),
    ("currency", "https://www.xe.com/"),
    ("wttr", "https://wttr.in/"),
    ("photon", "https://photon.komoot.io/"),
    ("openstreetmap", "https://www.openstreetmap.org/"),
    ("genius", "https://genius.com/"),
    ("mixcloud", "https://www.mixcloud.com/"),
    ("chefkoch", "https://www.chefkoch.de/"),
    ("gentoo", "https://www.gentoo.org/"),
    ("devicons", "https://devicon.dev/"),
    ("lucide", "https://lucide.dev/"),
    ("hoogle", "https://hoogle.haskell.org/"),
    ("karmasearch", "https://karmasearch.org/"),
    ("sepiasearch", "https://sepiasearch.org/"),
    ("radio browser", "https://www.radio-browser.info/"),
    ("artic", "https://www.artic.edu/"),
    ("ahmia", "https://ahmia.fi/"),
]

FOREIGN_PROBES = [
    ("google", "https://www.google.com/"),
    ("duckduckgo", "https://duckduckgo.com/"),
    ("brave", "https://search.brave.com/"),
]

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


def probe_key(name: str) -> str | None:
    lowered = name.lower()
    for key, _ in PROBES:
        if key in lowered:
            return key
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
    foreign = probe_all(FOREIGN_PROBES)
    is_foreign = any(foreign.values())
    disable = set(EXCLUDED) | BROKEN
    if is_foreign:
        mode = "foreign"
    else:
        mode = "domestic"
        available = probe_all(PROBES)
        for name in engines:
            if name in disable:
                continue
            key = probe_key(name)
            if key is None or not available.get(key, False):
                disable.add(name)
    active = [name for name in engines if name not in disable]
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(render(template, disable), encoding="utf-8")
    temporary.replace(output)
    return mode, len(active), len(disable)
