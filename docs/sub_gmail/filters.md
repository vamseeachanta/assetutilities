# Gmail filters and spam reduction

Use the [retention cleanup guide](cleanup.md) for elapsed-age cleanup and the
worked example. Incoming filters do not periodically revisit mail as it ages.

## Preserve wanted mail

Before changing filters, review **Settings → Filters and Blocked Addresses**
for existing rules that delete wanted mail. Star or mark important messages that
must be excluded from the cleanup command. A custom label alone does not grant
that protection. Gmail has no general filter action that guarantees retention
forever, and another matching filter can still move mail to Trash.

For a trusted category of incoming mail, search for the intended criteria first,
inspect the matches, then use **Create filter**. Choose an organizing label or
archive action as appropriate. Avoid broad deletion filters when preserving
important correspondence. Google documents the supported workflow in
[Create rules to filter your emails](https://support.google.com/mail/answer/6579?hl=en).
A reply is filtered only if it also matches the criteria.

## Reduce spam over time

Report unwanted suspicious messages using **Report spam**. Correct false positives
using **Not spam**. For legitimate recurring bulk mail that is no longer wanted,
use the unsubscribe action where available; block repeat unwanted senders when
appropriate. Review matches before creating sender or category filters. Google's
[Report spam in Gmail](https://support.google.com/mail/answer/1366858?hl=en)
explains these actions and how reporting informs future classification.

Avoid automatically trashing every message in Spam: it removes the opportunity
to inspect misclassified wanted messages. The cleanup policy applies the same
age threshold and starred/important protection checks to Spam as to other mail.
Messages already in Spam remain subject to Gmail's own retention behavior.
Spam elimination is not guaranteed; effectiveness requires delivery history and
a separately supplied acceptance target.

Sources were opened on 2026-10-20. No filter or mailbox is changed by this guide.
