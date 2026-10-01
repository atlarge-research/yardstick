# Recorded `ubi` CLI output

Samples of what the real Ubicloud CLI prints, kept so the fake `ubi` in
`tests/test_ubicloud.py` can be pinned against them.

Why they exist: the parser in `Ubicloud._show` used to split each line on a
tab, and the fake CLI in the tests printed tab-separated lines too. The two
agreed with each other and not with the CLI, so the test suite stayed green
while `_wait_until_running()` never once saw a VM reach `running` (commit
`8651c57`). A fake that encodes the same assumption as the code under test
proves nothing; these files are the third opinion.

| File | Command |
| --- | --- |
| `vm_show_running.txt` | `ubi vm <location>/<name> show -f id,ip4,ip6,state` on a VM that finished booting |
| `vm_show_creating.txt` | the same command moments after `ubi vm ... create`, while the VM has no IPv4 address yet |

**Provenance.** Captured during the session that fixed `8651c57`, from a VM
created in `eu-central-h1`. The *format* is verbatim: one `key: value` line
per requested field, in the order the fields were requested, and a field
with no value printed as a bare `key:` with nothing after the colon. The
*values* are redacted -- the VM id is a made-up UBID and the addresses are
from the documentation ranges (`203.0.113.0/24`, `2001:db8::/32`) -- since
nothing here should look like a real machine somebody could try to reach.
`ip6` deliberately keeps a colon-bearing value: the parser has to split on
the *first* colon only.

**Re-recording.** With `UBI_TOKEN` set and a VM of your own:

    ubi vm eu-central-h1/<your-vm> show -f id,ip4,ip6,state

Paste the output here, redact the id and addresses as above, and run
`uv run pytest tests/test_ubicloud.py`. If the format has changed, those
tests fail -- which is the point: update `Ubicloud._show` and the fake CLI
together, never one without the other.
