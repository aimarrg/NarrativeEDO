# Nagasaki 1641: El sello de Dejima

Prototipo jugable de aventura point-and-click para **Visionaire Studio 5**.
Nagasaki, 1641 (período Edo), estética ukiyo-e. La partida se abre con una
**cinemática en el castillo del Shogun** (la ejecución de Haru) y, al terminar,
Haru despierta en su casa. Desde ahí recorre la ciudad:
**casa → calle → puerto (pescador) → calle → mercado**, y de vuelta.

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
| Clic sobre un texto | Salta el texto (sale en el cuadro de arriba) |
| **Clic derecho** o **ESC** | Abre el **menú de pausa** (Continuar / Menú principal / Salir) |

`ESC` también cierra el menú de pausa (lo implementa un script Lua con
`registerEventHandler("keyEvent", …)`). En la cinemática del castillo, cerrar
la pausa no saca a Haru de pie: la pausa respeta `pause_show_char`.

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
│  ├─ fix_editor_layout.py  Reinicia el layout del editor de Visionaire
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

Y si cambias la música (necesita `ffmpeg` en el PATH):

```
py build\make_music.py
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
START_SCENE = "castillo"

SCENES = [
    {"key": "castillo", "name": "Castillo del Shogun", "bg": "bg_castle",
     "music": "audio/castle.ogg",
     "way": [(0, 600), (1280, 600), (1280, 714), (0, 714)],
     "entry": (240, 690),
     "start_hide_char": True,
     "cinematic": ["castillo_1", "castillo_2",
                   {"set": "ejecutado"}, "castillo_7"],
     "start_show_char": True,
     "start_scene_to": "casa",
     "pause_show_char": False},
    {"key": "casa", "name": "Casa de Haru", "bg": "bg_home",
     "music": "audio/warehouse.ogg",
     "way": [(0, 585), (1280, 585), (1280, 714), (0, 714)],
     "entry": (640, 690), "start_texts": []},
    ...
]
```

- `key`: identificador interno (se usa en `scene` y `scene_to`).
- `bg`: fondo generado por `make_art.py` (`bg_castle`, `bg_home`,
  `bg_street`, `bg_market`, `bg_port`, `bg_fisher`).
- `way`: polígono de suelo por el que puede caminar Haru. El último valor
  (`714`) es el borde inferior.
- `entry`: punto donde aparece Haru al entrar en la escena.
- `start_texts`: lista de claves de `TEXTS` que se muestran al entrar
  (vacía = ninguna). Útil para narración automática al cambiar de escena.
- `cinematic`: como `start_texts`, pero admite bloques `{"set": "condición"}`
  entre las frases. Si existe, manda sobre `start_texts`.
- `start_hide_char` / `start_show_char`: ocultan a Haru al empezar y lo
  vuelven a mostrar al terminar (para cinemáticas).
- `start_scene_to`: escena a la que se salta cuando acaba la secuencia.
- `pause_show_char`: ponlo a `False` si el menú de pausa no debe mostrar a
  Haru al pulsar CONTINUAR (por ejemplo, en una cinemática).

El **orden de la lista `SCENES`** solo afecta al orden en que las escenas
aparecen en el editor. La navegación real la definen los `scene_to` de los
clicables, así que puedes reordenar la historia sin tocar nada más.

### 3.2 Cambiar el recorrido

Cada salida es un clicable con `scene_to`:

```python
{"key": "salir_casa", "scene": "casa", "name": "n_salir_casa",
 "rect": (1030, 160, 190, 420), "stand": (1015, 690), "order": 2,
 "scene_to": "calle"},
```

Para invertir el orden (por ejemplo, mercado antes que puerto) basta cambiar a
qué escena apunta cada salida. Las salidas actuales son:

| Desde | Salida | Hacia |
|---|---|---|
| castillo | (cinemática inicial) | casa |
| casa | puerta derecha | calle |
| calle | borde izquierdo (con el pase) | mercado |
| calle | borde izquierdo (sin el pase) | aviso: «Abre a las 9:00» |
| calle | borde derecho | puerto |
| calle | puerta central | casa |
| mercado | borde izquierdo | calle |
| puerto | borde izquierdo | calle |
| puerto | cabaña derecha | casa_pescador |
| casa_pescador | puerta izquierda | puerto |

El castillo no tiene salidas clicables: se recorre solo, de principio a fin, y
salta a `casa` al terminar su cinemática.

> Las claves de `CLICKABLES` deben ser **únicas en todo el juego**, aunque las
> salidas estén en escenas distintas (por eso el mercado usa `salir_mercado` y
> el puerto `volver_calle`). Si repites una clave, `make_ved.py` se detiene con
> un error para que no desaparezca una salida sin darte cuenta.

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
    "hablo_pescador": False,     # ya has hablado con el pescador
    "tengo_check": False,        # el pescador te ha dado el pase del mercado
    "pausa": False,              # menú de pausa abierto
    "sin_haru_en_pausa": False,  # la pausa no muestra a Haru (cinemáticas)
    "ejecutado": False,          # el filo ha caído en la cinemática inicial
}
```

Para añadir una condición nueva:

1. Añádela a `CONDITIONS`.
2. Úsala en un clicable con `"cond": "mi_condicion"` (visible cuando es
   verdadera) o `"negate": True` (visible cuando es falsa).
3. Actívala desde cualquier interacción con `"set": ["mi_condicion"]` o
   desactívala con `"unset": ["mi_condicion"]`.

### 4.2 Las dos tabernas

En la calle hay dos tabernas, cerradas al principio:

- `taberna_a_cerrada` / `taberna_b_cerrada` → visibles mientras
  `tabernas_abiertas` es falsa (`negate: True`).
- `taberna_a_abierta` / `taberna_b_abierta` → visibles cuando
  `tabernas_abiertas` es verdadera.

Para abrirlas, añade `"set": ["tabernas_abiertas"]` al clicable que deba
hacerlo. Por ejemplo, al hablar con el pescador:

```python
{
    "key": "pescador_1", "scene": "casa_pescador", "name": "n_pescador",
    "sprite": "fisher", "pos": (760, 377), "stand": (990, 690),
    "order": 5, "text": "pescador",
    "cond": "hablo_pescador", "negate": True,
    "set": ["hablo_pescador", "tengo_check", "tabernas_abiertas"],
},
```

No hay ninguna lógica cableada: cuando la condición cambia, los sprites
cerrados desaparecen y aparecen los abiertos.

### 4.3 El pase del mercado

La calle tiene dos salidas laterales: a la izquierda el **mercado**, a la
derecha el **puerto**. Al principio no se puede entrar al mercado:

- `mercado_cerrado` (condición `tengo_check` **negada**) ocupa el borde
  izquierdo y muestra «El mercado está cerrado… abre a las 9:00».
- `ir_mercado` (condición `tengo_check`) ocupa el mismo rect y cambia a la
  escena `mercado` cuando ya tienes el pase.

El pase lo da el pescador en su primera conversación
(`"set": ["hablo_pescador", "tengo_check"]`). Para cambiar el requisito, usa
otra condición en `ir_mercado` / `mercado_cerrado`, o pon el `set` donde
prefieras.

En el mercado hay tres puestos: el del **socio** (izquierda), el **tuyo**
(centro) y el del **rival** (derecha). Cada uno es un clicable independiente
con su propio texto (`mercado_socio`, `mercado_tuyo`, `mercado_rival`).

### 4.4 Textos y diálogos

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

- **Todos los textos salen en un cuadro centrado arriba** (panel semitransparente
  de 1000x110 en `x=140..1140`, `y=10..120`). Hay un objeto `dialog_box_<escena>`
  por escena; el generador enciende la condición `caja_texto` justo antes de cada
  texto y la apaga justo después, así que el cuadro solo se ve mientras suena una
  frase. El texto se centra (`GameTextAlignment = 2`) y la fuente rompe línea a
  880 px, de modo que ninguna frase pasa de 2 líneas dentro del cuadro.
- **El nombre de un clicable aparece junto al cursor**, es decir, sobre el propio
  objeto (`GameDrawActionText = 1`). `GameActionTextRect` solo marca los límites
  para que el nombre no se corte en los bordes. Con el valor `2` el nombre se
  dibujaría fijo dentro de ese rectángulo, que es lo que lo dejaba en medio abajo.
- Las opciones de diálogo (`GameDialogTextAlignment`) también se centran (`2`).

### 4.5 Conversaciones con ramas

Para una conversación que cambia según lo ya hablado, añade el texto y usa la
condición en un clicable alternativo:

```python
{"key": "pescador_1", "scene": "casa_pescador", "name": "n_pescador",
 "sprite": "fisher", "pos": (760, 377), "stand": (990, 690),
 "cond": "hablo_pescador", "negate": True,
 "text": "pescador", "set": ["hablo_pescador", "tengo_check"]},

{"key": "pescador_2", "scene": "casa_pescador", "name": "n_pescador",
 "sprite": "fisher", "pos": (760, 377), "stand": (990, 690),
 "cond": "hablo_pescador",
 "text": "pescador_despues"},
```

El primero se ve la primera vez (y da el pase del mercado); el segundo,
después. Es la misma mecánica que las tabernas y no requiere tocar el
generador.

### 4.6 La cinemática inicial (castillo del Shogun)

La partida no empieza en casa: `START_SCENE = "castillo"` y la escena
`castillo` reproduce su secuencia de entrada. Está descrita en `SCENES`:

```python
"start_hide_char": True,          # Haru no aparece de pie en el cadalso
"cinematic": [
    "castillo_1", "castillo_2",   # claves de TEXTS, en orden
    "castillo_3", "castillo_4",
    "castillo_5", "castillo_6",
    {"set": "ejecutado"},         # ← aquí cae el filo
    "castillo_7", "castillo_8", "castillo_9",
],
"start_show_char": True,
"start_scene_to": "casa",         # al acabar, Haru despierta en su casa
"pause_show_char": False,         # la pausa no saca a Haru de pie aquí
```

Qué hace cada pieza:

- Cada cadena es una frase de `TEXTS`; se muestran seguidas y se pueden
  saltar con un clic. Los diálogos son marcadores: escríbelos tú.
- `{"set": "ejecutado"}` cambia la condición a mitad de la secuencia. Los
  objetos del cadalso están ligados a ella: mientras es falsa se ve la
  guillotina con el filo arriba y Haru de rodillas (`haru_reo`); cuando pasa a
  verdadera, se cambia a `guillotine_down` y desaparece el reo.
- `start_hide_char` oculta al personaje real (el de los sprites de andar), y
  `start_show_char` lo vuelve a mostrar antes de saltar a casa.
- El decorado son cuatro objetos sin acción en `CLICKABLES` (`guillotine_up`,
  `guillotine_down`, `verdugo`, `haru_reo`); se mueven con las claves `pos` y
  `order` como cualquier otro sprite. Los cuatro están **en el suelo del
  patio**, con los pies/base a la altura `y ≈ 700`, y sus clics en
  `guillotine_up/down` (250, 368), `verdugo` (470, 449) y `haru_reo`
  (320, 579).
- El fondo `bg_castle` dibuja el **torreón arriba**, sobre la muralla, y una
  **escalinata central** que sube desde el patio hasta la puerta. Para mover
  algo, cambia su `pos` (la base del sprite) sin tocar el generador.

Para cambiar el texto de la cinemática edita `castillo_1` … `castillo_9` en
`TEXTS`. Para alargarla o acortarla, añade o quita claves en `cinematic`.

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
- El **menú de pausa** se abre con **clic derecho** (`GameRightClickAction` →
  acción `abrir_pausa`) o con **ESC** (script Lua `nagasakiKeyHandler`).
  - `CONTINUAR` cierra la pausa y muestra a Haru.
  - `MENÚ PRINCIPAL` cierra la pausa y vuelve al menú.
  - `SALIR` cierra el juego.
- El script de teclado filtra `eEvtKeyDown` (el evento llega dos veces: tecla
  pulsada y soltada) y consume la tecla con `return true`.
- Al cerrar la pausa, la acción `Cerrar pausa` consulta `sin_haru_en_pausa`.
  Cada acción de inicio de escena la fija según `pause_show_char`, así que en
  la cinemática del castillo Haru no reaparece de pie. Ya no se detecta la
  escena por nombre (en Lua `Scene.Name` no devuelve la clave de `world.py`).
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
(`audio/menu.ogg`, `audio/market.ogg`, `audio/warehouse.ogg`,
`audio/castle.ogg`…).

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

## 11. El editor de Visionaire

### 11.1 Abrir el proyecto

El editor arranca en una pantalla de inicio (Home). Para trabajar en el juego:
**Load recently opened game → `Nagasaki1641.ved`** (o `CTRL+O` y elegir
`game\Nagasaki1641.ved`). El título de la ventana muestra la ruta del proyecto
abierto.

Las secciones se cambian con los iconos de la barra superior:

| Icono | Sección |
| --- | --- |
| engranaje | Game properties (escena inicial, personaje activo, resolución…) |
| casita | **Scenes** (escenas y sus objetos) |
| persona | Characters |
| ventana | Interfaces |
| diamante | Items / Objects |
| flecha | Cursors |
| A | Fonts |
| `{}` | Scripts |
| copo | Particles |
| bocadillo | Texts (diálogos y traducciones) |
| líneas | Shaders |
| onda | Audio |

En *Scenes*, la lista de la izquierda son las escenas (`menu` no aparece aquí:
está en la sección *Menus*). Al seleccionar una escena, la zona central muestra
su imagen y sus pestañas `Objects / Way systems / Actions / Curves`, y a la
derecha sus `Conditions / Values / Components`.

> Coordenadas de los iconos en pantalla (para depurar): con un editor abierto en
> pantalla completa (2560x1440), la casita (*Scenes*) está en aproximadamente
> `(x=276, y=25)` a partir del esquina superior izquierda del cliente, y el
> engranaje (*Game properties*) en `(150, 20)`. Si un clic no responde, probar con
> el cursor justo encima del icono.

Para inspeccionar todo el proyecto de una vez: *Tools → Explorer* (`CTRL+E`),
que lista `eScenes`, `eCharacters`, `eDialogs`, `eTexts`…

### 11.5 Verificación (estado actual)

Con las dos correcciones de arriba, el editor ya no muestra secciones vacías:

- *Game properties*: datos reales (primera escena `menu`, personaje activo `Haru`,
  idioma `Español`, fuente de texto `Noto`, 1280x720).
- *Scenes*: lista con las **7 escenas** (`menu`, `castillo`, `casa`, `calle`,
  `mercado`, `puerto`, `casa_pescador`), y al seleccionar una se ven la imagen de
  fondo, sus objetos (`Objects`), la pestaña `Actions` y la panel de
  condiciones.
- *Characters*: 1 personaje (`Haru`).
- *Fonts*: fuente `Noto`.
- *Texts*: 54 textos / diálogos.

Si algún panel sigue en blanco de nuevo, mirar `build/make_ved.py` (listas de
enlaces) y `build/fix_editor_layout.py` (workspace del `.ini`).

### 11.2 Si una sección sale vacía

El editor guarda el layout de paneles en
`%LOCALAPPDATA%\Visionaire Editor\viseditor.ini` y **solo guarda el de la
sección que estuviera activa al cerrarlo**. Si sales del editor estando en
*Texts*, la próxima vez abre con el panel de diálogos y traducciones y parece
que el proyecto "solo tiene textos": el `.ved` está bien, es el layout.

Dos remedios:

1. En el editor: clic derecho sobre el icono de la sección (la casita para
   *Scenes*) → **Reset workspace**.
2. Con el editor cerrado:

   ```
   py build\fix_editor_layout.py
   ```

   Borra la línea `Workspaces=` del `.ini` (con copia de seguridad) y el editor
   reconstruye el layout por defecto. Si el editor sigue abierto, al salir
   volverá a escribir su workspace.

### 11.3 Las listas del juego (`GameSceneLinks`)

Cada sección del editor es un filtro sobre el proyecto (`\eScenes`,
`\eCharacters`, `\eFonts`…, definidos en `structures.xml` del programa). Esas
rutas recorren las listas de enlaces que cuelgan del objeto `Game`:
`GameSceneLinks`, `GameCharacterLinks`, `GameFontLinks`, `GameCursors`…

El player no las necesita (carga las escenas del contenedor `<Scenes>`), pero
el editor **sí**: si están vacías, el proyecto abre, *Game properties* muestra
los datos, y sin embargo *Scenes*, *Characters* o *Fonts* aparecen sin
contenido. Por eso `make_ved.py` las rellena al final con un `<Link>` por cada
objeto (`id` del objeto y `tableId` de su tabla: escenas 4, personajes 0, fuentes
3, cursores 15). Si algún día se añade una tabla nueva al generador, hay que
añadir también su lista de enlaces.

### 11.4 Guardar

> Cada vez que el editor se cierra guarda el `.ved` (y reescribe el archivo con
> su propio formato). La fuente de verdad del proyecto es `build\make_ved.py`:
> si has estado trasteando en el editor y quieres volver a la versión generada,
> ejecuta `py build\make_ved.py`, o `git checkout -- game/Nagasaki1641.ved`.

---

## 12. Copia de seguridad

El prototipo anterior (mercado/almacén/epílogo y su generador) está guardado en
`build/legacy/`:

- `Nagasaki1641_v1.ved`
- `make_ved_v1.py`
- `make_art_v1.py`

No se usa al regenerar; solo sirve para recuperar algo del diseño anterior.

---

## 13. Créditos y licencias

- Arte, música y textos: generados para este prototipo.
- Tipografía: **Noto Sans** (SIL Open Font License).
- Motor: **Visionaire Studio 5**.
- Inspiración de diseño: aventuras point-and-click clásicas y grabados
  ukiyo-e del período Edo.
