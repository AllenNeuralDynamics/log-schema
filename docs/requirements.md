# Requirements

Logging minimum requirements

- Configurable schema of fields that are part of each log message
- Configurable severity (levels) for log messages
- Configurable log locations (file, console, log server, Loki)
- Log message format should be in JSON
- Time format: ISO 8601

Additional features

- Dynamic fields (scope = log message): [example here](#dynamic-field-log-message-scope)
- Dynamic fields (scope = logger): [example here](#dynamic-field-logger-scope)

# aind-log-utils?

Depending on the logging package chosen (stdlib logging vs loguru), the minimum requirements for logging can be fulfilled without the need of a helper library. 

- Loguru: with the ``loguru-config`` all the requirements are met
- stdlib: need a helper function to format into JSON 

To integrate the additional features some sort of helper function needs to be provided, this is what ``aind-log-utils`` will be. An unopinionated library that utilizes configuration files to help setup logging.

# Examples

## Dynamic Field (Log Message Scope)

Below is an example of a dynamic field. The field is statically set from a config file and it's value can be seen in the first log call. 

On the second log call, the field is dynamically updated.

```python
logging.info("Test message")
# [2026-01-22 07:29:35,613] w10dt700123 | Mouse: 614173 | INFO: Test message

logging.info("Test message", extra={"mouse_id": "999999"})
# [2026-01-22 07:29:35,613] w10dt700123 | Mouse: 999999 | INFO: Test message
```

## Dynamic Field (Logger Scope)

Below is an example of a dynamic field where the field is dynamically set for the logger. 

The config file provides us with a static default value for our fields. 

The ``setup_logging`` function, which is part of the ``aind-log-util`` library, contains additional code logic and attempts to update the static fields defined in the yaml file. In the preceding log call, the mosue field has been updated to a new value. 

```yaml 
# yaml file
version: 1
disable_existing_loggers: False

.log_structure: &log_structure
hostname: "w10dt700123"
mouse_id: "614173"

formatters:

logfile_format:
    "()": "main.JSONFormatter"
    # STRUCTURE
    <<: *log_structure
```

```python
from aind_log_util import setup_logging

# setup logging tries to auto-populate our static fields defined in the yaml
setup_logging("logging-config.yml") 

logging.info("dynamic field - logger scope")
# [2026-01-22 07:29:35,613] w10dt700123 | Mouse: 100000 | INFO: dynamic field - logger scope
```