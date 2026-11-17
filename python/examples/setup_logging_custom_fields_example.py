import logging

from pydantic import BaseModel

from log_schema import setup_logging


# Custom fields from dictionary
def setup_with_custom_fields_from_dict():
    setup_logging(model={"custom_field": "from_dictionary"})

    logging.info("Field defined from dictionary")


# Custom fields from pydantic BaseModel
def setup_with_custom_fields_from_basemodel():
    """
    This example shows adding logging labels through the use of a pydantic BaseModel. The fields
    defined in the BaseModel will be added as static fields to the log formatter.

    By default, it will ignore empty (None) fields in the BaseModel.
    """

    class CustomModel(BaseModel):
        custom_field: str = "from_basemodel"

    setup_logging(model=CustomModel())

    logging.info("Field defined from pydantic model")


# Custom fields from provided log_schema.defaults model
def setup_with_custom_fields_from_provided_models():
    """
    This example shows adding logging labels using a provided model from the log_schema.defaults module.
    """
    from log_schema.defaults import AINDLogFields

    setup_logging(
        model=AINDLogFields(
            software_name="test_software",
            software_version="1.0.0",
        )
    )
    logging.info("Field defined from provided model")


# Custom fields from extras
def setup_with_custom_fields_from_extras():
    """
    This example uses a dictionary to add additional logging labels.
    """
    setup_logging()
    logging.info("Field defined from extras", extra={"custom_field": "from_extras"})


# Custom fields from logging config
def setup_with_custom_fields_from_logging_config():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "log_schema.DefaultFormatter",
                "static_fields": {"custom_field": "from_config"},
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

    setup_logging(config=config)
    logging.info("Field defined from logging config")


def main():
    examples = {
        "Custom fields from dictionary": setup_with_custom_fields_from_dict,
        "Custom fields from pydantic BaseModel": setup_with_custom_fields_from_basemodel,
        "Custom fields from provided log_schema.defaults model": setup_with_custom_fields_from_provided_models,
        "Custom fields from extras": setup_with_custom_fields_from_extras,
        "Custom fields from logging config": setup_with_custom_fields_from_logging_config,
    }

    for example_name, example_func in examples.items():
        print(f"\n{example_name} \n{'-' * len(example_name)}\n")
        example_func()


if __name__ == "__main__":
    main()
