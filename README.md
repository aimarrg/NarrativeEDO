# Nagasaki 1641: El sello de Dejima

Prototipo jugable de aventura point-and-click para **Visionaire Studio 5**.
Nagasaki, 1641 (período Edo), estética ukiyo-e. Haru empieza en su casa y
recorre cuatro escenas encadenadas: **casa → mercado → puerto → casa del
pescador**.

La historia y los diálogos son tuyos: todo el contenido narrativo está en un
único archivo editable, `build/world.py`.

Repositorio: <https://github.com/aimarrg/NarrativeEDO>

---

## 1. Cómo jugar

Doble clic en:

```
Jugar Nagasaki1641.bat
```

O a mano:

```
"C:\Program Files\Visionaire Studio 5\visplayer.exe" "game\Nagasaki1641.ved"
```

> El archivo `.ved` es el **proyecto**, no un ejecutable. Windows lo tiene
> asociado al editor de Visionaire, por eso el doble clic abre el editor y no
> el juego. Para editar: abre el `.ved` desde Visionaire Studio 5 → *Abrir
> proyecto*. Para jugar: usa el `.bat` o `visplayer.exe`.

**Controles**

| Acción | Efecto |
|---|---|
| Clic en el suelo | Haru camina hasta ahí (solo por las zonas de suelo) |
| Clic en un objeto/persona | Interactúa (el nombre aparece al pasar el ratón) |
| Clic sobre un texto | Salta el texto |
| **Clic derecho** | Abre el **menú de pausa** (Continuar / Menú principal / Salir) |

El cursor lo dibuja un script Lua (`graphics.addDrawFunc`), porque `visplayer`
oculta el cursor del sistema.

---

## 2. Estructura

```
visionaire-nagasaki/
├─ game/
│  ├─ Nagasaki1641.ved      Proyecto (XML) que abre Visionaire
│  ├─ graphics/             Fondos, objetos, cursor, marcadores
│  ├─ characters/           Sprites de Haru (andar / reposo)
│  ├─ fonts/                Noto Sans (OFL)
│  └─ audio/                Música OGG
├─ build/
│  ├─ world.py              ► CONTENIDO EDITABLE: escenas, clicables, textos
│  ├─ make_ved.py           Generador del .ved (no hace falta tocarlo)
│  ├─ make_art.py           Genera todo el arte ukiyo-e (Pillow, 1280x720)
│  ├─ make_music.py         Genera la música (numpy) y la codifica a OGG
│  ├─ art_manifest.json     Posiciones/tamaños de sprites (lo escribe make_art)
│  └─ legacy/               Copia del prototipo anterior (por si acaso)
├─ Jugar Nagasaki1641.bat
└─ README.md
```

Regenerar el juego después de editar `world.py`:

```
py build\make_ved.py
```

Si además cambias el arte:

```
py build\make_art.py
py build\make_ved.py
```

`make_ved.py` necesita `art_manifest.json`, así que ejecuta `make_art.py` antes
la primera vez o cuando cambies sprites.

---

## 3. El mapa del mundo (`build/world.py`)

Todo el juego se describe con cuatro bloques:

| Bloque | Para qué sirve |
|---|---|
| `START_SCENE` | Escena en la que empieza una partida nueva |
| `SCENES` | Escenas que se crean, su fondo, música, suelo y punto de entrada |
| `CONDITIONS` / `VALUES` | Variables de la historia (puertas abiertas, diálogos vistos…) |
| `TEXTS` | Todos los nombres y frases que se muestran |
| `CLICKABLES` | Objetos, personas y salidas: qué se ve y qué pasa al hacer clic |

### 3.1 Escenas

```python
START_SCENE = "casa"

SCENES = [
    {"key": "casa", "name": "Casa de Haru", "bg": "bg_home",
     "music": "audio/warehouse.ogg",
     "way": [(0, 585), (1280, 585), (1280, 714), (0, 714)],
     "entry": (640, 690), "start_texts": []},
    ...
]
```

- `key`: identificador interno (se usa en `scene` y `scene_to`).
- `bg`: fondo generado por `make_art.py` (`bg_home`, `bg_street`,
  `bg_port`, `bg_fisher`).
- `way`: polígono de suelo por el que puede caminar Haru. El último valor
  (`714`) es el borde inferior.
- `entry`: punto donde aparece Haru al entrar en la escena.
- `start_texts`: lista de claves de `TEXTS` que se muestran al entrar
  (vacía = ninguna). Útil para narración automática al cambiar de escena.

El **orden de la lista `SCENES`** solo afecta al orden en que las escenas
aparecen en el editor. La navegación real la definen los `scene_to` de los
clicables, así que puedes reordenar la historia sin tocar nada más.

### 3.2 Cambiar el recorrido

Cada salida es un clicable con `scene_to`:

```python
{"key": "salir_casa", "scene": "casa", "name": "n_salir_casa",
 "rect": (1030, 160, 190, 420), "stand": (1015, 690), "order": 2,
 "scene_to": "mercado"},
```

Para invertir el orden (por ejemplo, puerto antes que mercado) basta cambiar a
qué escena apunta cada salida. Las salidas actuales son:

| Desde | Salida | Hacia |
|---|---|---|
| casa | puerta derecha | mercado |
| mercado | borde izquierdo | casa |
| mercado | borde derecho | puerto |
| puerto | borde izquierdo | mercado |
| puerto | cabaña derecha | casa_pescador |
| casa_pescador | puerta izquierda | puerto |

### 3.3 Clicables

Cada entrada de `CLICKABLES` admite:

| Campo | Significado |
|---|---|
| `key` | Nombre interno único (no repetir) |
| `scene` | Escena donde aparece |
| `name` | Clave de `TEXTS` con el nombre que se ve al pasar el ratón |
| `sprite` | Sprite opcional (`photo`, `note`, `tavern_a_closed`, `fisher`…) |
| `pos` | `(x, y)` donde se dibuja el sprite |
| `rect` | `(x, y, ancho, alto)` de la zona de clic (si no hay sprite) |
| `stand` | `(x, y)` donde se coloca Haru al interactuar |
| `order` | Orden de dibujo dentro de la escena (mayor = más delante) |
| `cond` | Condición para que aparezca (opcional) |
| `negate` | `True` = aparece cuando la condición es **falsa** |
| `walk` | `False` = no camina antes de actuar (para botones y capas) |
| `text` | Clave de `TEXTS` con la frase que se muestra |
| `set` | Condiciones que se ponen a **verdadero** |
| `unset` | Condiciones que se ponen a **falso** |
| `value` | `("final", operador, número)` para cambiar un valor |
| `set_first` | Aplica condiciones **antes** del texto (para abrir el zoom) |
| `hide_char` / `show_char` | Oculta/muestra a Haru durante la acción |
| `scene_to` | Escena a la que se cambia al terminar |
| `quit` | `True` = cierra el juego |

Los objetos pueden superponerse: los que tienen `cond` aparecen y desaparecen
solos cuando la condición cambia, sin necesidad de acciones.

---

## 4. La historia: condiciones y textos

### 4.1 Condiciones

```python
CONDITIONS = {
    "viendo_foto": False,        # la foto está ampliada
    "tabernas_abiertas": False,  # las tabernas están cerradas al principio
    "hablo_pescador": False,     # marca de diálogo
    "pausa": False,              # menú de pausa abierto
}
```

Para añadir una condición nueva:

1. Añádela a `CONDITIONS`.
2. Úsala en un clicable con `"cond": "mi_condicion"` (visible cuando es
   verdadera) o `"negate": True` (visible cuando es falsa).
3. Actívala desde cualquier interacción con `"set": ["mi_condicion"]` o
   desactívala con `"unset": ["mi_condicion"]`.

### 4.2 Las dos tabernas

En el mercado hay dos tabernas, cerradas al principio:

- `taberna_a_cerrada` / `taberna_b_cerrada` → visibles mientras
  `tabernas_abiertas` es falsa (`negate: True`).
- `taberna_a_abierta` / `taberna_b_abierta` → visibles cuando
  `tabernas_abiertas` es verdadera.

Para abrirlas, añade `"set": ["tabernas_abiertas"]` al clicable que deba
hacerlo. Por ejemplo, al hablar con el pescador:

```python
{
    "key": "pescador", "scene": "casa_pescador", "name": "n_pescador",
    "sprite": "fisher", "pos": (760, 377), "stand": (865, 690),
    "order": 5, "text": "pescador",
    "set": ["hablo_pescador", "tabernas_abiertas"],   # ← abre las tabernas
},
```

No hay ninguna lógica cableada: cuando la condición cambia, los sprites
cerrados desaparecen y aparecen los abiertos.

### 4.3 Textos y diálogos

Todas las frases están en `TEXTS` dentro de `world.py`. Las claves que
empiezan por `n_` son nombres de objeto; el resto son frases:

```python
TEXTS = {
    "n_foto": "Foto de familia",
    "foto": ("Tu familia, retratada el año del incendio. Tu madre sostiene "
             "el abanico que aún guardas; tu padre finge no sonreír."),
    ...
}
```

Reglas prácticas:

- Usa `\n` para forzar un salto de línea.
- Mantén las frases por debajo de ~140 caracteres: el texto se dibuja centrado
  sobre el personaje y las líneas largas se recortan en los bordes.
- No dupliques el nombre del hablante dentro del texto salvo que quieras
  escribirlo tú (el motor no lo añade solo).
- Los acentos, `«»`, `¿` y `¡` funcionan: el `.ved` se guarda en UTF-8.

### 4.4 Conversaciones con ramas

Para una conversación que cambia según lo ya hablado, añade el texto y usa la
condición en un clicable alternativo:

```python
{"key": "pescador_1", "scene": "casa_pescador", "name": "n_pescador",
 "sprite": "fisher", "pos": (760, 377), "stand": (865, 690),
 "cond": "hablo_pescador", "negate": True,
 "text": "pescador_primera", "set": ["hablo_pescador"]},

{"key": "pescador_2", "scene": "casa_pescador", "name": "n_pescador",
 "sprite": "fisher", "pos": (760, 377), "stand": (865, 690),
 "cond": "hablo_pescador",
 "text": "pescador_despues"},
```

El primero se ve la primera vez; el segundo, después. Es la misma mecánica que
las tabernas y no requiere tocar el generador.

---

## 5. El zoom de la foto

La foto de familia no es una escena aparte: es una **capa superpuesta** a
pantalla completa (`foto_zoom`) que se muestra cuando `viendo_foto` es
verdadera.

- Al hacer clic en la foto se activa `viendo_foto` y se oculta Haru
  (`hide_char`), para que la capa tape todo.
- La foto pequeña y la nota tienen `cond: "viendo_foto"` + `negate: True`, así
  que desaparecen mientras el zoom está abierto.
- Al hacer clic en cualquier punto del zoom se desactiva `viendo_foto` y Haru
  vuelve a mostrarse (`show_char`).

Para cambiar la imagen ampliada, edita `obj_photo_zoom()` en `make_art.py` y
regenera el arte.

---

## 6. Menú principal y menú de pausa

- El **menú principal** es siempre la escena 0 (`GameFirstScene=0`). Sus
  botones se definen en `MENU_ITEMS` dentro de `make_ved.py`:
  `NUEVA PARTIDA` reinicia todas las condiciones y valores, muestra a Haru y
  salta a `START_SCENE`; `SALIR` cierra el juego.
- El **menú de pausa** se abre con **clic derecho** en cualquier escena
  (`GameRightClickAction` → acción `abrir_pausa`).
  - `CONTINUAR` cierra la pausa y muestra a Haru.
  - `MENÚ PRINCIPAL` cierra la pausa y vuelve al menú.
  - `SALIR` cierra el juego.
- La capa de pausa y sus botones son objetos con `cond: "pausa"`; se generan
  automáticamente para cada escena de `world.py`.
- Para cambiar los textos de los botones, edita `n_continuar`, `n_menu`,
  `n_salir`, `n_nueva` y `n_abandonar` en `TEXTS`.
- Para cambiar su posición, edita `PAUSE_BUTTONS` y las coordenadas del panel
  en `make_ved.py`/`obj_pause()` de `make_art.py`.

---

## 7. Añadir contenido

**Una escena nueva:**

1. Dibuja el fondo en `make_art.py` (`def bg_mi_escena()`) y añádelo al
   `main()` con `save(bg_mi_escena(), "bg_mi_escena.png")` y al manifiesto.
2. Añade la escena a `SCENES` en `world.py` con su `bg`, `music`, `way` y
   `entry`.
3. Crea sus clicables en `CLICKABLES`.
4. Enlázala desde otra escena con un clicable `"scene_to": "mi_escena"`.

**Un objeto nuevo:**

1. Dibújalo en `make_art.py` y regístralo en el diccionario `objs` del `main()`.
2. Ejecuta `py build\make_art.py` para que aparezca en `art_manifest.json`.
3. Añade un clicable en `world.py` con `"sprite": "mi_objeto"` y `"pos"`.

**Un diálogo nuevo:** añade la frase a `TEXTS` y asígnala a un clicable con
`"text": "mi_frase"`.

---

## 8. Suelo y posiciones

- Haru solo camina dentro del polígono `way` de cada escena. El borde inferior
  habitual es `y = 714`.
- `stand` es el punto al que camina Haru al interactuar con un objeto. Debe
  estar dentro del suelo y cerca del objeto.
- `order` controla qué sprite tapa a cuál dentro de la escena (mayor = más
  delante). Las capas a pantalla completa (zoom, pausa) usan valores altos
  (`900`–`960`).
- Si un sprite tapa una zona de clic, reduce su `rect` o baja su `order`.

---

## 9. Música

`build/make_music.py` sintetiza los bucles con numpy y los convierte a OGG con
`ffmpeg`. Cada escena declara su pista en `music` dentro de `SCENES`
(`audio/menu.ogg`, `audio/market.ogg`, `audio/warehouse.ogg`…).

Si `ffmpeg` no está en el PATH, instálalo o edita la ruta en `make_music.py`.

---

## 10. Exportar / publicar

Desde el editor: *Archivo → Exportar juego*. Visionaire genera una carpeta con
el `.vis` (o los recursos) y un ejecutable de distribución. Para pruebas
rápidas no hace falta exportar: `visplayer.exe` + el `.ved` ya ejecuta el
juego.

Requisitos para que el juego funcione: mantener juntos el `.ved` y las
carpetas `graphics/`, `characters/`, `fonts/` y `audio/`.

---

## 11. Copia de seguridad

El prototipo anterior (mercado/almacén/epílogo y su generador) está guardado en
`build/legacy/`:

- `Nagasaki1641_v1.ved`
- `make_ved_v1.py`
- `make_art_v1.py`

No se usa al regenerar; solo sirve para recuperar algo del diseño anterior.

---

## 12. Créditos y licencias

- Arte, música y textos: generados para este prototipo.
- Tipografía: **Noto Sans** (SIL Open Font License).
- Motor: **Visionaire Studio 5**.
- Inspiración de diseño: aventuras point-and-click clásicas y grabados
  ukiyo-e del período Edo.
