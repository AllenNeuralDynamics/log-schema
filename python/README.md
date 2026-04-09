# Logging Utility Library

This library utilizes [python's standard logging library](https://docs.python.org/3/library/logging.html) and [logging.config](https://docs.python.org/3/library/logging.config.html) to help setup logging. Use the command below to easily setup logging for a project.  

## Usage

### Basic Setup

The default setup for logging adheres to the best practice guidelines described [here](https://github.com/AllenNeuralDynamics/aind-log-utils/blob/main/README.md).

```python
import aind_log_utils
import logging

aind_log_utils.setup_logging()
logging.info("Hello")

# Output: {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello"}
```

### Setup Logging - Custom Configuration

The utility library provides a formatter called ``DefaultFormatter``. A custom config file can be used to setup logging with this formatter. It is recommended to use the ``aind_log_utils.DefaultFormatter`` to ensure logs adhere to the best practice guidelines. 

Example yaml:

```yaml
---
version: 1
disable_existing_loggers: false
formatters:
  default:
    "()": aind_log_utils.DefaultFormatter
    static_fields:
      software_name: SIPE-thingy-doo-dad
handlers:
  console:
    class: logging.StreamHandler
    formatter: default
    level: INFO
    stream: ext://sys.stdout
loggers:
  "":
    handlers:
      - console
    level: DEBUG 
```

Setup logging with custom yaml configuration

```python
import aind_log_utils
import logging

aind_log_utils.setup_logging(path_to_config="<path to config>")
logging.info("Hello")

# Output: {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello", "software_name": "SIPE-thingy-doo-dad"}
```

### Setup Logging - Dynamic Fields

``setup_logs`` has an optional field called ``models`` which allows users to add additional labels to the logs. It does so by adding the fields in models to the ``DefaultFormatter``.

```python
import aind_log_utils
import logging

aind_log_utils.setup_logging(models={"instrument_id": "1234"})
logging.info("Hello")

# Output: {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello", "instrument_id": "1234"}
```

It also works with custom config for setup. Example below uses same config file example as the one in [Setup Logging - Custom Configuration](#setup-logging---custom-configuration)

```python
import aind_log_utils
import logging

aind_log_utils.setup_logging(path_to_config="<path to config>", models={"instrument_id": "1234"})
logging.info("Hello")

# Output: {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello", "instrument_id": "1234", "software_name": "SIPE-thingy-doo-dad"}
```

### Setup Logging - Additional Handlers After Setup

```python
import aind_log_utils
import logging
import sys

aind_log_utils.setup_logging(models={"instrument_id": "1234"})
new_handler = logging.StreamHandler(sys.stdout)

# New formatter declared, if you want the same labels, MUST use the same model.
new_handler.setFormatter(DefaultFormatter(models={"subject_id": "614173"}))
logging.getLogger().addHandler(new_handler)

logging.info("Hello")

# There are two stream handlers, 
#  1) one with the original formatter with "instrument_id"
#  2) the other handler with the new formatter with "subject_id"

# Output: {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello", "subject_id": "614173"}
# Output: {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello", "instrument_id": "1234"}
```

## Implementation Notes

- If using a custom config file, the fields in ``model`` will overwrite the static_fields set in the config **ONLY IF** the formatters explicitly reference ``aind_log_utils.DefaultFormatter``.
- Each handler has its own formatter. Any additional handlers added to the root logger needs to redefine the formatter. This can easily be done by using the ``DefaultFormatter`` with the same ``model`` used for setup. Alternatively, you can make new models for different handlers.
    ```python
    new_handler.setFormatter(DefaultFormatter(models="<whatever model used for setup"))
    ```

## Local Development

```python
cd python
uv sync
uv run src/aind_log_utils/main.py
```