# Logging Utility Library

This library utilizes [python's standard logging library](https://docs.python.org/3/library/logging.html) and [logging.config](https://docs.python.org/3/library/logging.config.html) to help setup logging. Use the command below to easily setup logging for a project.  

## Usage

The default setup for logging adheres to the best practice guidelines described [here](https://github.com/AllenNeuralDynamics/aind-log-utils/blob/main/README.md).

```python
import aind_log_utils
import logging

aind_log_utils.setup_logging()
logging.info("Hello")

# Output: {"timestamp": "2026-04-08T22:58:22.677137Z", "level": "INFO", "message": "Hello"}
```

The examples directory in this project contains additional examples on other features such as: 

- Setup logging from a config (logging.config) 
- Setup logging with dynamic fields 
- Adding additional handlers with correct format

## Implementation Notes

- If using a custom config file, the fields in ``model`` will overwrite the static_fields set in the config **ONLY IF** the formatters explicitly reference ``aind_log_utils.DefaultFormatter`` AND contains the same field key.
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