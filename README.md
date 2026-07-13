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

## Développement

```bash
uv run ruff check .
uv run pytest
```

L'application est découpée par responsabilité : `core` orchestre le cycle de
vie, `audio` produit les analyses, `scene` stocke l'état visuel, `graphics` et
`renderer` dessinent, `window` encapsule GLFW, et `config`/`utils` fournissent
les services transverses.

## Reconnaissance ACRCloud et illustrations

L'interface et les fournisseurs ACRCloud/Cover Art Archive sont conservés dans
le projet, mais la reconnaissance est volontairement désactivée pour l'instant.
MusicScope ne charge donc pas `.env` et n'effectue aucune requête réseau au
démarrage. Le travail actuel est concentré sur la capture SoundDevice,
l'analyse RMS/FFT, le rendu de la trace et le shader CRT ModernGL.
