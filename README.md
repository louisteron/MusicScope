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

Le visuel central par défaut est la grenouille, dont les contours réagissent à la musique :

```bash
musicscope --logo frog
```

Appuie sur `M` (ou `F1`) pour ouvrir le menu **OSCILLATION**. Sur certains
claviers AZERTY macOS, la touche physique `M` est également prise en charge.
Utilise `↑` et `↓` pour sélectionner l'amplitude, l'épaisseur, la réactivité,
le mode couleur ou la sortie audio, puis `←` et `→` pour modifier la valeur en
temps réel.
Appuie de nouveau sur `M` pour le fermer.

La ligne `RECOGNITION` permet de basculer immédiatement entre `AUDD`, `LOCAL CD`
et `OFF`. `LOCAL CD` arrête AudD et lit les métadonnées du CD présent dans le
lecteur configuré avec `--cd-device`.

### Sortie jack / chaîne hi-fi

Dans le menu **SETTINGS**, l'option `OUTPUT` est sur `OFF` par défaut. Utilise
`←` et `→` pour choisir la sortie qui correspond à ta prise jack ou à ton
adaptateur audio USB : MusicScope renvoie alors l'audio capturé vers cette
sortie tout en le visualisant et en l'envoyant à AudD.

Ce mode est adapté à une platine vinyle, un lecteur CD/cassette ou un téléphone
branché sur une **entrée audio** du Raspberry Pi/de la carte son. Avec BlackHole
sur macOS, préfère généralement un périphérique de sortie multiple dans
Configuration Audio et MIDI ; activer en plus `OUTPUT` peut dupliquer le son.

Les modes couleur sont :

- `COVER NEON` *(mode par défaut)* : seuls les traits de la cover reprennent
  ses couleurs d'origine, tout en conservant l'effet néon.
- `NEON GREEN` : le rendu oscilloscope vert classique.
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

## Mode CD local (sans AudD)

Le mode `local-cd` ne transmet aucun extrait audio à AudD. Il lit l'identifiant
du CD dans un lecteur interne ou USB, recherche ses métadonnées dans MusicBrainz,
puis récupère la cover via Cover Art Archive et le cache local de MusicScope.
Il fonctionne donc pour les CD, même si l'entrée audio utilisée pour le
visualiseur est une autre source.

Installe le support de lecture de CD et la bibliothèque système requise :

```bash
sudo apt install libdiscid0
uv sync --extra cd
```

Puis démarre MusicScope avec le lecteur optique (sur Raspberry Pi/Linux,
`/dev/sr0` est courant) :

```bash
musicscope --recognition-mode local-cd --cd-device /dev/sr0
```

Le mode CD reste dépendant de MusicBrainz et de Cover Art Archive pour les
métadonnées et la cover, mais ne nécessite aucune clé API ni AudD. Si le CD
n'est pas référencé, MusicScope continue normalement sans modifier le visuel.
