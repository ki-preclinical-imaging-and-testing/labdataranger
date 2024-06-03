# Lab Data Ranger

Lab Data Ranger is a tool for managing and surveying lab data using the context of file trees.

## Features

- Collect and manage file tree structures
- Extract and handle metadata for various file types
- Build graphs and load data into Neo4j for advanced queries

## Installation

```bash
pip install -r requirements.txt
```

## Configure database credentials

First copy the template database configuration file to a new file:

```bash
cp template_db_config.json db_config.json
```

The default in most functions and `.gitignore` is `db_config.json`, so that is recommended.

Then edit your new `db_config.json` in your editor of choice, updating for your own credentials.

Once this is set, you will no longer need to input your credentials in code.
