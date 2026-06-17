# Log Schema

A small utility library to help setup structured logs. It's built on top of the [python's standard logging library](https://docs.python.org/3/library/logging.html) and [logging.config](https://docs.python.org/3/library/logging.config.html). 

This library contains one main function ``setup_logging`` that handles setting up logs.

```python
import log_schema
import logging

log_schema.setup_logging()

logging.info("Hello")
# {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello"}
```

### Features
 
- ➕ Logs adhere to AIND logging standards
- ➕ JSON-formatted logs
- ➕ Logs written to the console by default
- ➕ ISO 8601 timestamps
- ➕ Default fields: `timestamp`, `level`, and `message`
- ➕ Add custom fields via a dict or a pydantic model (with validation and dynamic fields)
- ➕ Add handlers and other behavior through standard `logging.config` files

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

# Table of Contents

- [Log Schema](#log-schema)
    - [Features](#features)
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [`setup_logging`](#setup_logging)
  - [Parameters](#parameters)
- [Examples](#examples)
  - [Basic Setup](#basic-setup)
  - [Setting Log Fields](#setting-log-fields)
  - [Setting Handlers](#setting-handlers)
- [Implementation Notes](#implementation-notes)

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

# Installation

```
uv add log-schema
```

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

# `setup_logging`

Configures logging for a model, using either an inline config dict or a path to a config file.

```python
setup_logging(model, path_to_config=None, config=None)
```

## Parameters

| Name             | Type                | Required | Description                                                                                               |
| ---------------- | ------------------- | -------- | --------------------------------------------------------------------------------------------------------- |
| `model`          | `BaseModel \| dict` | No       | Model that represents fields in a log. These fields will be applied to all logs using the main formatter. |
| `path_to_config` | `str`               | No       | Path to a logging configuration file (e.g. YAML/JSON).                                                    |
| `config`         | `dict`              | No       | Logging configuration as a dict. Takes precedence over `path_to_config` if both are provided.             |

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

# Examples

- Basic setup
- Log content: Adding additional fields to logs
- Log destination: Adding additional handlers

## Basic Setup

In the software you want to provision with logging, add the following: 

```python
import log_schema
import logging

log_schema.setup_logging()

logging.info("Hello")
# {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello"}
```

This adds the following to your project: 

- ➕ JSON formatted logs
- ➕ logs write to console
- ➕ ISO 8601 timestamp 
- ➕ timestamp, level, and message fields (default fields)

## Setting Log Fields

To add additional fields to logs, use the ``model`` parameter in ``setup_logging``. The ``model`` parameter can accept the following: 
- **dictionary** of key-value pairs to make into log fields
- **pydantic model** of fields to add to logs. **This is the recommended method to use when adding additional fields**.

The example below demonstrates adding fields with a pydantic model. **This is the recommended method as it provides validation and dynamic field generation.** A pydantic model provides the following feature:

- validation on the fields
- ability to generate fields dynamically with ``default_factory``

```python
import log_schema
import logging

from pydantic import BaseModel

class ExampleLogFields(BaseModel):
    software_name: str
    software_version: str
    user_id: int
    dynamic: str = Field(default_factory=lambda: "wow")


log_schema.setup_logging(model=ExampleLogFields(
    software_name="software_a",
    software_version="0.1.0",
    user_id=123
))

logging.info("Hello")
# {"timestamp": "2026-06-17T15:22:46.835898Z", "level": "INFO", "message": "Hello", "software_name": "software_a", "software_version": "0.1.0", "user_id": 123, "dynamic": "wow"}
```

This adds the following: 

- ➕ Static fields
- ➕ Dynamic fields
- ➕ Validation
- ➕ Reusability

<!-- TODO: add section about where models should be save (once that is figured out) -->

> **NOTE:** If using ``extra`` (from std logging library) to add additional fields, this will have highest precedence compared to the additional fields set by ``setup_logging`` 
> 
> Example:
> ```python
> import log_schema
> import logging
>
> log_schema.setup_logging(model={
>     "example": "foo",
> })
>
> logging.info("Hello", extra={"example": "bar"})
> # {"timestamp": "2026-06-17T15:35:48.973790Z", "level": "INFO", "message": "Hello", "example": "bar"}
> ```

## Setting Handlers 

``setup_logging`` utilizes [logging.config](https://docs.python.org/3/library/logging.config.html) to help configure logging. With ``log-schema``, logging.config is primarily used to add additional handlers, but it  can also do other things such as (set static fields, formatters, etc).

Here is an example of adding additional handlers with a config file.

Config file:
```yaml 
# logging.yml
---
version: 1
disable_existing_loggers: false
formatters:
  default:
    "()": log_schema.main.DefaultFormatter

handlers:
  console:
    class: logging.StreamHandler
    formatter: default
    level: INFO
    stream: ext://sys.stdout
  file:
    class: logging.FileHandler
    formatter: default
    level: INFO
    filename: example.log

loggers:
  "":
    handlers:
      - console
      - file 
    level: INFO
    propagate: true
```

Code example:

```python
import log_schema
import logging

log_schema.setup_logging(path_to_config="configs/logging.yml")

logging.info("Hello")
# Outputs to console and example.log
# {"timestamp": "2026-06-17T15:35:48.973790Z", "level": "INFO", "message": "Hello"}
```

Using configs provides the following:

- ➕ Ability to add additional handlers
- ➕ Reusability
- ➕ logging.config features

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

# Implementation Notes

- If using a custom config file, the fields in ``model`` will overwrite the static_fields set in the config **ONLY IF** the formatters explicitly reference ``log_schema.DefaultFormatter`` AND contains the same field key.
- Each handler has its own formatter. Any additional handlers added to the root logger needs to have the ``DefaultFormatter`` added to it. This can easily be done by using the ``DefaultFormatter`` class, and passing in the same ``model`` used for setup. Alternatively, you can make new models for different handlers.

    ```python
    new_handler.setFormatter(DefaultFormatter(model="<whatever model used for setup"))
    ```
