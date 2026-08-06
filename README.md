# MusicScope

MusicScope transforme un Raspberry Pi (ou un ordinateur) en visualiseur musical
temps réel. La V0.1 ouvre une fenêtre OpenGL, capture l'entrée audio et affiche
un fond dont l'intensité réagit au niveau sonore.

> **V0.1 alpha** — la playlist locale est prête aux essais sur macOS et Linux
> avec `mpv`. Le mode CD dépend du lecteur, de `libdiscid` et de la plateforme.
> Sous Windows, les playlists locales lisent l'audio avec `mpv` embarqué et le
> visualiseur capture automatiquement les haut-parleurs via WASAPI. Le suivi
> automatique de la piste suivante et le recalage après une pause restent
> expérimentaux pour les paroles synchronisées.

## Démarrage

Python 3.13 est requis.

```bash
uv sync --extra dev
uv run musicscope
```

Pour créer un exécutable natif, installe les dépendances de release puis lance
PyInstaller sur **chaque OS cible** :

```bash
uv sync --extra release
uv run pyinstaller --noconfirm --clean packaging/musicscope.spec
```

Les builds automatisés et la checklist de publication sont documentés dans
[`RELEASE.md`](RELEASE.md).

### Prérequis des builds alpha

Les archives de release incluent MusicScope mais pas le lecteur audio externe
`mpv`. Pour écouter une playlist locale ou un CD, installe `mpv` sur la machine
du testeur (`brew install mpv` sur macOS, `sudo apt install mpv` sur Debian et
Ubuntu). L'archive Windows inclut désormais `mpv` pour lire les playlists sans
installation supplémentaire. Le mode CD nécessite en plus un lecteur CD audio
et `libdiscid`.
Sous Windows, le visualiseur est utilisable ; la lecture locale et le suivi des
pistes restent expérimentaux dans cette alpha.

Sur macOS, ouvre `MusicScope.app` après l'avoir déplacée hors du dossier
Téléchargements. Les builds alpha ne sont pas encore signés avec un certificat
Apple Developer : si macOS les bloque, utilise clic droit sur l'application,
puis **Ouvrir** et confirme l'ouverture.

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

### Playlist locale par glisser-déposer

Déposez un ou plusieurs fichiers audio, ou un dossier d'album, directement dans la fenêtre MusicScope. Les fichiers sont ajoutés à une playlist locale et lus à la suite avec `mpv`. MusicScope lit leurs tags intégrés (`titre`, `artiste`, `album` et `numéro de piste`) ; le nom du dossier devient le nom de l'album lorsqu'un tag album est absent. Il utilise d'abord `cover.jpg`, `folder.jpg` ou la cover intégrée au fichier, puis cherche et met en cache la pochette de l'album à partir de ces métadonnées. Les formats pris en charge sont MP3, M4A, FLAC, WAV, OGG, OPUS, AAC et AIFF.

Pour visualiser la musique locale, conservez la même sortie loopback que pour le CD (par exemple BlackHole) : MusicScope envoie `mpv` vers cette entrée et le visualiseur la lit en temps réel.
Les paroles utilisent aussi le temps de lecture réel de `mpv` : LRCLIB est utilisé en premier, puis Lyrics.ovh en secours lorsque des paroles synchronisées ne sont pas disponibles.

Appuyez sur `P` pour afficher le panneau **PLAYLIST** à droite. Cliquez sur une ligne pour lire ce morceau, glissez-la vers le haut ou le bas pour modifier l'ordre de lecture, cliquez sur `×` pour retirer un morceau, ou choisissez `CLEAR PLAYLIST` pour tout supprimer.

## Logos réactifs

Le visuel central par défaut est la grenouille, dont les contours réagissent à la musique :

```bash
musicscope --logo frog
```

Appuie sur `M` (ou `F1`) pour ouvrir le menu **OSCILLATION**. Sur certains
claviers AZERTY macOS, la touche physique `M` est également prise en charge.
Utilise `↑` et `↓` pour sélectionner l'amplitude, l'épaisseur, la réactivité,
le mode couleur, la palette `PHOSPHOR`, `TRACK NO.`, ou la sortie audio, puis
`←` et `→` pour modifier la valeur en temps réel. `PHOSPHOR` propose vert,
blanc, ambre, bleu et violet pour tout l'environnement oscilloscope.
`TRACK NO.` affiche ou masque le numéro de piste quand il est disponible,
notamment avec un CD local.
Appuie de nouveau sur `M` pour le fermer.

Pour éjecter le CD sans quitter MusicScope, utilise `⌘E` sur macOS ou `Ctrl+E`
sur Windows et Linux. La lecture est arrêtée avant l'éjection.

Avec un CD local en lecture, appuie sur `Espace` pour afficher la barre de
transport : le temps courant et la durée de la piste apparaissent. Clique sur
la barre pour avancer ou reculer dans le morceau, puis appuie de nouveau sur
`Espace` pour la masquer.

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

MusicScope est distribué sous licence [MIT](LICENSE).

## Mode CD local (sans AudD)

Le mode `local-cd` ne transmet aucun extrait audio à AudD. Il lit l'identifiant
du CD dans un lecteur interne ou USB, recherche ses métadonnées dans MusicBrainz,
puis récupère la cover via Cover Art Archive et le cache local de MusicScope.
Lorsqu'un CD audio est présent, MusicScope lance aussi sa lecture avec `mpv`.
Il fonctionne donc pour les CD, même si l'entrée audio utilisée pour le
visualiseur est une autre source.

Installe le support de lecture de CD et la bibliothèque système requise :

```bash
sudo apt install libdiscid0
sudo apt install mpv
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
Sur macOS, installe le lecteur avec `brew install mpv`.

### Paroles de secours

MusicScope recherche d'abord des paroles synchronisées via LRCLIB. Si aucune
ligne LRC n'est disponible, il utilise Lyrics.ovh sans clé API. Ce dernier ne
fournit pas d'horodatages : les lignes sont donc affichées avec un rythme
approximatif de quatre secondes par ligne.
