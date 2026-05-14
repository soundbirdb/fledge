# fledge

A minimal job queue daemon for running periodic data ingestion tasks, configured via TOML.

---

## Installation

```bash
pip install fledge
```

Or install from source:

```bash
git clone https://github.com/yourname/fledge.git && cd fledge && pip install .
```

---

## Usage

Define your jobs in a `fledge.toml` file:

```toml
[job.fetch_users]
schedule = "every 15 minutes"
command = "python ingest/fetch_users.py"

[job.sync_orders]
schedule = "every 1 hour"
command = "python ingest/sync_orders.py"
```

Then start the daemon:

```bash
fledge start
```

Fledge will read your config, schedule each job, and run them in the background. Logs are written to `fledge.log` by default.

To check the status of running jobs:

```bash
fledge status
```

To stop the daemon:

```bash
fledge stop
```

---

## Configuration

| Key | Description | Default |
|-----------|-------------------------------|-------------|
| `schedule` | How often the job runs | required |
| `command` | Shell command to execute | required |
| `timeout` | Max runtime in seconds | `300` |
| `retries` | Retry attempts on failure | `0` |

---

## License

MIT © 2024