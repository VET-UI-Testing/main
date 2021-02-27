# VET: Identifying and Avoiding UI Exploration Tarpits

## Accessing raw data

All our raw experimental data are available
[here](https://osf.io/8wsfz/?view_only=4896b40797ce4b1bb25c85efcc5aec56).

### Explanation of data format

Each Bzip2 tarball represents data for a single trace, with filenames in the forms of `{TOOL_NAME}-{APP_NAME}-{RUN_ID}.tar.bz2`. The `{RUN_ID}` is encoded in the following fashion:

- `1`, `2`, and `3`: the initial runs for each tool-app pair.
- `4`, `5`, and `6`: the comparison runs, using exactly the same settings as initial runs.
- `vXdY`: VET-enhanced runs by addressing top-`X` ranked regions on the respective tool-app pair. These regions are all from initial runs. `Y` is any of `1`, `2`, and `3`.

Within each trace the meanings of files are as follows:

- `./{TIMESTAMP}.json` represents the full UI hierarchy of each screen in the trace. Within each file:
  - Each JSON object is a UI element. Child elements are stored as JSON arrays in the `ch` field.
  - The UI element that the tool acts on is marked with `is_source: true`. Note that it is possible to act without involving any UI element (e.g., pressing Back on the device).
  - `act_id` denotes Activity ID.
  - `ua_type` denotes what kind of action triggers OURINFRA to record this step. The values have the following meanings:
    * 0: short click
    * 1: long click
    * 2: touch
    * 3: context click
    * 7: menu click
    * 100: back
  - `en`: whether the UI element is enabled.
  - `vclk`, `vlclk`, `vcclk`: class names of short click handlers, long click handlers, and context click handlers, respectively. If one field is not present for some object, the corresponding UI element does not respond to the corresponding event.
  - `bound`: UI element boundary.
  - `class`: Class name of the type of the UI element.
  - `ucls`: Unified class name, must be a superclass of `class`, either starts with `android.widget.` or is `android.webkit.WebView`. Might not exist in some cases.
  - `id`: Resolved resource ID in strings if the UI element has one.
  - `idn`: Resource ID in numbers, `-1` if the UI element does not have an associated resource ID.
  - `hash`: Internal unique representation of the object supporting the corresponding UI element in the app's internal UI data structures.
