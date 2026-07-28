باشه جواد جان! کوتاه و مختصر:

---

# 📚 ClickHouse Telecom Analytics - CLI Commands

## Getting Started
```bash
python main.py
```

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `help <command>` | Show command details |
| `count` | Total number of events |
| `sample [n]` | Show n random events (default: 5) |
| `latest [n]` | Show n latest events (default: 10) |
| `user <id>` | Show user events & stats |
| `info` | Show table information |
| `top_apps [n]` | Top n applications by usage (default: 10) |
| `top_cities [n]` | Top n cities by traffic (default: 10) |
| `network_quality` | Network quality report by type |
| `daily_report [n]` | Daily report for last n days (default: 7) |
| `hourly_heatmap` | Hourly event distribution |
| `device_stats` | Device statistics |
| `query <SQL>` | Execute custom SQL query |
| `clear` | Clear screen |
| `exit` / `quit` | Exit CLI |

---

## 🎯 Quick Examples

```bash
# Basic
telecom> count
telecom> sample 3
telecom> user 123456

# Analytics
telecom> top_apps 5
telecom> network_quality
telecom> daily_report 3

# Custom SQL
telecom> query SELECT count() FROM network_events
telecom> query SELECT city, count() FROM network_events GROUP BY city

# Exit
telecom> exit
```

---

## 🛑 Exit

```bash
telecom> exit
# or
telecom> quit
```

---
