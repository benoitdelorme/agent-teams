# README illustration sources

The [README](../README.md) uses three original illustrations created with the built-in ImageGen tool. The assets are stored locally in [images/](images/) and require no external image host.

All finished illustrations use English labels, an ivory background and a consistent rust, blue and teal palette. The diagrams explain the configured hierarchy, ticket lifecycle and shared-file architecture; they are conceptual illustrations, not screenshots of running sessions.

## Final ImageGen prompts

The following are the exact final prompts applied to the corresponding diagram drafts. Keep technical labels and arrow directions aligned with the implementation when updating an illustration.

### Team hierarchy

Asset: [images/team-hierarchy.png](images/team-hierarchy.png).

Use case: text-localization.
Edit target: the provided agent-teams hierarchy infographic.
Primary request: translate EVERY piece of visible French text into English, preserving the polished composition, hierarchy, typography, ivory/rust/cobalt/teal palette, cards, connectors, alignment, and exact technical relationships. There must be NO FRENCH remaining.
Use exactly these replacement labels:
Top eyebrow stays "AGENT-TEAMS / 01".
Headline: "One goal. Coordinated teams."
Top card: "You"; subtitle "Goals · Priorities · Decisions".
Management card: "Management"; subtitle "Plan · Delegate · Verify".
Side optional worker card: "Analysis workers"; subtitle "Research · Planning · Review".
Backend card: "Backend"; subtitle "API · Data · Logic".
Frontend card: "Frontend"; subtitle "Interface · Flows · Integration".
Horizontal arrow: "API contracts".
Bottom blue card: "Backend workers"; subtitle "Implement · Test".
Bottom teal card: "Frontend workers"; subtitle "Implement · Test".
Footer, two neatly spaced lines instead of the single French line:
"Leads coordinate. Workers execute on demand."
"Default setup shown. Add teams to fit your project."
Resize text or make modest spacing adjustments if required for English, keep all text legible at 900px display width and inside margins. No added roles, permanent workers, logos, gradients or code. The only requested changes are localization and the second footer line explaining extensibility.

### Ticket lifecycle

Asset: [images/ticket-lifecycle.png](images/ticket-lifecycle.png).

Use case: text-localization.
Edit target: the supplied five-stage agent-teams ticket lifecycle infographic.
Translate ALL visible French into English. Preserve composition, ivory/rust/cobalt/teal palette, number sequence, pictograms, exact connector directions and layout. There must be NO French anywhere.
Exact final text:
Eyebrow "AGENT-TEAMS / 02".
Headline "From request to verified result."
Stage 1 "Backlog" with subtitle "You prepare".
Stage 2 "TODO" with subtitle "Ready to assign".
Stage 3 "In progress" with subtitle "Team delivers".
Stage 4 "Ready for QA" with subtitle "Manager checks".
Stage 5 "Done" with subtitle "Result accepted".
Forward arrow labels from left to right "Your decision", "TASK", "DONE", "Validation".
Return arrow from stage 4 to stage 3: "Needs changes".
Amber flag note: "Blocked is a ticket flag, not a column."
Footer: "DONE starts review. Management verifies before closing."
Keep exact five-stage workflow and one return arrow. Fit text cleanly within cards and margins, no overlap. Large typography legible at 900px width. No additional labels, roles or logo.

### Shared state

Asset: [images/shared-state.png](images/shared-state.png).

Use case: text-localization.
Edit target: the supplied agent-teams shared-ticket infographic.
Translate ALL visible French into English. Preserve layout, ivory/rust/cobalt/teal palette, pictograms, bidirectional connectors, card hierarchy and design. There must be NO French anywhere.
Exact final text:
Eyebrow "AGENT-TEAMS / 03".
Headline "One ticket. One shared state."
Left card heading "Board", footer "Create · Prioritize · Comment".
Center heading "Shared tickets"; three lines "Goals & criteria", "Team & status", "History & verification".
Right card heading "Teams", footer "Read · Build · Report".
Both bidirectional connectors labelled "Read / write".
Small left document card "API contracts"; subtitle "Agreed interfaces".
Small right document card "Shared log"; subtitle "Inter-team events".
Label under the small document cards: "Supporting shared documents".
Main footer: "The board and agents use the same files."
Keep all relationships and line directions. Adjust font size only as necessary so the center heading fits on one line and all English text fits cleanly within margins. No other changes, extra roles, cloud, or logos.

