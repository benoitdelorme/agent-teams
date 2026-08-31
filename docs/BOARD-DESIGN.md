# Task Board — conception

Un kanban web local, bindé en direct sur ce que font les agents. Lancé par `teams up`,
il devient la deuxième porte d'entrée des tickets (l'autre restant le terminal de gestion).
Statut : document de conception — rien n'est implémenté.

## 1. Le principe directeur : les fichiers restent la source de vérité

Aucune base de données, aucun état serveur. La vérité vit dans des fichiers markdown que
les agents savent déjà lire et écrire. Le serveur web n'est qu'une **vue + un stylo** sur
ces fichiers :

- **agents → UI** : un agent modifie un fichier ticket → le serveur détecte le changement
  (watch) → pousse un événement SSE → l'UI se met à jour.
- **UI → agents** : l'humain crée/déplace un ticket → le serveur écrit le fichier →
  et *réveille* gestion via `programa send` (le mécanisme de `teams msg`) uniquement
  quand ça compte (passage en TODO).

Cohérent avec la philosophie du repo : `bin/teams` est du Python stdlib pur ; le serveur
board le sera aussi.

## 2. Modèle de données : un fichier par ticket

`shared/PLAN.md` (une table unique) est mauvais pour l'édition concurrente : gestion et
l'UI écriraient la même table. On passe à **un fichier par ticket** :

```
shared/tasks/
  T1.md
  T2.md
  ...
  .counter          # prochain id (le serveur et gestion incrémentent atomiquement)
```

Format d'un ticket (`shared/tasks/T3.md`) :

```markdown
---
id: T3
title: Auth layer frontend
team: frontend            # ou "-" tant que non assigné
status: doing             # backlog | todo | doing | qa | done
blocked: false            # badge rouge, pas une colonne
created: 2026-08-31T15:20
updated: 2026-08-31T16:02
by: human                 # human | gestion
---

## Description
Contexte / but, écrit par l'humain (UI) ou gestion.

## Criteria
- `pnpm build` + `pnpm lint` green
- wrong creds shows error

## Log
- 16:02 gestion → frontend | TASK T3 | auth layer, see criteria
- 16:41 frontend → gestion | DONE T3 | lib/auth.tsx, pages/Login.tsx — build green
- 16:45 gestion: spot-check ok, moved to qa
```

- Le kanban = le champ `status` du frontmatter. Déplacer une carte = réécrire une ligne.
- **La trace vit dans `## Log`** : elle est alimentée automatiquement (voir §5) et
  manuellement par les agents (« detail lives in files » — c'est déjà le protocole).
- Écritures toujours atomiques (tmp + `os.rename`) des deux côtés.
- `shared/PLAN.md` garde le rôle « Goal / Contracts » de la feature courante, mais la
  table des tâches disparaît au profit de `shared/tasks/`. `plan_summary()` de
  `teams status` lit désormais le dossier.

### Statuts et sémantique

| statut  | qui le pose                  | sens |
|---------|------------------------------|------|
| backlog | humain (UI) ou gestion       | idées / non prêt. **Invisible pour gestion** (règle de prompt + le serveur ne notifie jamais dessus) |
| todo    | humain (drag) ou gestion     | prêt à dispatcher → gestion est réveillée |
| doing   | gestion au dispatch          | TASK envoyée à une team |
| qa      | gestion à la réception DONE  | à vérifier (spot-check worker / humain) |
| done    | gestion après vérification   | terminé |

`blocked: true` est un flag transversal (carte marquée rouge dans sa colonne), posé
quand un BLOCKED arrive — pas une sixième colonne.

## 3. Le serveur : `teams board` (Python stdlib, zéro dépendance)

Un seul fichier `bin/teams-board` (~400 lignes), ou une commande de `bin/teams` :

- **HTTP** : `http.server.ThreadingHTTPServer`, bind sur `127.0.0.1:0` → l'OS donne un
  port libre (rien à scanner). Port + pid écrits dans `.state/board.json`.
- **API** (JSON, minimale) :
  - `GET /api/tasks` — tous les tickets (frontmatter + corps rendu)
  - `POST /api/tasks` — créer (par défaut en backlog)
  - `PATCH /api/tasks/T3` — status / title / team / blocked
  - `POST /api/tasks/T3/comment` — l'humain ajoute une ligne au `## Log`
  - `GET /api/state` — roster + liveness (relit `.state/sessions/*.json`)
  - `GET /events` — **SSE** (un seul flux : `task-changed`, `state-changed`)
- **Watch** : poll des mtimes de `shared/tasks/` + `.state/sessions/` toutes les 500 ms
  (un `os.scandir` sur ~50 fichiers, coût nul, fiable sur macOS — pas besoin de FSEvents).
  Diff → événement SSE avec le ticket complet (l'UI patche, pas de re-fetch).
- **Réveil de gestion** : quand un ticket **entre en `todo` depuis l'UI**, le serveur
  exécute l'équivalent de `teams msg gestion` :
  `programa send --workspace … --surface … "NEW T7 | <title> — read shared/tasks/T7.md, plan and dispatch\n"`.
  C'est le seul push vers un agent. Tout le reste (doing/qa/done posés par gestion,
  logs), l'UI l'apprend par le watch. Un commentaire humain sur un ticket en cours peut
  optionnellement notifier gestion (`COMMENT T7 | see Log`), derrière un toggle dans l'UI.

### Cycle de vie

- `teams up` : lance le serveur en subprocess détaché, imprime
  `board → http://127.0.0.1:5173` dans le terminal qui a fait le up (+ dans LOG.md).
- `teams down` : tue le pid de `.state/board.json`.
- `teams board` : lancer/relancer seul (utile hors programa) ; `teams up --resume`
  relance s'il est mort.
- Serveur mort ≠ système cassé : les agents continuent, l'UI rattrape au redémarrage
  (tout est dans les fichiers).

## 4. Deux portes d'entrée, un seul chemin de données

1. **Web** : créer en backlog → affiner → drag vers TODO → le serveur écrit le fichier
   et réveille gestion → gestion lit `shared/tasks/T7.md`, assigne `team`, passe en
   `doing`, dispatche `TASK T7 | …`.
2. **Terminal** : l'humain parle à gestion comme aujourd'hui → gestion **crée elle-même
   les fichiers tickets** (son prompt remplace « écris la table PLAN.md » par « un
   fichier par tâche dans `shared/tasks/`, statuts backlog|todo|doing|qa|done ») → l'UI
   les voit apparaître en live via le watch.

Aucun des deux chemins ne parle à l'autre directement : les deux écrivent les mêmes
fichiers, le watch fait converger tout le monde. Pas de double vérité possible.

## 5. Traces automatiques : étendre le hook existant

Le hook `PreToolUse/SendMessage` de `bin/teams` loggue déjà chaque message inter-team
dans `LOG.md`. Extension : si le header du message matche `^\w+ (T\d+)` (TASK T3, DONE
T3, BLOCKED T3…), la même ligne est **aussi appendue au `## Log` du ticket**. Effets :

- chaque ticket porte l'historique complet de ses échanges **sans changer les prompts** ;
- `BLOCKED T3` pose `blocked: true` au passage ; `DONE T3` peut poser `status: qa`
  automatiquement (gestion confirme ensuite) — deux règles de hook, zéro token dépensé.

Les agents restent libres d'écrire des notes plus riches dans le corps du ticket
(résultat, chemins modifiés) — le protocole les y pousse déjà.

## 6. L'UI : une page, dark, sans framework

**Recommandation : pas de shadcn.** shadcn = React + Tailwind + node_modules + build,
pour 5 colonnes et une modale. Le repo est zéro-dépendance et le besoin est petit ;
un `board.html` unique (~600 lignes HTML/CSS/JS vanilla, servi par le serveur) donne le
même rendu haut de gamme, se charge en <50 ms, et n'introduit aucune chaîne de build.
(Option B si l'UI doit grossir : Vite + React + shadcn, `dist/` commité, servi statique —
même serveur, même API ; la frontière API/SSE rend le swap indolore.)

- **Thème** : dark only. Fond `#0e1013`, cartes `#16191d`, bordures `#23272d`, texte
  `#e6e8ea`, accents par team (frontend cyan, backend violet, gestion ambre), `blocked`
  rouge. Police `Inter, -apple-system, system-ui, sans-serif` (aucune serif), tailles
  13–15 px, densité type Linear.
- **Layout** : 5 colonnes (Backlog · TODO · En cours · Ready for QA · Done) en CSS grid,
  scroll vertical par colonne, compteur par colonne. Header : nom de la feature
  (PLAN.md), pastilles de liveness des teams (vert = working, gris = idle, rouge = dead —
  depuis `/api/state`), point de connexion SSE.
- **Carte** : `T7` + badge team + titre + horodatage de dernière activité + icône bloqué.
- **Drag & drop** : pointer events maison (~80 lignes, pas de lib). Optimiste : la carte
  bouge tout de suite, `PATCH` derrière, rollback si erreur. L'écho SSE de sa propre
  écriture est déduppliqué par `updated`.
- **Modale ticket** : frontmatter éditable (titre, team, blocked), description/criteria,
  et le `## Log` rendu en flux type chat qui **s'allonge en live** pendant que les agents
  travaillent. Zone commentaire humain en bas.
- **Création** : bouton `+` en Backlog, input inline (titre, Entrée = créé), détail dans
  la modale.
- **Live** : `EventSource` avec reconnexion auto ; à la reconnexion un `GET /api/tasks`
  resynchronise. Pas de websocket : SSE suffit (flux unidirectionnel serveur→UI, les
  écritures passent par l'API).

## 7. Ce qui change dans l'existant (petit)

| fichier | changement |
|---|---|
| `bin/teams` | `cmd_up`/`cmd_down`/`resume` : start/stop du board, print de l'URL ; hook : append au `## Log` du ticket + règles blocked/qa ; `plan_summary()` lit `shared/tasks/` |
| `bin/teams-board` | **nouveau** — serveur HTTP+SSE+watch (stdlib) |
| `board.html` (dans bin/ ou tools/board/) | **nouveau** — l'UI |
| `prompts/gestion.md` | tickets fichiers au lieu de la table PLAN.md ; « ignore status: backlog » ; poser doing/qa/done |
| `prompts/PROTOCOL.md` | `<ref>` pointe vers `shared/tasks/T<n>.md` ; une ligne sur les statuts |
| `.gitignore` | `shared/tasks/` (contenu runtime, comme LOG.md) |
| `teams.json` | optionnel : `board: {"port": 0, "open": false}` |

## 8. Coût, perf, risques

- **Coût tokens** : quasi nul. Le board ne parle jamais à un LLM ; l'unique interaction
  est une ligne `NEW T7 | …` tapée dans le terminal de gestion — le même coût qu'un
  message humain. Les traces automatiques passent par le hook (gratuit).
- **Perf** : poll de mtimes 2×/s sur un dossier local, SSE avec 1 client (ou 2-3 onglets),
  fichiers < 10 Ko. Rien à optimiser.
- **Risques & réponses** :
  - *Écriture concurrente sur un même ticket* (gestion édite pendant un drag) : rare
    (fichiers séparés par ticket), écritures atomiques, dernière écriture gagne sur le
    frontmatter, le `## Log` est append-only. Acceptable pour un outil mono-utilisateur.
  - *Gestion rate le réveil* (session occupée) : `programa send` tape dans le terminal,
    le message est traité au tour suivant — même garantie que `teams msg` aujourd'hui.
  - *Frontmatter cassé par un agent* : le serveur valide au parse ; ticket illisible →
    carte « ⚠ à réparer » dans l'UI plutôt que crash.

## 9. Ordre d'implémentation proposé

1. Modèle tickets : `shared/tasks/`, parseur/écrivain dans `bin/teams`, migration de
   `plan_summary`, prompt gestion. (Le système marche déjà mieux, sans UI.)
2. Serveur : API + watch + SSE + start/stop dans `up`/`down`.
3. UI : colonnes + cartes + drag + modale + live.
4. Boucle de réveil (`todo` → programa send) + traces auto dans le hook.
5. Finitions : liveness header, commentaires, badge blocked, reconnexion.
