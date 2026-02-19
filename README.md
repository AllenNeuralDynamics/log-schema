# AIND Logging Standards

<!-- TODO: rewrite introduction -->

This repository outlines the **logging standards** for AIND, enabling logs that are *consistent*, *searchable*, and *impactful*. This document serves a guideline and includes topics such as best practices and observability integration.

<!-- TODO: rewrite TOC -->

[Standards](#-standards)

- [Structured Logs](#structured-logging)
- [Levels](#levels)
- [Fields/Labels](#fieldslabels)

[Best Practices](#-best-practices)

- [Meaningful Logs](#meaningful-logs)
- [Canonical Logs](#canonical-logs)
- [Don't log sensitive information](#dont-log-sensitive-information)
- [Don't rely on logs for monitoring](#dont-log-sensitive-information)

[Observability Integration](#-observability-integration)

- [How to get logs on Grafana](#how-to-get-logs-on-grafana)
- [How to get logs on SIPE Log Server](#how-to-get-logs-on-sipe-log-server)

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

# :star: Standards

### Structured Logging

Log messages should be structured in JSON format. If saving logs to a file, the logs should be structured as [**JSON Lines (JSONL)**](https://jsonlines.org/).

Example structured logs in a file: 

```json
{"timestamp": "2026-02-09T21:19:24.061270Z", "level": "INFO", "message": "Starting program"}
{"timestamp": "2026-02-09T21:19:24.061270Z", "level": "INFO", "message": "Connecting to database"}
{"timestamp": "2026-02-09T21:19:24.061774Z", "level": "INFO", "message": "Successfully retrieved data"}
{"timestamp": "2026-02-09T21:19:24.061774Z", "level": "INFO", "message": "Closing program"}
```

### Levels

Levels should be used to organize logs with different severity. The following leveling scheme is based on the python standard logging library. **When using levels in logs, the string should be used.**

The table below provides the string used for a level, the number value associated with that level, and a description of what events/scenarios should be associated with that level.

| Level String | Level Number | Description                                                    |
| ------------ | ------------ | -------------------------------------------------------------- |
| DEBUG        | 10           | Detailed information that is usually useful only to developers |
| INFO         | 20           | Significant business events                                    |
| WARNING      | 30           | Events that may indicate future problems                       |
| ERROR        | 40           | Errors that affect a **specific operation**                    |
| CRITICAL     | 50           | Errors that affect **entire program**                          |


### Fields/Labels

<!-- TODO: fill out missing info in table-->

At a minimum, projects should contain the following labels: timestamp, level, and message.

The table below contains a list of common fields/labels used in AIND projects. These fields are not mandatory to add to a log message, but when applicable, they should be used with the exact label name and the expected format. The table describes each field's format, purpose, and provides examples.

| Field/Label      | Required | Description                                                                                                                  | Format                         | Examples                                   |
| ---------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------ |
| timestamp        | ✓        | Time the log was created                                                                                                     | ISO8601 UTC                    |                                            |
| level            | ✓        | Log level                                                                                                                    | See [level standards](#levels) | DEBUG, INFO, WARNING, ERROR, CRITICAl      |
| message          | ✓        | String message about event                                                                                                   | String                         | "Error connecting to database... retrying" |
| lineno           |          | Source line number where log call was issued                                                                                 | Integer                        | 1, 20, 39                                  |
| process          |          | Process ID (from OS)                                                                                                         | String                         | 1231                                       |
| processName      |          | Process name                                                                                                                 | String                         | python.exe                                 |
| thread           |          | Thread ID (from OS)                                                                                                          | String                         | 12913                                      |
| threadName       |          | Thread name                                                                                                                  | String                         | python.exe                                 |
| hostname         |          | Hostname of the machine running software                                                                                     | String                         | w10dt700140                                |
| software_name    |          | The software generating the logs                                                                                             | String                         | waterlog, aind-data-schema                 |
| software_version |          | Version of the software generating the logs                                                                                  | String                         | 1.0.4.dev0                                 |
| instrument_id    |          | SIPE's naming convention for rigs/machines. Commonly found as an environment variable called ``aibs_comp_id`` on the machine | SIPE's rig naming convention   | frg_1_a, ephys_9_acq                       |
| acquisition_name |          | ?                                                                                                                            | String                         |                                            |
| subject_id       |          | ?                                                                                                                            | String                         |                                            |
| specimen_id      |          | ?                                                                                                                            | String                         |                                            |
| pipeline_name    |          | ?                                                                                                                            | String                         | codeocean pipeline, airflow DAG            |
| user_id          |          | User running software. Intended specifically for software which run experiments to indicate who is running the experiment    | String                         |                                            |


![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

# :pencil: Best Practices

In additional to following the standards above, it is recommended to adhere to these practices when implementing logs. 


Majority of the information in this section is based off of the following resources: 

- [Betterstack: logging best practices](https://betterstack.com/community/guides/logging/logging-best-practices/#2-do-use-log-levels-correctly)
- [Logging Discussion](https://github.com/AllenNeuralDynamics/SIPE-Admin/discussions/130)

### Meaningful Logs 

The utility of logs is directly tied to the quality of the information it provides. Ensure that log messages fully describe the situation happening and that there are ample labels/fields to give context about the log. 

Here is an example of a **poor** log message with not enough context

```
{"level": "INFO", "message": "Fail to save subject info"}
```

Here is the same example with a more informative message, and additional context about the log

```
{"level": "INFO", "message": "Fail to save subject info: field 'experiment_id' is missing", "subject_id": 714392}
```

### Canonical Logs

A canonical log line is a single log entry emitted at the **end of a request** that captures all essential information needed to understand what occurred, without requiring users to piece together multiple log messages.

Here is an example of two canonical logs:

```json
{
  "timestamp": "2026-02-09T21:19:24.061270Z",
  "level": "INFO",
  "message": "Session recorded",
  "subject_id": "713491",
  "instrument_id": "frg_1_a",
  "status": "success",
  "database": "dataverse",
  "user_id": "bobby.b",
  "wt_g": 23.93,
  "water_earned_ml": 0.89
}
{
  "timestamp": "2026-02-09T21:19:24.061270Z",
  "level": "ERROR",
  "message": "Failed to save session: could not connect to database",
  "subject_id": "713491",
  "instrument_id": "frg_1_a",
  "status": "fail",
  "database": "dataverse",
  "error_type": "TimeoutError",
  "user_id": "bobby.b",
  "wt_g": 17.21,
  "water_earned_ml": 1.2
}
```

These logs contain all the relevant information about a session where a mouse was fed water. Within this example program, there could've been individual logs about events such as adding a mouse, adding a user, feeding it water, connecting to the database etc. With the canonical log, debugging an error doesn't require looking at all these individual logs since a user can reference the summary provided in these logs. 

### Don't log sensitive information

Using hard-coded tokens or passwords in your program? Shame. Accidentally exposing that information because it was logged and ingested into a public observability platform? Double shame.

It is also recommended to redact fields if logging custom objects. Here is an example of a python implementation that properly redacts sensitive information: 


```python
from pydantic import BaseModel, SecretStr


class User(BaseModel):
    id: str
    email: str
    password: SecretStr
    inner_most_thoughts: SecretStr
```

### Don't rely on logs for monitoring 

Metrics generally provide continuous and efficient stream of data (think CPU usage over time). Logs aren't really designed to capture this type of data. 

Logs generally have high-cardinality to describe in detail about events, if metrics were recorded in these logs, queries would be slow since they would have to parse through other information. On large-scale systems logs may be sampled and or even by lossy under high load which is not great for metrics. 

If metrics are need there are tools like [**Telegraf**](https://www.influxdata.com/time-series-platform/telegraf/) which is designed to collect metrics, and [**InfluxDB**](https://www.influxdata.com/) which is used to store time-series data. Both these tools are also supported by Grafana.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)


# :telescope: Observability Integration

There are currently two major observability platforms in AIND that are used to monitor logs. Each with their own datastore setup that centrally stores all logs. 

1. [Grafana](https://grafana-sipe.corp.alleninstitute.org/) - Loki database
2. [SIPE Log Server](http://eng-logtools:8080/) - MySQL database

It is recommended to send the logs to Loki and to use Grafana as the primary observability tool for logging. This is the most current solution for centralize observability and will have the most support. 

The SIPE Log Server is the legacy observability platform and only handles viewing logs store in the MySQL database associated with it. These logs can also be viewed in Grafana. 

### How to get logs on Grafana

<!-- TODO: add upload to loki directly example-->
<!-- TODO: add upload to loki w/ grafana alloy example-->

To view logs on Grafana, logs must first be uploaded to Loki. There are two primary methods to get logs into Loki:

- Logs can be uploaded directly using the following API: http://eng-logtools:3100/loki/api/v1/push
- Logs can also be uploaded with an agent like [Grafana Alloy](https://grafana.com/docs/alloy/latest/). This [document](https://github.com/AllenNeuralDynamics/SIPE-Admin/wiki/Observability%3A-Alloy) outlines the details on how to setup alloy to send logs to AIND's Loki database. 

After the logs are stored in Loki, Grafana can be used to view the logs within the Loki database. This can be done by going to the "Explore" tab in Grafana and selecting Loki as teh datasource. If the tab is not visible, you may need additional permissions in Grafana.

### How to get logs on SIPE Log Server

Logs can be sent to the SIPE Log Server using this url: http://eng-logtools.corp.alleninstitute.org:9000

[Here](https://github.com/AllenNeuralDynamics/SIPE-Admin/blob/main/snippets/log.py) is a python example logging to the SIPE Log Server.


