import logging

from pydantic import BaseModel

from log_schema import setup_logging


class Person(BaseModel):
    user: str
    age: int
    ssn: str | None = None
    timestamp: str | None = None


if __name__ == "__main__":
    # User123 is born into the world at the ripe age of 30
    # ---------------------------------------------------------------
    user123 = Person(user="Doe", age=30)
    setup_logging(static_fields={"ssn": "123-45-6789"}, model=user123)
    logging.info("Test message")
    # {"timestamp": "2026-06-24T22:22:53.080092Z", "level": "INFO", "message": "Test message", "ssn": "123-45-6789"}

    # User123 has a birthday and is now 31
    # ---------------------------------------------------------------
    user123.age += 1
    logging.info(f"Happy Birthday, {user123.user}!")
    # {"timestamp": "2026-06-24T22:22:53.080730Z", "level": "INFO", "message": "Happy Birthday, Doe!", "ssn": "123-45-6789"}

    # Uh oh, User123 does unspeakable crimes and now must flee the country
    # ---------------------------------------------------------------
    user123.user = "Dee"
    user123.age = 38
    user123.ssn = "987-65-4321"  # cannot be changed, was defined as static field in setup_logging
    logging.info("Users new identity - unable to hack into ssn database")
    # {"timestamp": "2026-06-24T22:22:53.081333Z", "level": "INFO", "message": "Users new identity - unable to hack into ssn database", "ssn": "123-45-6789"}

    # User123 regrets everything. Tries to go back in time
    user123.timestamp = "2020-01-01T00:00:00Z"  # this is reserved attribute, cannot be changed
    logging.info("The laws of the universe forbid time travel, but User123 tries anyway")
    # {"timestamp": "2026-06-24T22:22:53.081933Z", "level": "INFO", "message": "The laws of the universe forbid time travel, but User123 tries anyway", "ssn": "123-45-6789"}

    # With the powers of "extra" anything can be changed
    # ---------------------------------------------------------------
    logging.info(
        "Super new identity",
        extra={"timestamp": 0, "user": "!^&@?@", "age": "?^?@!@#", "ssn": "!!!"},
    )
    # {"timestamp": 0, "level": "INFO", "message": "Super new identity", "ssn": "!!!", "user": "!^&@?@", "age": "?^?@!@#"}
