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

## Développement

```bash
uv run ruff check .
uv run pytest
```

L'application est découpée par responsabilité : `core` orchestre le cycle de
vie, `audio` produit les analyses, `scene` stocke l'état visuel, `graphics` et
`renderer` dessinent, `window` encapsule GLFW, et `config`/`utils` fournissent
les services transverses.
