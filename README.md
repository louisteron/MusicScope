# MusicScope

MusicScope transforme un Raspberry Pi (ou un ordinateur) en visualiseur musical
temps réel. La V0.1 ouvre une fenêtre OpenGL, capture l'entrée audio et affiche
un fond dont l'intensité réagit au niveau sonore.

## Démarrage

Python 3.13 est requis.

```bash
uv sync --group dev
uv run musicscope
```

Le mode silencieux, utile sans entrée audio ou pour les démonstrations, est
disponible avec `musicscope --no-audio`.

## Audio système macOS

MusicScope ne capture pas le microphone. Pour visualiser l'audio des
applications en temps réel sur macOS, installe un périphérique virtuel de
boucle tel que [BlackHole](https://existential.audio/blackhole/), puis configure
dans **Configuration Audio et MIDI** un périphérique de sortie multiple qui
inclut tes haut-parleurs et BlackHole. MusicScope détecte automatiquement
BlackHole ; sinon précise son nom :

```bash
musicscope --audio-device "BlackHole 2ch"
```

## Logos réactifs

Les logos, un CD et un vinyle détourés sont fournis et se déforment avec la musique. Sélectionne
celui à afficher au lancement :

```bash
musicscope --logo frog
musicscope --logo jvb
musicscope --logo ram
musicscope --logo cd
musicscope --logo vinyl
```

Pendant l'exécution, appuie sur `Espace` ou `→` pour sélectionner le visuel suivant,
ou sur `←` pour revenir au précédent.

Appuie sur `M` (ou `F1`) pour ouvrir le menu **OSCILLATION**. Sur certains
claviers AZERTY macOS, la touche physique `M` est également prise en charge.
Utilise `↑` et `↓` pour sélectionner l'amplitude, l'épaisseur, la réactivité
ou le mode couleur, puis `←` et `→` pour modifier la valeur en temps réel.
Appuie de nouveau sur `M` pour le fermer.

Les modes couleur sont :

- `NEON GREEN` : le rendu oscilloscope vert classique.
- `COVER NEON` : seuls les traits de la cover reprennent ses couleurs d'origine,
  tout en conservant l'effet néon.
- `COVER THEME` : la couleur dominante de la cover colore l'oscillation, la
  grille CRT, les informations du morceau et les contours de la cover.

## Développement

```bash
uv run ruff check .
uv run pytest
```

L'application est découpée par responsabilité : `core` orchestre le cycle de
vie, `audio` produit les analyses, `scene` stocke l'état visuel, `graphics` et
`renderer` dessinent, `window` encapsule GLFW, et `config`/`utils` fournissent
les services transverses.

## Reconnaissance musicale avec AudD

MusicScope peut identifier la musique jouée par la sortie système via
[AudD](https://audd.io/), puis récupérer et mettre en cache la pochette associée.

1. Crée un compte dans le [tableau de bord AudD](https://dashboard.audd.io/) et
   récupère ton jeton API.
2. Copie `.env.example` vers `.env` à la racine du projet.
3. Renseigne la valeur :

   ```env
   MUSICSCOPE_AUDD_API_TOKEN=ton_jeton_audd
   ```

4. Lance MusicScope normalement :

   ```bash
   musicscope --audio-device "BlackHole 2ch"
   ```

Au démarrage, `✓ AudD provider loaded` confirme l'activation. Sans jeton,
MusicScope affiche `⚠ AudD disabled (missing API token)` et le visualiseur
continue sans reconnaissance. ACRCloud reste présent dans le code comme ancien
fournisseur, mais n'est plus configuré ni utilisé.
