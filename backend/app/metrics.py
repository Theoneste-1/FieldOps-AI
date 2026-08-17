from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
inspection_submission_total = Counter(
    "inspection_submission_total",
    "Inspections submitted",
    ["risk_level"],
)
ai_requests_total = Counter("ai_requests_total", "AI analysis requests", ["status"])
ai_request_failures = Counter("ai_request_failures", "AI analysis failures", ["reason"])
ai_request_latency = Histogram(
    "ai_request_latency_seconds",
    "Gemini / analyzer latency",
    buckets=(0.2, 0.5, 1, 2, 5, 10, 20, 40),
)
sync_failures = Counter("sync_failures", "Synchronization failures", ["reason"])
database_query_latency = Histogram(
    "database_query_latency_seconds",
    "Selected database operation latency",
    ["operation"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2),
)
risk_calculations_total = Counter("risk_calculations_total", "Risk engine invocations", ["level"])
work_orders_created_total = Counter("work_orders_created_total", "Work orders created", ["priority"])
critical_notifications_total = Counter("critical_notifications_total", "Critical-risk notifications emitted")


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
