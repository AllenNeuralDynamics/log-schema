from typing import Any


class ConfigBuilder:
    def get_invalid_config_file_content(self):
        return """im bad"""

    def get_config_file_content(self):
        return """
        version: 1
        disable_existing_loggers: False
        formatters:
            default:
                '()': aind_log_utils.main.DefaultFormatter
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

    def get_config_dict(self, has_default_format: bool, has_static_fields: bool):
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
        if has_default_format:
            config["formatters"]["default"]["()"] = "aind_log_utils.main.DefaultFormatter"
        if has_static_fields:
            config["formatters"]["default"]["static_fields"] = {
                "app_name": "my_app",
                "env": "production",
            }
        return config
