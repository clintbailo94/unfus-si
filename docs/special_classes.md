# Special domain classes in the workbook

The final workbook groups labels that should not be treated as ordinary
availability candidates on the **Reserved/Restricted/Invalid/Premium** sheet.
Include one row per non-`ok` label with these columns:

| Column | Value |
| --- | --- |
| `domain` | The label plus `.si` |
| `class` | `reserved`, `restricted`, `invalid_syntax`, or `premium` |
| `rule` | The stable rule ID returned by `si_domains.rules.explain(label)` |
| `source URL` | The source URL returned by `si_domains.rules.explain(label)` |

Reserved and restricted labels come only from their evidence-backed CSV files.
Invalid syntax is identified before RDAP. A premium row is included only when a
source-backed premium rule exists. An `ok` classification means “passes known
rules”; it does not mean the name is available. RDAP is not queried for any
non-`ok` classification, and its classification is kept in the evidence row.
