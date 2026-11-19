from typing import Any, Literal, Optional


class ConfigBuilder:
    def get_invalid_config_file_content(self):
        return """im bad"""

    def get_config_file_content(self):
        return """
        version: 1
        disable_existing_loggers: False
        formatters:
            default:
                '()': log_schema.DefaultFormatter
                static_fields:
                    i-am-from-yaml: hello
        handlers:
            console:
                class: logging.StreamHandler
                formatter: default
                level: INFO
                stream: ext://sys.stdout
        loggers:
            '':
                handlers: [console]
                level: INFO
                propagate: True
        """

    def get_config_dict(
        self,
        formatter: Optional[Literal["default", "console"]],
        has_static_fields: bool,
    ):
        """
        formatter: None for a plain logging formatter, "default" for DefaultFormatter (JSON),
            "console" for ConsoleFormatter (text).
        """
        config: dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": "INFO",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {  # Root logger
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": True,
                },
            },
        }
        if formatter == "default":
            config["formatters"]["default"]["()"] = "log_schema.DefaultFormatter"
        elif formatter == "console":
            config["formatters"]["default"]["()"] = "log_schema.ConsoleFormatter"
        if has_static_fields:
            config["formatters"]["default"]["static_fields"] = {
                "app_name": "my_app",
                "env": "production",
            }
        return config
