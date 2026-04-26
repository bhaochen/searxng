# SearXNG Meta Search Engine

A self-hosted meta search engine running in Docker, aggregating results from multiple search engines.

## Quick Start

```bash
# Start services
docker compose up -d

# Access the interface
# Visit http://localhost:8080
```

## Project Structure

```
searxng/
├── docker-compose.yml       # Container orchestration
├── .env                    # Environment variables
├── core-config/
│   └── settings.yml        # Main configuration
└── .env.example            # Environment template
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_VERSION` | Docker image tag | latest |
| `SEARXNG_HOST` | Listen address | - |
| `SEARXNG_PORT` | Listen port | 8080 |

### Main Settings (settings.yml)

- **Server**: Port 8888 (internal), exposed on 8080
- **Search**: SafeSearch level 0 (none), no autocomplete by default
- **UI**: Simple theme, auto dark mode support
- **Outgoing**: 3s timeout, HTTP/2 enabled

## Enabled Search Engines

### General
- arch linux wiki, arxiv, bandcamp, brave, currency converter
- duckduckgo, google, wikipedia, wikidata, yandex

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
# Restart services
docker compose restart

# Stop services
docker compose down

# View logs
docker logs searxng-core

# Update image
docker compose pull
docker compose up -d
```

## Ports

| Service | Internal Port | External Port |
|--------|--------------|--------------|
| searxng-core | 8888 | 8080 |
| valkey (cache) | 6379 | - (not exposed) |

## Documentation

- [Official Docs](https://docs.searxng.org/)
- [Settings Guide](https://docs.searxng.org/admin/settings/settings_general.html)
- [Engine List](https://searxng.github.io/searxng/admin/engines.html)

## License

This project is for local/private use. SearXNG is AGPL licensed. See [searxng/searxng](https://github.com/searxng/searxng) for details.