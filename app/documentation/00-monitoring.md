# Monitoring

<a hx-get="/documentation/index.md"> <img height="20" src="/assets/chevron-left-duo.svg" width="20"/> Back </a> | <a 
hx-get="/documentation/index.md"> Index </a>

[TOC]

Since version 3.10.0, the app provides two endpoints for monitoring purposes.

## `Health` endpoint

The simple `/health` provides data on the system and its main dependencies.

```json
{
  "app_status": "running",
  "container_status": "<where the app is running i.e. inside or outside a container",
  "cpu": "CPU total consumption as a float (including other applications)",
  "memory": "RAM total consumption as a float (including other applications)",
  "os": "The os running the app",
  "pg_in_recovery": "Postgresql status as a boolean",
  "pg_connections": "Number of Postgresql connections on the app database",
  "redis_ping": "Redis response to ping command as a boolean"
}
```

## `Metrics` endpoint

The `/metrics` endpoint provides Prometheus scrapable data.

It is based on the `prometheus-fastapi-instrumentator` [see the github repo](https://github.com/trallnag/prometheus-fastapi-instrumentator)

The results look like this response:

```text
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 27871.0
python_gc_objects_collected_total{generation="1"} 7068.0
python_gc_objects_collected_total{generation="2"} 1325.0
# HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 416.0
python_gc_collections_total{generation="1"} 37.0
python_gc_collections_total{generation="2"} 3.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="12",patchlevel="4",version="3.12.4"} 1.0
# HELP http_requests_total Total number of requests by method, status and handler.
# TYPE http_requests_total counter
# HELP http_request_size_bytes Content length of incoming requests by handler. Only value of header is respected. Otherwise ignored. No percentile calculated. 
# TYPE http_request_size_bytes summary
# HELP http_response_size_bytes Content length of outgoing responses by handler. Only value of header is respected. Otherwise ignored. No percentile calculated. 
# TYPE http_response_size_bytes summary
# HELP http_request_duration_highr_seconds Latency with many buckets but no API specific labels. Made for more accurate percentile calculations. 
# TYPE http_request_duration_highr_seconds histogram
http_request_duration_highr_seconds_bucket{le="0.01"} 0.0
http_request_duration_highr_seconds_bucket{le="0.025"} 0.0
http_request_duration_highr_seconds_bucket{le="0.05"} 0.0
http_request_duration_highr_seconds_bucket{le="0.075"} 0.0
http_request_duration_highr_seconds_bucket{le="0.1"} 0.0
http_request_duration_highr_seconds_bucket{le="0.25"} 0.0
http_request_duration_highr_seconds_bucket{le="0.5"} 0.0
http_request_duration_highr_seconds_bucket{le="0.75"} 0.0
http_request_duration_highr_seconds_bucket{le="1.0"} 0.0
http_request_duration_highr_seconds_bucket{le="1.5"} 0.0
http_request_duration_highr_seconds_bucket{le="2.0"} 0.0
http_request_duration_highr_seconds_bucket{le="2.5"} 0.0
http_request_duration_highr_seconds_bucket{le="3.0"} 0.0
http_request_duration_highr_seconds_bucket{le="3.5"} 0.0
http_request_duration_highr_seconds_bucket{le="4.0"} 0.0
http_request_duration_highr_seconds_bucket{le="4.5"} 0.0
http_request_duration_highr_seconds_bucket{le="5.0"} 0.0
http_request_duration_highr_seconds_bucket{le="7.5"} 0.0
http_request_duration_highr_seconds_bucket{le="10.0"} 0.0
http_request_duration_highr_seconds_bucket{le="30.0"} 0.0
http_request_duration_highr_seconds_bucket{le="60.0"} 0.0
http_request_duration_highr_seconds_bucket{le="+Inf"} 0.0
http_request_duration_highr_seconds_count 0.0
http_request_duration_highr_seconds_sum 0.0
# HELP http_request_duration_highr_seconds_created Latency with many buckets but no API specific labels. Made for more accurate percentile calculations. 
# TYPE http_request_duration_highr_seconds_created gauge
http_request_duration_highr_seconds_created 1.7313306481360803e+09
# HELP http_request_duration_seconds Latency with only few buckets by handler. Made to be only used if aggregation by handler is important. 
# TYPE http_request_duration_seconds histogram
```
## Limitations

These endpoints are to be use externally. There is no security on accessing them.

The `/health` doesn't have a GUI counterpart.

The `/health` endpoint is quite slow and consumes Postgresql connection. It doesn't provide a `ready` and `live` status.