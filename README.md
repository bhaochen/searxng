# SearXNG Meta Search Engine

A self-hosted meta search engine running in Docker, aggregating results from multiple search engines.

## Quick Start

```bash
# Install and start the lazy wake proxy
./start.sh

# Wake explicitly
./wake.sh

# Access the interface; any request wakes the backend first
# Visit http://127.0.0.1:18081
```

The proxy listens on `127.0.0.1:18081` and keeps the backend sleeping until the
first request. It stops the Compose stack with `docker compose stop` after
`SEARXNG_IDLE_TIMEOUT_SECONDS` without activity. Containers are reused on the
next wake; data volumes are never removed.

Codev can use the wake endpoint directly:

```bash
export SEARXNG_BASE_URL=http://127.0.0.1:18081
export SEARXNG_WAKE_URL=http://127.0.0.1:18081/wake
```

## Project Structure

```
searxng/
├── docker-compose.yml       # Container orchestration
├── wake_proxy.py            # Always-on loopback wake proxy
├── searxng-wake.service.in  # systemd user service template
├── install-service.sh       # Install the user service
├── wake.sh / sleep.sh       # Manual wake / sleep helpers
├── .env                     # Environment variables
├── core-config/
│   └── settings.yml        # Main configuration
├── overrides/
│   └── sitecustomize.py    # Disable curl_cffi browser impersonation
└── .env.example            # Environment template
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_VERSION` | Docker image tag | latest |
| `SEARXNG_HOST` | Backend bind address | 127.0.0.1 |
| `SEARXNG_PORT` | Container port | 8080 |
| `SEARXNG_BACKEND_PORT` | Host-side backend port behind the proxy | 18080 |
| `SEARXNG_PROXY_HOST` | Wake proxy bind address | 127.0.0.1 |
| `SEARXNG_PROXY_PORT` | Wake proxy port | 18081 |
| `SEARXNG_IDLE_TIMEOUT_SECONDS` | Stop the backend after this idle period | 300 |
| `SEARXNG_WAKE_TIMEOUT_SECONDS` | Maximum wake readiness wait | 120 |
| `SEARXNG_SEARCH_TIMEOUT_SECONDS` | Proxied request timeout | 120 |

### Main Settings (settings.yml)

- **Server**: Container port 8080, exposed on host port 18080
- **Search**: SafeSearch level 0 (none), no autocomplete by default
- **UI**: Simple theme, auto dark mode support
- **Outgoing**: 10s timeout, HTTP/2 disabled, browser impersonation disabled

## Enabled Search Engines

### General
- bing, yandex, wikipedia, wikidata, aol, karmasearch
- google, duckduckgo, brave, startpage, baidu and seznam are disabled in this environment

### Images
- bing images, duckduckgo images, flickr, openverse, pexels, pixabay

### Videos
- bing videos, duckduckgo videos, google videos, piped

### News
- bing news, duckduckgo news, google news, qwant news, reuters

### IT / Development
- github, gitlab, stackoverflow,MDN, docker hub

### Science
- arxiv, crossref, openalex, pubmed, semantic scholar

### Maps & Weather
- openstreetmap

### Music
- deezer, soundcloud, mixcloud

## Available Plugins

The following plugins are enabled by default:

- Calculator (`searx.plugins.calculator`)
- Hash Generator (`searx.plugins.hash_plugin`)
- Self Info (`searx.plugins.self_info`)
- Unit Converter (`searx.plugins.unit_converter`)
- AHMIA Filter (`searx.plugins.ahmia_filter`)
- Hostnames (`searx.plugins.hostnames`)
- Time Zone (`searx.plugins.time_zone`)
- Tracker URL Remover (`searx.plugins.tracker_url_remover`)

## Management

```bash
# Start the wake proxy
./start.sh

# Start the backend directly without the proxy
./start.sh --backend

# Wake the backend
./wake.sh

# Put the backend to sleep; add --proxy to also stop the proxy
./stop.sh
./stop.sh --proxy

# View logs
journalctl --user -u searxng-wake.service -f
docker logs searxng-core

# Update image
docker compose pull
./wake.sh
```

## Ports

| Service | Internal Port | Host Port |
|--------|--------------|-----------|
| searxng-wake proxy | - | 127.0.0.1:18081 |
| searxng-core | 8080 | 127.0.0.1:18080 |
| valkey (cache) | 6379 | - (not exposed) |

## Documentation

- [Official Docs](https://docs.searxng.org/)
- [Settings Guide](https://docs.searxng.org/admin/settings/settings_general.html)
- [Engine List](https://searxng.github.io/searxng/admin/engines.html)

## License

This project is for local/private use. SearXNG is AGPL licensed. See [searxng/searxng](https://github.com/searxng/searxng) for details.