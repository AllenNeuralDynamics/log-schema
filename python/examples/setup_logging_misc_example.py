import logging

from log_schema import DefaultFormatter, setup_logging


# Adding additional handlers
def setup_with_additional_handler():
    setup_logging()

    # Add an additional handler after setup
    additional_handler = logging.StreamHandler()

    # Need to add DefaultFormatter to new handler to ensure logs are formatted correctly
    #   formatter also takes in model field to load fields dynamically
    additional_handler.formatter = DefaultFormatter(model={"app_name": "test_app"})
    logging.getLogger().addHandler(additional_handler)

    logging.info("Two stream logs, one default, one with additional handler")


# Multiple custom fields defined precedence
def custom_field_behaviors():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "log_schema.DefaultFormatter",
                "static_fields": {
                    "field1": "from_config",
                    "field2": "will be overridden by model",
                    "field3": "will be overridden by extra",
                },
            },
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

    # Field2 and Field3 will be overridden with new values defined in model
    setup_logging(
        config=config,
        model={
            "field2": "from_model",
            "field3": "will be overridden by extra",
        },
    )

    # Field3 will be overridden by extra
    logging.info("Precedence", extra={"field3": "from_extra"})
    text = """
    Precedence order (extra has highest precedence): 
    1. extra
    2. model
    3. config
    """
    print(text)


def main():
    examples = {
        "Adding additional handlers": setup_with_additional_handler,
        "Multiple custom fields defined precedence": custom_field_behaviors,
    }

    for example_name, example_func in examples.items():
        print(f"\n{example_name} \n{'-' * len(example_name)}\n")
        example_func()


if __name__ == "__main__":
    main()
