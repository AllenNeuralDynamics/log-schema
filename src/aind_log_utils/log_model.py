"""Public interface for the AIND log entry Pydantic model.

``_log_model`` is auto-generated from ``schema/logs.json`` via
``datamodel-codegen`` (see ``schema/schema.sh``).  Import from this
module — never directly from ``_log_model`` — so that downstream code
is insulated from regeneration churn.
"""

from aind_log_utils._log_model import AindLogEntry, Level

__all__ = ["AindLogEntry", "Level"]
