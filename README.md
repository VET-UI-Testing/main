# VET: Identifying and Avoiding UI Exploration Tarpits

## Accessing raw data

All our raw experimental data are available
[here](https://osf.io/8wsfz/?view_only=4896b40797ce4b1bb25c85efcc5aec56).

### Explanation of data format

Each Bzip2 tarball represents data for a single trace, with filenames in the forms of `{TOOL_NAME}-{APP_NAME}-{RUN_ID}.tar.bz2`. The `{RUN_ID}` is encoded in the following fashion:

- `1`, `2`, and `3`: the initial runs for each tool-app pair.
- `4`, `5`, and `6`: the comparison runs, using exactly the same settings as initial runs.
- `vXdY`: VET-enhanced runs by addressing top-`X` ranked regions on the respective tool-app pair. These regions are all from initial runs. `Y` is any of `1`, `2`, and `3`.
