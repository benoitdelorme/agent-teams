# SCR-002 — Ticket

A ticket in full, on its own page — not in a dialog. A ticket is the unit of work this
whole product exists to move; it gets a page.

**Composes:** field (`prose` and `compact`), chip, action, log-line, badge, toast.

```
┌────────────────────────────────────────────────────────────────────┐
│ ← Board                                              Doing ▾  ●    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   T7   Sujet du ticket, éditable en place                          │  ← hero
│        ─────────────────────────────────────────                   │
│                                                                    │
│   ┌───────────────────────────────────┬──────────────────────────┐ │
│   │ Description                       │ Team      [ backend  ▾ ] │ │
│   │ ╭───────────────────────────────╮ │ Jira      [ LUM-482   ] │ │
│   │ │ grande zone, grandit toute    │ │ Bloqué    ( ○ )          │ │
│   │ │ seule avec le contenu         │ │                          │ │
│   │ ╰───────────────────────────────╯ │ Créé      il y a 2 h     │ │
│   │ Critères de vérification          │ Modifié   à l'instant    │ │
│   │ ╭───────────────────────────────╮ │ Par       vous           │ │
│   │ ╰───────────────────────────────╯ │ shared/tasks/T7.md       │ │
│   │ Journal                           │                          │ │
│   │ ╭───────────────────────────────╮ │ [Supprimer le ticket]    │ │
│   │ │ 18:31 TASK T7 | …             │ │                          │ │
│   │ ╰───────────────────────────────╯ │                          │ │
│   │ [note…………] (notifier) [Ajouter]  │                          │ │
│   └───────────────────────────────────┴──────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

**The hero.** The ordinal in mono at `--t-id` beside the title at `--t-hero`, editable
in place with no visible box until approach. This is the one loud element on the
screen; everything below it is quiet. The pairing reads as a work order, which is what
a ticket is here.

**The content column** is 72ch at most and left-aligned. Description is a `prose` field
with a 6-line floor that grows without a scrollbar of its own — the page scrolls, the
field does not. Criteria sits directly beneath it because the two are read together:
what to do, and how we will know it was done.

**The sidebar** is 268px, sticky, and holds only what is *set* rather than *written*:
team, Jira, blocked, and the read-only facts. Status is not here — it is in the top bar,
because it is the ticket's state and the first thing you look for on arrival.

**Meta** is a two-column list, one fact per row, label then value. Not a run of values
joined by separators.

**Routing.** The page is at `#T7`, so it is linkable and the browser's back button
returns to the board. `Esc` returns too. A remote update never steals the field under
the cursor.

**Motion.** The board→ticket swap is the product's single orchestrated moment: the page
rises 8px and fades in over `--enter`. Nothing else on the screen animates on load.
