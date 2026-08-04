
# Telecom Analytics Platform - Architecture Documentation
*Documentation Version 1.0.0 | Last Updated: August 2026*

## Project Overview

A production-ready telecom analytics platform built with **ClickHouse** as the data warehouse. The system provides both a **CLI** for power users and a **REST API** for frontend applications and external systems. It handles synthetic network event data with realistic distributions and supports advanced analytics, partition management, and performance monitoring.

---

## System Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                             │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐     │
│  │   main.py (CLI)      │  │   app.py (FastAPI)               │     │
│  │   - Command line     │  │   - REST endpoints               │     │
│  │   - Interactive shell│  │   - Middleware & CORS            │     │
│  │   - User input       │  │   - Static files (dashboard)     │     │
│  └──────────────────────┘  └──────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API LAYER (api/)                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  routes/                                                     │   │
│  │  ├── events.py     → /api/events/*                           │   │
│  │  ├── analytics.py  → /api/analytics/*                        │   │
│  │  ├── partitions.py → /api/partitions/*                       │   │
│  │  └── health.py     → /health, /ready                         │   │
│  │                                                              │   │
│  │  models/response_models.py  → Pydantic models for responses  │   │
│  │  dependencies.py            → Dependency injection           │   │
│  │  exceptions.py              → Global error handlers          │   │
│  │  middleware.py              → Logging, timing, rate limit    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER (services/)                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  event_service.py       → Logic for events & users           │   │
│  │  analytics_service.py   → Reports & aggregations             │   │
│  │  partition_service.py   → Partition management               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 REPOSITORY LAYER (repositories/)                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  network_event_repository.py                                 │   │
│  │  - All database queries (CRUD, aggregations, filters)        │   │
│  │  - Raw data access                                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  DATABASE LAYER (database/)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  clickhouse_client.py                                        │   │
│  │  - Singleton pattern                                         │   │
│  │  - Connection management                                     │   │
│  │  - Query execution                                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CLICKHOUSE                                 │
│                   (Columnar Database)                               │
│  Table: network_events (partitioned by month)                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. API Request Flow

```
Client (Frontend / Postman / curl)
    │
    │  GET http://localhost:8000/api/events/count
    ▼
app.py (FastAPI)
    │  - Middleware: log_requests() → Request logging
    │  - Middleware: timing_middleware() → Response time measurement
    │  - RateLimitMiddleware → Rate limiting check
    ▼
api/routes/events.py
    │  - Extract parameters (limit, user_id, ...)
    │  - Call service.get_count()
    ▼
services/event_service.py
    │  - Fetch data from repository
    │  - Combine data (e.g., add statistics)
    ▼
repositories/network_event_repository.py
    │  - Build SQL query
    │  - Call client.query()
    ▼
database/clickhouse_client.py
    │  - Execute query on ClickHouse
    │  - Return result_rows
    ▼
Response flows back up:
    │  - Repository returns results to Service
    │  - Service returns processed data to Route
    │  - Route formats with ApiResponse
    ▼
Client receives JSON response
```

### 2. CLI Command Flow

```
User types command
    │  telecom> count
    ▼
main.py (ClickHouseCLI)
    │  - do_count() method called
    │  - Call repo.count()
    ▼
repositories/network_event_repository.py
    │  - Build query: SELECT count() FROM network_events
    │  - Call client.query()
    ▼
database/clickhouse_client.py
    │  - Execute query on ClickHouse
    │  - Return result_rows
    ▼
main.py
    │  - Receive result (e.g., 5,000,000)
    │  - Display with tabulate
    ▼
User sees result
    │  📊 Total events: 5,000,000
```

### 3. Data Generation Flow

```
Run generate_data.py
    ▼
Generate random weights
    │  - city_weights = generate_city_weights()
    │  - app_weights = generate_app_weights()
    │  - network_weights = generate_network_weights()
    ▼
Generate data in batches
    │  - generate_batch() → Creates 50,000 records
    │  - client.insert() → Insert into ClickHouse
    ▼
Repeat until TOTAL_RECORDS is complete
    ▼
Display final statistics
```

---

## Component Details

### Root Files

| File | Responsibility | Input From | Output To |
|------|----------------|------------|-----------|
| `main.py` | CLI entry point, command management | User terminal input | Commands to Repository & Analytics |
| `app.py` | API entry point, FastAPI configuration | HTTP requests | JSON responses to client |
| `generate_data.py` | Synthetic test data generation | Configuration (TOTAL_RECORDS, BATCH_SIZE) | Data in ClickHouse |
| `test_connection.py` | ClickHouse connection testing | Settings from config.py | Connection report to user |

### Core Layer (core/)

| File        | Responsibility                          | Input From            | Output To             |
| ----------- | --------------------------------------- | --------------------- | --------------------- |
| `config.py` | Central application settings management | Environment variables | Settings to all files |

### Database Layer (database/)

| File | Responsibility | Input From | Output To |
|------|----------------|------------|-----------|
| `clickhouse_client.py` | Singleton ClickHouse connection management | Settings from config.py | Client to Repository & Analytics |

### Repository Layer (repositories/)

| File | Responsibility | Input From | Output To |
|------|----------------|------------|-----------|
| `network_event_repository.py` | All database queries (CRUD, aggregations, filters) | Services & CLI | Raw data (tuples) to Services & CLI |

### Service Layer (services/)

| File | Responsibility | Input From | Output To |
|------|----------------|------------|-----------|
| `event_service.py` | Events and users business logic | Routes & CLI | Processed data to Routes |
| `analytics_service.py` | Reports and analytics | Routes | Analytical data to Routes |
| `partition_service.py` | Partition management | Routes | Partition status to Routes |

### API Layer (api/)

| File | Responsibility | Input From | Output To |
|------|----------------|------------|-----------|
| `routes/events.py` | Event endpoints | HTTP requests | JSON responses |
| `routes/analytics.py` | Analytics endpoints | HTTP requests | JSON responses |
| `routes/partitions.py` | Partition endpoints | HTTP requests | JSON responses |
| `routes/health.py` | Health endpoints | HTTP requests | System status |
| `models/response_models.py` | Pydantic response models | Code definition | JSON response structure |
| `dependencies.py` | Dependency injection | FastAPI | Services to Routes |
| `exceptions.py` | Global error handling | Errors from anywhere | JSON error responses |
| `middleware.py` | Middleware (logging, timing, rate limiting) | HTTP requests | Requests to Routes |

### Partition Manager Layer (partition_manager/)

| File | Responsibility | Input From | Output To |
|------|----------------|------------|-----------|
| `partition_manager.py` | Partition management for CLI | Commands from main.py | Operations on partitions |

### Analytics CLI Layer (analytics/)

| File | Responsibility | Input From | Output To |
|------|----------------|------------|-----------|
| `network_event_analytics.py` | Analytical queries for CLI | Commands from main.py | Analytical data (tuples) to CLI |

---

## File Dependencies

| Source File | Target File | What is passed? | What is received? |
|-------------|-------------|-----------------|-------------------|
| `app.py` | `api/routes/*` | HTTP request | JSON response |
| `api/routes/*` | `api/dependencies.py` | Request for service | Service instance |
| `api/dependencies.py` | `services/*` | - | Service instance |
| `services/*` | `repositories/*` | Data request | Raw data (tuples) |
| `repositories/*` | `database/clickhouse_client.py` | SQL query | result_rows |
| `main.py` | `repositories/*` | Data request | Raw data (tuples) |
| `main.py` | `analytics/*` | Analytics request | Analytical data (tuples) |
| `main.py` | `partition_manager/*` | Partition request | Operation status |
| `generate_data.py` | `database/clickhouse_client.py` | Generated data | - |
| `test_connection.py` | `database/clickhouse_client.py` | Connection test | Connection status |

---

## Key Features

### 1. Dual Interface
- **CLI**: 20+ commands for data exploration and management
- **REST API**: 15+ endpoints with automatic Swagger/OpenAPI documentation

### 2. Data Management
- **ClickHouse Integration**: Columnar database optimized for analytical queries
- **Monthly Partitioning**: Automatic partition management for performance
- **Batch Processing**: Efficient bulk data insertion (50,000 rows/batch)

### 3. Analytics & Reporting
- Application usage statistics
- Network quality reports (4G vs 5G comparison)
- Geographic analysis (city-level metrics)
- Device performance ranking
- Hourly and daily trends

### 4. Production-Ready Features
- Singleton database connection
- Rate limiting (100 requests/minute)
- Request logging and timing
- Global error handling
- Health check endpoints
- CORS support for frontend integration
- Environment-based configuration

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Database** | ClickHouse | 26.4+ |
| **API Framework** | FastAPI | 0.115.6+ |
| **Language** | Python | 3.10+ |
| **CLI** | Python cmd module | - |
| **Data Generation** | Faker | 30.8.0+ |
| **Container** | Docker | 27.5+ |

---

## API Endpoints

### Events
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events/count` | Total number of events |
| GET | `/api/events/sample` | Random event samples |
| GET | `/api/events/user/{user_id}` | Events for a specific user |
| POST | `/api/events/search` | Advanced search with custom queries |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/top-apps` | Most used applications |
| GET | `/api/analytics/network-quality` | Network performance report |
| GET | `/api/analytics/hourly-heatmap` | Hourly event distribution |
| GET | `/api/analytics/device-stats` | Device statistics |
| GET | `/api/analytics/city-stats` | City-level analytics |

### Partitions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/partitions/status` | Partition information |
| DELETE | `/api/partitions/{year_month}` | Drop a specific partition |
| POST | `/api/partitions/clean` | Clean partitions older than N months |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Detailed system health |
| GET | `/ready` | Readiness probe for load balancers |

---

## CLI Commands

### Basic Commands
| Command | Description |
|---------|-------------|
| `count` | Show total number of events |
| `sample [n]` | Show n sample events |
| `user <id>` | Show events for a user |
| `latest [n]` | Show n latest events |
| `info` | Show table information |

### Analytics Commands
| Command | Description |
|---------|-------------|
| `top_apps [n]` | Show top n applications |
| `top_cities [n]` | Show top n cities |
| `network_quality` | Show network quality report |
| `daily_report [n]` | Show daily report for last n days |
| `hourly_heatmap` | Show hourly event distribution |
| `device_stats` | Show device statistics |

### Partition Commands
| Command | Description |
|---------|-------------|
| `partition_status` | Show table and partition status |
| `partition_create` | Create a partitioned table |
| `partition_migrate` | Migrate data to partitioned table |
| `partition_replace` | Replace original with partitioned table |
| `partition_show` | Show partition information |
| `partition_drop <YYYYMM>` | Drop a specific partition |
| `partition_clean <months>` | Drop partitions older than N months |

### Utility Commands
| Command | Description |
|---------|-------------|
| `query <SQL>` | Execute custom SQL query |
| `clear` | Clear the screen |
| `exit/quit` | Exit the CLI |

---

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start ClickHouse (Linux)
sudo systemctl start clickhouse-server

# Run CLI
python main.py

# Run API
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
# Build the image
docker build -t telecom-analytics .

# Run with docker-compose
docker-compose up -d
```

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `CLICKHOUSE_HOST` | ClickHouse server host | `localhost` |
| `CLICKHOUSE_PORT` | ClickHouse server port | `8123` |
| `CLICKHOUSE_DATABASE` | Database name | `telecom_analytics` |
| `CLICKHOUSE_USERNAME` | Database username | `default` |
| `CLICKHOUSE_PASSWORD` | Database password | `` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `API_DEBUG` | Debug mode | `false` |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| **Data Generation Speed** | ~60,000 rows/second |
| **Batch Size** | 50,000 rows |
| **Query Response Time** | < 100ms for simple queries |
| **Partition Pruning** | Automatic partition selection |
| **Concurrent Requests** | Configurable rate limiting |

---

## Architecture Principles

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Testability**: Every layer can be tested independently
3. **Maintainability**: Changes in one layer don't affect others
4. **Reusability**: Services work for both CLI and API
5. **Flexibility**: Database, logic, and UI can be changed independently

---

## Future Enhancements

- [ ] Authentication and authorization (JWT)
- [ ] Redis-based rate limiting for distributed deployment
- [ ] Unit and integration tests
- [ ] Grafana dashboards for monitoring
- [ ] Data retention policies automation
- [ ] Materialized views for faster reports
- [ ] Support for multiple ClickHouse clusters


