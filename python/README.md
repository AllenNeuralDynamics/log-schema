# Log-Schema

Structured JSON logging for Python, built on the standard [`logging`](https://docs.python.org/3/library/logging.html) module, with optional [OpenTelemetry](https://opentelemetry.io/) support. 

## 📦 Install

There are several versions of the package based on what you're trying to provision logging with. 

```bash
uv add log-schema                # core
uv add "log-schema[otel]"        # + OpenTelemetry support
uv add "log-schema[cloudwatch]"  # + CloudWatch support
uv add "log-schema[all]"         # everything
```

## 🚀 Quick start

```python
import logging
import log_schema

log_schema.setup_logging(model={"software_name": "my-app"})
logging.info("Hello")
# {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello", "software_name": "my-app"}
```

🔭 With OpenTelemetry tracing:

```python
from opentelemetry import trace

log_schema.setup_logging_otel(resource={"service.name": "my-app"})
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("work"):
    logging.info("Hello")  # includes trace_id and span_id
```

## ✨ Features

- 🧾 JSON logs with ISO-8601 UTC timestamps
- 🏷️ Static fields on every record from a `dict` or pydantic model
- ⚙️ Bring your own `logging.config` dict or YAML file
- 🔗 OpenTelemetry tracing setup with trace/span IDs in logs
- ☁️ Optional OTLP log export (`otel_log_handler`) and CloudWatch defaults (`log_schema.cloudwatch`)

## 📚 Learn more

- 📖 Full documentation: _coming soon (mkdocs)_
- 🧪 Examples: [examples/](examples/)
