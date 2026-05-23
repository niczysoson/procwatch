# procwatch

Minimal process monitor that restarts services on failure with configurable backoff.

---

## Installation

```bash
pip install procwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/procwatch.git && cd procwatch && pip install .
```

---

## Usage

Define your watched processes in a `procwatch.yaml` config file:

```yaml
processes:
  web:
    command: "gunicorn app:app -w 4"
    backoff:
      initial: 1
      multiplier: 2
      max: 30
  worker:
    command: "celery -A tasks worker"
    backoff:
      initial: 2
      multiplier: 1.5
      max: 60
```

Then start the monitor:

```bash
procwatch start
```

Or point to a specific config:

```bash
procwatch start --config /etc/procwatch/config.yaml
```

**procwatch** will automatically restart any process that exits unexpectedly, applying exponential backoff between restart attempts to avoid thrashing.

---

## Options

| Flag | Description |
|------|-------------|
| `--config` | Path to config file (default: `./procwatch.yaml`) |
| `--log-level` | Logging verbosity: `debug`, `info`, `warn` (default: `info`) |

---

## License

MIT © 2024 Your Name