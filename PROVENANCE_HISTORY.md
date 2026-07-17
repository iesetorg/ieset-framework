# Repository history and privacy migration

On 2026-07-17 the public repository history was rewritten to remove personal
filesystem paths, private operator briefs, internal control-plane artifacts, and
machine-specific author metadata. Project-account metadata replaced personal
or device-derived author identities. Commit author and committer timestamps were
preserved, but commit hashes changed.

This privacy migration has two methodological consequences:

1. Links to pre-migration commit hashes are obsolete.
2. A self-hosted git timestamp is not an independent registration authority.

`engine/preregistration_index.json` is regenerated from the current history and
drives the registration badge shown by the site. An audit performed during the
migration found historical spec/run pairs that entered git in the same commit.
Those IDs are frozen in `engine/preregistration_legacy_exceptions.json`, labelled
`legacy_same_commit`, and do not receive verified pre-registration credit. CI
rejects new same-commit pairs.

Going forward, prospective tests should also use an independent timestamp or
registry. Retrospective analyses of already-public data should be described as
registered analysis plans, not as proof that the analyst had never inspected
the data.
