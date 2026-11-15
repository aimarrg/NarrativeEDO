# -*- coding: utf-8 -*-
"""
Genera game/Nagasaki1641.ved: proyecto de Visionaire Studio 5 (XML .ved)
para el prototipo "Nagasaki 1641: El sello de Dejima".
"""
import json
import os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game")
MANIFEST = json.load(open(os.path.join(ROOT, "build", "art_manifest.json"), encoding="utf-8"))

T = {
    "characters": 0, "interfaces": 1, "buttons": 2, "fonts": 3, "scenes": 4,
    "points": 5, "objects": 6, "actions": 7, "actionparts": 8, "animations": 9,
    "conditions": 10, "dialogs": 11, "dialogparts": 12, "sprites": 13, "texts": 14,
    "cursors": 15, "commentsets": 16, "outfits": 17, "languages": 18, "values": 20,
    "interfaceclasses": 31, "waysystems": 29, "scripts": 30,
}

# El editor de Visionaire no muestra en la lista de "Characters" el personaje
# con id="0" (lo trata como "sin personaje"), asi que Haru se guarda con id 1
# y todas las referencias (GameCharacterLinks, GameFirstCharacter, ActionParts)
# apuntan a ese id.
CHAR_ID = 1
NARRATOR_ID = 2

FONT_PATH = "fonts/NotoSans-Regular.ttf"
ALPHABET = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            "áéíóúüñÁÉÍÓÚÜÑ¿¡.,:;!?()'-·%")

# ---------------------------------------------------------------------------
# Estado del proyecto
# ---------------------------------------------------------------------------
texts, conditions, values, sprites, actions, aps, animations, objects, scenes = ([] for _ in range(9))
next_ids = {k: 0 for k in ["text", "cond", "val", "sprite", "action", "ap", "anim", "obj", "scene"]}


def nid(kind):
    i = next_ids[kind]
    next_ids[kind] += 1
    return i


def add_text(s, name=None):
    i = nid("text")
    texts.append({"id": i, "name": name or f"Texto {i}", "text": s})
    return i


def add_cond(name, initial=False):
    i = nid("cond")
    conditions.append({"id": i, "name": name, "value": initial})
    return i


def add_value(name, initial=0):
    i = nid("val")
    values.append({"id": i, "name": name, "value": initial})
    return i


def add_sprite(path, x, y, name=None):
    i = nid("sprite")
    sprites.append({"id": i, "path": path, "x": x, "y": y, "name": name or f"Sprite {i}"})
    return i


def add_ap(cmd, name, link1=None, link2=None, i1=0, i2=0, i3=0):
    i = nid("ap")
    aps.append({"id": i, "cmd": cmd, "name": name, "l1": link1, "l2": link2,
                "i1": i1, "i2": i2, "i3": i3, "order": 0})
    return i


def add_action(name, exec_type, part_ids):
    i = nid("action")
    for n, p in enumerate(part_ids):
        aps[p]["order"] = n
    actions.append({"id": i, "name": name, "exec": exec_type, "parts": list(part_ids)})
    return i


# ---------------------------------------------------------------------------
# Contenido narrativo (definido en build/world.py)
# ---------------------------------------------------------------------------
import world

COND = {}
for _name, _initial in world.CONDITIONS.items():
    COND[_name] = add_cond(_name, _initial)

VAL = {}
for _name, _initial in world.VALUES.items():
    VAL[_name] = add_value(_name, _initial)

TX = {}
for _key, _s in world.TEXTS.items():
    TX[_key] = add_text(_s, _key)

SCENE_NAME = {}
for _sc in world.SCENES:
    SCENE_NAME[_sc["key"]] = add_text(_sc["name"], "scene_" + _sc["key"])
SCENE_NAME["menu"] = add_text("Menú principal", "scene_menu")


# ---------------------------------------------------------------------------
# Objetos
# ---------------------------------------------------------------------------
OBJ = {}
_OBJ_ORDER = [0]


def make_object(key, scene_key, z=0, name_text=None, sprite=None, pos=None,
                rect=None, cond=None, negate=False, walkable="F", stand=None):
    """Crea un objeto. El sprite es opcional (las salidas son zonas invisibles)."""
    if key in OBJ:
        # Cada clicable necesita una clave única aunque esté en escenas distintas:
        # si se repite, el segundo sustituye al primero y su escena se queda sin él.
        raise SystemExit(
            "ERROR: la clave de clicable '%s' está repetida en world.py" % key)
    w = h = 0
    sprite_id = None
    if sprite is not None:
        m = MANIFEST["objects"][sprite]
        px, py = pos if pos is not None else (m["x"], m["y"])
        sprite_id = add_sprite(m["path"], px, py, sprite)
        w, h = m["w"], m["h"]
    else:
        px, py = pos if pos is not None else (0, 0)

    if rect is None:
        rect = (px, py, w, h)
    if stand is None:
        stand = (rect[0] + rect[2] // 2, rect[1] + rect[3] - 4)

    OBJ[key] = {
        "id": nid("obj"),
        "name": name_text,
        "sprite": sprite_id,
        "scene": scene_key,
        "order": _OBJ_ORDER[0],
        "z": z,
        "cond": COND.get(cond) if cond else None,
        "walkable": walkable,
        "negate": negate,
        "stand": stand,
        "rect": rect,
    }
    _OBJ_ORDER[0] += 1
    return key


def make_zone(key, scene_key, z, name_text, rect, stand=None, cond=None,
              negate=False, walkable="F"):
    """Zona clicable sin dibujo (salidas, botones, áreas del decorado)."""
    return make_object(key, scene_key, z=z, name_text=name_text, sprite=None,
                       rect=rect, stand=stand, cond=cond, negate=negate,
                       walkable=walkable)


# Punto de entrada invisible de cada escena (destino de los cambios de escena)
for _sc in world.SCENES + [{"key": "menu", "entry": (640, 690)}]:
    _ex, _ey = _sc["entry"]
    make_object("_entry_" + _sc["key"], _sc["key"], z=-10, walkable="T",
                rect=(_ex - 6, _ey - 6, 12, 12), stand=(_ex, _ey))


# ---------------------------------------------------------------------------
# ActionParts
# ---------------------------------------------------------------------------
def ap_text(text_id, char=CHAR_ID, obj=None):
    if obj is not None:
        link2 = (T["objects"], OBJ[obj]["id"])
    else:
        link2 = (T["characters"], char)
    return add_ap(23, "DIALOGO", link1=(T["texts"], text_id),
                  link2=link2, i1=0)


def ap_if(cond_id, is_true=True, elseif=False):
    return add_ap(140, "Si condición", link1=(T["conditions"], cond_id),
                  i1=0 if is_true else 1, i3=1 if elseif else 0)


def ap_setcond(cond_id, value=0):
    return add_ap(139, "Cambiar condición", link1=(T["conditions"], cond_id), i1=value)


def ap_else():
    return add_ap(5, "Si no")


def ap_endif():
    return add_ap(6, "Fin si")


def ap_ifvalue(value_id, op, number, elseif=False):
    return add_ap(69, "Comparar valor", link1=(T["values"], value_id),
                  i1=op, i2=number, i3=1 if elseif else 0)


def ap_setvalue(value_id, op, number):
    return add_ap(70, "Cambiar valor", link1=(T["values"], value_id), i1=op, i2=number)


def ap_goto(obj_key):
    o = OBJ[obj_key]
    return add_ap(31, "Ir a " + obj_key, link1=(T["characters"], CHAR_ID),
                  link2=(T["objects"], o["id"]), i1=1)


def ap_scene(entry_key):
    o = OBJ[entry_key]
    return add_ap(10, "Cambiar a escena " + entry_key,
                  link1=(T["objects"], o["id"]), i1=1, i2=0)


def ap_showchar(char=CHAR_ID):
    return add_ap(98, "Mostrar personaje", link1=(T["characters"], char), i1=0)


def ap_hidechar(char=CHAR_ID):
    return add_ap(98, "Ocultar personaje", link1=(T["characters"], char), i1=1)


# ---------------------------------------------------------------------------
# Clicables definidos en world.py
# ---------------------------------------------------------------------------
OBJ_ACTION = {}
OBJECT_COUNT = [0]


def build_clickable(spec):
    key = spec["key"]
    make_object(
        key,
        spec["scene"],
        z=spec.get("order", 0),
        name_text=TX.get(spec.get("name")) if spec.get("name") else None,
        sprite=spec.get("sprite"),
        pos=spec.get("pos"),
        rect=spec.get("rect"),
        cond=spec.get("cond"),
        negate=spec.get("negate", False),
        stand=spec.get("stand"),
    )

    wants_action = any(k in spec for k in
                       ("text", "set", "unset", "value", "scene_to", "quit"))
    if not wants_action:
        return

    parts = []
    if spec.get("walk", True):
        parts.append(ap_goto(key))

    def condition_parts():
        out = []
        for cname in spec.get("set", []):
            out.append(ap_setcond(COND[cname]))
        for cname in spec.get("unset", []):
            out.append(ap_setcond(COND[cname], 1))
        if spec.get("value"):
            vname, op, number = spec["value"]
            out.append(ap_setvalue(VAL[vname], op, number))
        if spec.get("hide_char"):
            out.append(ap_hidechar())
        if spec.get("show_char"):
            out.append(ap_showchar())
        return out

    if spec.get("set_first"):
        parts.extend(condition_parts())
    if spec.get("text"):
        parts.append(ap_text(TX[spec["text"]], obj=key))
    if not spec.get("set_first"):
        parts.extend(condition_parts())
    if spec.get("scene_to"):
        target = spec["scene_to"]
        parts.append(ap_scene("_entry_" + target))
    if spec.get("quit"):
        parts.append(add_ap(55, "Salir"))

    OBJ_ACTION[key] = add_action("Acción: " + key, 7, parts)


for _spec in world.CLICKABLES:
    build_clickable(_spec)

# Caja de dialogo (panel superior semi-transparente, solo en la cinematica del castillo).
_box_sprite = add_sprite("graphics/dialog_box.png", 140, 10, "dialog_box")
OBJ["dialog_box"] = {
    "id": nid("obj"),
    "name": None,
    "sprite": _box_sprite,
    "scene": "castillo",
    "order": 0,
    "z": 1000,
    "cond": COND.get("ejecutado"),
    "negate": True,
    "stand": (640, 690),
    "rect": (140, 10, 1000, 110),
    "walkable": "F",
}


# ---------------------------------------------------------------------------
# Menú principal
# ---------------------------------------------------------------------------
MENU_ITEMS = [
    {"key": "menu_nueva", "name": "n_nueva", "rect": (440, 396, 400, 66),
     "new_game": True},
    {"key": "menu_salir", "name": "n_abandonar", "rect": (440, 486, 400, 66),
     "quit": True},
]

for _item in MENU_ITEMS:
    make_zone(_item["key"], "menu", 10, TX[_item["name"]], _item["rect"],
              stand=(640, 690))

A = {}
_show_parts = [ap_showchar(), ap_scene("_entry_" + world.START_SCENE)]
_reset_parts = [ap_setcond(c, 1) for c in COND.values()]
_reset_parts += [ap_setvalue(v, 0, 0) for v in VAL.values()]
A["menu_nueva"] = add_action("Nueva partida", 7, _reset_parts + _show_parts)
A["menu_salir"] = add_action("Salir del juego", 7, [add_ap(55, "Salir")])
A["start_menu"] = add_action("Inicio del menú", 31,
                             [ap_setcond(COND["sin_haru_en_pausa"]),
                              ap_setcond(COND["en_menu"]),
                              ap_hidechar()])
OBJ_ACTION["menu_nueva"] = A["menu_nueva"]
OBJ_ACTION["menu_salir"] = A["menu_salir"]
A["ir_mapa"] = add_action("Ir al mapa", 7, [ap_scene("_entry_mapa")])


# ---------------------------------------------------------------------------
# Menú de pausa (clic derecho): capa condicional en cada escena
# ---------------------------------------------------------------------------
PAUSE_BUTTONS = [
    {"key": "pausa_continuar", "name": "n_continuar", "rect": (440, 330, 400, 64),
     "unset": ["pausa"]},
    {"key": "pausa_menu", "name": "n_menu", "rect": (440, 420, 400, 64),
     "unset": ["pausa"], "scene_to": "menu"},
    {"key": "pausa_salir", "name": "n_salir", "rect": (440, 510, 400, 64),
     "quit": True},
]

for _sc in world.SCENES:
    _pkey = "pausa_fondo_" + _sc["key"]
    make_zone(_pkey, _sc["key"], 950, None, (0, 0, 1280, 720),
              stand=(640, 690), cond="pausa")
    OBJ[_pkey]["sprite"] = add_sprite(
        MANIFEST["objects"]["pause"]["path"], 0, 0, "pause")
    OBJ[_pkey]["rect"] = (0, 0, 1280, 720)

    for _btn in PAUSE_BUTTONS:
        _key = _btn["key"] + "_" + _sc["key"]
        make_zone(_key, _sc["key"], 960, TX[_btn["name"]], _btn["rect"],
                  stand=(640, 720), cond="pausa")
        _parts = []
        for cname in _btn.get("unset", []):
            _parts.append(ap_setcond(COND[cname], 1))
        if _btn.get("unset") and _sc.get("pause_show_char", True):
            _parts.append(ap_showchar())
        if _btn.get("scene_to"):
            _parts.append(ap_scene("_entry_" + _btn["scene_to"]))
        if _btn.get("quit"):
            _parts.append(add_ap(55, "Salir"))
        OBJ_ACTION[_key] = add_action("Acción: " + _key, 7, _parts)

A["abrir_pausa"] = add_action("Abrir pausa", 7,
                             [ap_setcond(COND["pausa"]), ap_hidechar()])
# Cierra la pausa. Si la escena marca pause_show_char = False (la cinemática
# del castillo) no vuelve a mostrar a Haru, igual que el botón CONTINUAR.
A["cerrar_pausa"] = add_action("Cerrar pausa", 7,
                              [ap_if(COND["sin_haru_en_pausa"], False),
                               ap_showchar(), ap_endif(),
                               ap_setcond(COND["pausa"], 1)])


# ---------------------------------------------------------------------------
# Orden de dibujo.
# En Visionaire, un Object.order MENOR se dibuja DELANTE. En world.py el campo
# "order"/z significa lo contrario (mayor = delante), así que aquí lo traducimos
# a rangos de 0..N por escena: el z más alto recibe el order más bajo.
# ---------------------------------------------------------------------------
_rank = [0]
for _sc in world.SCENES + [{"key": "menu"}]:
    for _o in sorted([o for o in OBJ.values() if o["scene"] == _sc["key"]],
                     key=lambda o: (-o["z"], o["order"])):
        _o["order"] = _rank[0]
        _rank[0] += 1


# ---------------------------------------------------------------------------
# Acciones de inicio de escena
#
# Una escena puede definir en world.py:
#   start_texts      lista de claves de TEXTS que se muestran al entrar
#   cinematic        secuencia avanzada: claves de TEXTS y bloques
#                    {"set": "condición"} / {"unset": "condición"}
#   start_hide_char  oculta a Haru al entrar (cinemáticas)
#   start_show_char  vuelve a mostrarlo antes de cambiar de escena
#   start_scene_to   escena a la que se salta al terminar la secuencia
# ---------------------------------------------------------------------------
SCENE_START_ACTION = {}


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return list(v)


def _beat_parts(item):
    if isinstance(item, str):
        return [ap_text(TX[item], obj="dialog_box")]
    out = []
    if item.get("text"):
        out.append(ap_text(TX[item["text"]], obj="dialog_box"))
    for cname in _as_list(item.get("set")):
        out.append(ap_setcond(COND[cname]))
    for cname in _as_list(item.get("unset")):
        out.append(ap_setcond(COND[cname], 1))
    return out


def make_start_action(sc):
    scene_key = sc["key"]
    # "sin_haru_en_pausa": las escenas con pause_show_char = False no muestran
    # al personaje al cerrar el menú de pausa (cinemáticas).
    parts = []
    parts.append(ap_setcond(COND["en_menu"], 1))
    if sc.get("pause_show_char", True):
        parts.append(ap_setcond(COND["sin_haru_en_pausa"], 1))
    else:
        parts.append(ap_setcond(COND["sin_haru_en_pausa"]))
    if sc.get("start_hide_char"):
        parts.append(ap_hidechar())

    seq = sc.get("cinematic")
    if seq is None:
        seq = list(sc.get("start_texts", []))
    for item in seq:
        parts.extend(_beat_parts(item))

    if sc.get("start_show_char"):
        parts.append(ap_showchar())
    if sc.get("start_scene_to"):
        parts.append(ap_scene("_entry_" + sc["start_scene_to"]))

    if not parts:
        return None
    return add_action("Inicio: " + scene_key, 31, parts)


SCENE_START_ACTION["menu"] = A["start_menu"]
for _sc in world.SCENES:
    SCENE_START_ACTION[_sc["key"]] = make_start_action(_sc)


# ---------------------------------------------------------------------------
# Animaciones / personaje / cursor
# ---------------------------------------------------------------------------
def sprite_el(parent, path, x=0, y=0, tag="sprite"):
    s = ET.SubElement(parent, tag)
    s.set("name", "")
    s.set("pause", "-1")
    s.set("path", path)
    s.set("Transparency", "2")
    p = ET.SubElement(s, "position")
    p.set("x", str(x))
    p.set("y", str(y))
    return s


def make_anim(name, direction, sprite_paths, center, pause, mirror=None):
    i = nid("anim")
    animations.append({"id": i, "name": name, "dir": direction, "sprites": sprite_paths,
                       "center": center, "pause": pause, "mirror": mirror})
    return i


CUR_A = make_anim("cursor", -1, ["graphics/cursor_arrow.png"], (3, 2), 20)
CUR_B = make_anim("cursor_off", -1, ["graphics/cursor_arrow.png"], (3, 2), 20)
WALK_L = make_anim("walk_left", 180, MANIFEST["characters"]["walk"], (46, 205), 130)
WALK_R = make_anim("walk_right", 0, [], (46, 205), 130, mirror=WALK_L)
IDLE_L = make_anim("idle_left", 180, MANIFEST["characters"]["idle"], (46, 205), 900)
IDLE_R = make_anim("idle_right", 0, [], (46, 205), 900, mirror=IDLE_L)


# ---------------------------------------------------------------------------
# Construcción XML
# ---------------------------------------------------------------------------
root = ET.Element("VisionaireAdventure")
root.set("projectType", "-1")
root.set("revision", "-1")
root.set("version", "209")

game = ET.SubElement(root, "Game")
game.set("name", "Nagasaki 1641")
game.set("id", "1")
game.set("order", "1")
game.set("lastModified", "-1")
game.set("GameId", "1185")
for k in ["GameDescription", "GameAbout", "GameIntro", "GameReserved", "GameComposedFile",
          "GameSceneComposedFile", "GameCharacterComposedFile", "GameMovieComposedFile",
          "GameVersion", "GameCompanyName", "GameGameName", "GameVideoSubtitleLanguage",
          "GameVideoAudioLanguage", "GameSavegameScreenshot", "GameVideoPauseScreen",
          "GameIconFile", "GameBuildOptions", "GameSavegameScrollStep"]:
    game.set(k, "")
game.set("GameCommandBehaviour", "2")
game.set("GameFadeDelay", "600")
game.set("GameScrollSpeed", "300")
game.set("GameFullScreenIntro", "F")
game.set("GameDraggableItems", "F")
game.set("GameHoldTime", "600")
game.set("GameFadeEffect", "3")
game.set("GameMinificationFilter", "0")
game.set("GameMagnificationFilter", "0")
game.set("GameAutoHideInterfacesInMenu", "T")
game.set("GameAlwaysAllowSkipText", "T")
game.set("GameExecuteActionsDuringDialog", "F")
game.set("GameAlignCharacterOnImExecution", "F")
game.set("GameSceneComposedFiles", "0")
game.set("GameCharacterComposedFiles", "0")
game.set("GameMovieComposedFiles", "2")
game.set("GameDrawActionText", "2")
game.set("GameQuake", "F")
game.set("GameSpeakerTextAlignment", "0")
game.set("GameTextAlignment", "2")
game.set("GameKeepCharacterSpritesDuringMenus", "T")
game.set("GameDisableInteractionDuringAnim", "0")
game.set("GamePictureCacheSize", "40")
game.set("GameInterfaceComposedFiles", "0")
game.set("GameInterfaceComposedFile", "")
game.set("GameGameComposedFiles", "0")
game.set("GameGameComposedFile", "")
game.set("GameVideosEncrypted", "F")
game.set("GamePreloadPicThreads", "3")
game.set("GamePreloadedPicBufferSize", "16384")
game.set("GamePicBufferSize", "120000")
game.set("GamePreallocatedTextures", "-1")
game.set("GameNearestNeighborInterpolation", "F")
game.set("SpeakerSoundPanFactor", "8")
game.set("GameShowBlackScreenAfterVideo", "F")
game.set("GameLeftHoldBehaviour", "0")
game.set("GameMiddleClickBehaviour", "0")
game.set("GameRightClickBehaviour", "0")
game.set("GameExecuteCalledActionImmediately", "T")
game.set("GameSmoothScrolling", "F")
game.set("GameSaveNameOffsetY", "-1")
game.set("GameLeftClickBehaviour", "1")
game.set("GameMinimumTurnAngle", "30")
game.set("GameMinimumWalkTurnAngle", "60")
game.set("GameLimitFramerate", "0")
game.set("GameSkipTextTransitionFirst", "T")
game.set("GameMinDelayBetweenTextSkips", "0")
game.set("GameActivateMipmapping", "F")
game.set("GameActivateMultiresolution", "F")
game.set("GameCommentWithStandardCommand", "F")
game.set("GameDialogTextAlignment", "2")

ET.SubElement(game, "GameSceneLinks")
ET.SubElement(game, "GameCharacterLinks")
ET.SubElement(game, "GameInterfaces")
ET.SubElement(game, "GameFontLinks")
langs = ET.SubElement(game, "GameLanguages")
lang_link = ET.SubElement(langs, "Link")
lang_link.set("parentLink", "T")
lang_link.set("id", "0")
lang_link.set("tableId", str(T["languages"]))
lang_link.set("LinkAny", "F")
first_scene = ET.SubElement(game, "GameFirstScene")
first_scene.set("parentLink", "F")
first_scene.set("id", "0")
first_scene.set("tableId", str(T["scenes"]))
first_scene.set("LinkAny", "F")
ET.SubElement(game, "GameItems")
loading_link = ET.SubElement(game, "GameLoading")
loading_link.set("parentLink", "T")
loading_link.set("id", "0")
loading_link.set("tableId", "21")
loading_link.set("LinkAny", "F")
res = ET.SubElement(game, "GameWindowResolution")
res.set("x", "1280")
res.set("y", "720")
ET.SubElement(game, "GameCursors")
first_char = ET.SubElement(game, "GameFirstCharacter")
first_char.set("parentLink", "F")
first_char.set("id", str(CHAR_ID))
first_char.set("tableId", str(T["characters"]))
first_char.set("LinkAny", "F")
std_lang = ET.SubElement(game, "GameStandardLanguage")
std_lang.set("parentLink", "F")
std_lang.set("id", "0")
std_lang.set("tableId", str(T["languages"]))
std_lang.set("LinkAny", "F")
ET.SubElement(game, "GameActions")
for tag in ["GameStartAction", "GameLeftDblClickAction", "GameLeftHoldAction",
            "GameLeftHoldingAction"]:
    e = ET.SubElement(game, tag)
    e.set("parentLink", "F")
    e.set("id", "-1")
    e.set("tableId", "-1")
    e.set("LinkAny", "F")
right_click = ET.SubElement(game, "GameRightClickAction")
right_click.set("parentLink", "T")
right_click.set("id", str(A["abrir_pausa"]))
right_click.set("tableId", str(T["actions"]))
right_click.set("LinkAny", "F")
ET.SubElement(game, "GameParticleContainerLinks")
left_click = ET.SubElement(game, "GameLeftClickAction")
left_click.set("parentLink", "F")
left_click.set("id", "-1")
left_click.set("tableId", "-1")
left_click.set("LinkAny", "F")
font_link = ET.SubElement(game, "GameActionTextFont")
font_link.set("parentLink", "F")
font_link.set("id", "0")
font_link.set("tableId", str(T["fonts"]))
font_link.set("LinkAny", "F")
rect = ET.SubElement(game, "GameActionTextRect")
# Cuadro de dialogo: centrado horizontalmente, anclado en la parte baja de la
# pantalla (game 1280x720), para no tapar la visibilidad del escenario.
rect.set("top", "440")
rect.set("left", "140")
rect.set("bottom", "700")
rect.set("right", "1140")
script_links = ET.SubElement(game, "GameScriptLinks")
l = ET.SubElement(script_links, "Link")
l.set("parentLink", "T")
l.set("id", "0")
l.set("tableId", str(T["scripts"]))
l.set("LinkAny", "F")
classes = ET.SubElement(game, "GameInterfaceClasses")
for i in range(5):
    l = ET.SubElement(classes, "Link")
    l.set("parentLink", "T")
    l.set("id", str(i))
    l.set("tableId", str(T["interfaceclasses"]))
    l.set("LinkAny", "F")
obj_font = ET.SubElement(game, "GameObjectFont")
obj_font.set("parentLink", "F")
obj_font.set("id", "0")
obj_font.set("tableId", str(T["fonts"]))
obj_font.set("LinkAny", "F")
for tag in ["GameVideoSubtitleFont", "GameMiddleClickAction", "GameMouseWheelUpAction",
            "GameMouseWheelDownAction", "GameDefaultSpeechBus", "GameDefaultSoundBus",
            "GameWalksoundBus", "GameDefaultMusicBus", "GameWaitCursor", "GameDefaultMovieBus"]:
    e = ET.SubElement(game, tag)
    e.set("parentLink", "F")
    e.set("id", "-1")
    e.set("tableId", "-1")
    e.set("LinkAny", "F")
sub_pos = ET.SubElement(game, "GameVideoSubtitlePosition")
sub_pos.set("x", "-1")
sub_pos.set("y", "-1")
ET.SubElement(game, "GameContainers")
ET.SubElement(game, "GameBuildRules")
ET.SubElement(game, "GameShaderLinks")
ET.SubElement(game, "GameAudioMixLinks")
ET.SubElement(game, "GameAudioContainerLinks")
ET.SubElement(game, "GameCustomActionParts")
ET.SubElement(game, "GamePlugins")
ET.SubElement(game, "GameBlockContainers")
ET.SubElement(game, "GameBehaviours")
ET.SubElement(game, "GameAdditionalFolders")
ET.SubElement(game, "GameConfigConditions")
ET.SubElement(game, "GameConfigValues")
a_off = ET.SubElement(game, "GameActionTextOffset")
a_off.set("x", "-1")
a_off.set("y", "-1")
cursor_link = ET.SubElement(game, "GameCursor")
cursor_link.set("parentLink", "F")
cursor_link.set("id", "0")
cursor_link.set("tableId", str(T["cursors"]))
cursor_link.set("LinkAny", "F")

# --- Loadings
loadings = ET.SubElement(root, "Loadings")
loadings.set("newId", "1")
loadings.set("versionedId", "-1")
loadings.set("tableId", "21")
ld = ET.SubElement(loadings, "Loading")
ld.set("name", "Cargando")
ld.set("id", "0")
ld.set("order", "0")
ld.set("lastModified", "-1")
ld.set("LoadingMusic", "")
ld.set("LoadingStatusCover", "F")
for sp in ("LoadingSprite", "LoadingStatusSprite"):
    e = ET.SubElement(ld, sp)
    e.set("name", "")
    e.set("pause", "-1")
    e.set("path", "")
    e.set("Transparency", "2")
    p = ET.SubElement(e, "position")
    p.set("x", "0")
    p.set("y", "0")

# --- Characters
chars = ET.SubElement(root, "Characters")
chars.set("newId", str(CHAR_ID + 1))
chars.set("versionedId", "-1")
chars.set("tableId", str(T["characters"]))
ch = ET.SubElement(chars, "Character")
ch.set("name", "Haru")
ch.set("id", str(CHAR_ID))
ch.set("order", str(CHAR_ID))
ch.set("lastModified", "-1")
ch.set("CharacterWalkingSound", "")
ch.set("CharacterScale", "T")
ch.set("CharacterDialogVerticalSpace", "10")
ch.set("CharacterScaleFactor", "100")
ch.set("CharacterHarmonizeWalkAnimations", "F")
nm = ET.SubElement(ch, "CharacterName")
nm.set("parentLink", "T")
nm.set("id", str(TX["haru"]))
nm.set("tableId", str(T["texts"]))
nm.set("LinkAny", "F")
ET.SubElement(ch, "CharacterInterfaces")
f = ET.SubElement(ch, "CharacterFont")
f.set("parentLink", "F")
f.set("id", "0")
f.set("tableId", str(T["fonts"]))
f.set("LinkAny", "F")
outfit_link = ET.SubElement(ch, "CharacterCurrentOutfit")
outfit_link.set("parentLink", "F")
outfit_link.set("id", "0")
outfit_link.set("tableId", str(T["outfits"]))
outfit_link.set("LinkAny", "F")
for tag in ["CharacterCurrentCommentSet", "CharacterDialogCursor"]:
    e = ET.SubElement(ch, tag)
    e.set("parentLink", "F")
    e.set("id", "-1")
    e.set("tableId", "-1")
    e.set("LinkAny", "F")
ET.SubElement(ch, "CharacterDialogs")
ET.SubElement(ch, "CharacterActions")
outs = ET.SubElement(ch, "CharacterOutfits")
l = ET.SubElement(outs, "Link")
l.set("parentLink", "T")
l.set("id", "0")
l.set("tableId", str(T["outfits"]))
l.set("LinkAny", "F")
ET.SubElement(ch, "CharacterCommentSets")
start = ET.SubElement(ch, "CharacterStartObject")
start.set("parentLink", "F")
start.set("id", str(OBJ["_entry_" + world.START_SCENE]["id"]))
start.set("tableId", str(T["objects"]))
start.set("LinkAny", "F")
ET.SubElement(ch, "CharacterValues")
ET.SubElement(ch, "CharacterConditions")
for tag in ["CharacterActiveDialogFont", "CharacterInactiveDialogFont"]:
    e = ET.SubElement(ch, tag)
    e.set("parentLink", "F")
    e.set("id", "-1")
    e.set("tableId", "-1")
    e.set("LinkAny", "F")
area = ET.SubElement(ch, "CharacterDialogArea")
# Mismo cuadro que el de action text: centrado abajo del todo del escenario
# (game 1280x720: x=140..1140, y=440..700). Evita que el dialogo salga por
# encima de la cabeza del personaje.
for k, v in {"top": "440", "left": "140", "bottom": "700", "right": "1140"}.items():
    area.set(k, v)
for tag in ["CharacterDialogActiveScrollUp", "CharacterDialogInactiveScrollUp",
            "CharacterDialogActiveScrollDown", "CharacterDialogInactiveScrollDown",
            "CharacterDialogSprite"]:
    e = ET.SubElement(ch, tag)
    e.set("name", "")
    e.set("pause", "-1")
    e.set("path", "")
    e.set("Transparency", "2")
    p = ET.SubElement(e, "position")
    p.set("x", "0")
    p.set("y", "0")
pos = ET.SubElement(ch, "CharacterActionDestPosition")
pos.set("x", "-1")
pos.set("y", "-1")
bus = ET.SubElement(ch, "CharacterAudioBus")
bus.set("parentLink", "F")
bus.set("id", "-1")
bus.set("tableId", "-1")
bus.set("LinkAny", "F")
ET.SubElement(ch, "CharacterComponents")
# El editor escribe estos nodos al final del personaje, en este orden exacto;
# si faltan o van descolocados, el personaje no aparece en la lista de Characters.
for tag in ["CharacterActiveUsedDialogFont", "CharacterInactiveUsedDialogFont",
            "CharacterStartScene"]:
    e = ET.SubElement(ch, tag)
    e.set("parentLink", "F")
    e.set("id", "-1")
    e.set("tableId", "-1")
    e.set("LinkAny", "F")
e = ET.SubElement(ch, "CharacterStartPos")
e.set("x", "0")
e.set("y", "0")
e = ET.SubElement(ch, "CharacterSnoopAnimation")
e.set("parentLink", "F")
e.set("id", "-1")
e.set("tableId", "-1")
e.set("LinkAny", "F")
e = ET.SubElement(ch, "CharacterSnoopAnimationOffsetPos")
e.set("x", "0")
e.set("y", "0")

# --- Narrador: personaje invisible para textos de cinematica (cuadro superior)
import copy as _copy
_nar = _copy.deepcopy(ch)
_nar.set("name", "Narrador")
_nar.set("id", str(NARRATOR_ID))
_nar.set("order", str(NARRATOR_ID))
# No depende de ningun objeto de escena (entry): puede mostrar texto sin personaje.
_sobj = _nar.find("CharacterStartObject")
_sobj.set("id", "-1")
_sobj.set("tableId", "-1")
_spos = _nar.find("CharacterStartPos")
_spos.set("x", "640")
_spos.set("y", "60")
_sscene = _nar.find("CharacterStartScene")
_sscene.set("id", "0")
_sscene.set("tableId", str(T["scenes"]))
_narea = _nar.find("CharacterDialogArea")
for _k, _v in {"top": "10", "left": "140", "bottom": "120", "right": "1140"}.items():
    _narea.set(_k, _v)
chars.append(_nar)
chars.set("newId", str(NARRATOR_ID + 1))

# enlazar el narrador en el juego (no es jugable, pero se necesita para textos)
_gl = game.find("GameCharacterLinks")
_nl = ET.SubElement(_gl, "Link")
_nl.set("parentLink", "T")
_nl.set("id", str(NARRATOR_ID))
_nl.set("tableId", "0")
_nl.set("LinkAny", "F")

# --- Interfaces / Buttons vacíos
for tag, table in (("Interfaces", T["interfaces"]), ("Buttons", T["buttons"])):
    e = ET.SubElement(root, tag)
    e.set("newId", "0")
    e.set("versionedId", "-1")
    e.set("tableId", str(table))

# --- Fonts
fonts = ET.SubElement(root, "Fonts")
fonts.set("newId", "1")
fonts.set("versionedId", "-1")
fonts.set("tableId", str(T["fonts"]))
fo = ET.SubElement(fonts, "Font")
fo.set("name", "Noto")
fo.set("id", "0")
fo.set("order", "0")
fo.set("lastModified", "-1")
fo.set("FontAlphabet", ALPHABET)
fo.set("FontLetterSpacing", "0")
fo.set("VerticalLetterSpacing", "3")
fo.set("FontSpaceWidth", "10")
fo.set("FontAutoLineBreak", "T")
fo.set("FontLineWidth", "640")
fo.set("FontKerning", "")
fo.set("FontTrueTypeFont", "T")
fo.set("FontTrueTypeFontPath", FONT_PATH)
fo.set("FontSize", "24.000000")
fo.set("FontColor", "16777215")
fo.set("FontBorder", "T")
fo.set("FontBorderColor", "0")
fo.set("FontBorderSize", "2.000000")
fo.set("FontShadow", "F")
fs = ET.SubElement(fo, "FontSprite")
fs.set("name", "")
fs.set("pause", "-1")
fs.set("path", "")
fs.set("Transparency", "2")
p = ET.SubElement(fs, "position")
p.set("x", "0")
p.set("y", "0")
ET.SubElement(fo, "FontLetters")
ff = ET.SubElement(fo, "FontFont")
ff.set("parentLink", "F")
ff.set("id", "-1")
ff.set("tableId", "-1")
ff.set("LinkAny", "F")
so = ET.SubElement(fo, "FontShadowOffset")
so.set("x", "1")
so.set("y", "1")

# --- Scenes
WAY_DEFS = {"menu": [(0, 640), (1280, 640), (1280, 714), (0, 714)]}
MUSIC = {"menu": "audio/menu.ogg"}
scene_defs = [("menu", "bg_menu", "Menú principal", SCENE_START_ACTION["menu"])]
for _sc in world.SCENES:
    WAY_DEFS[_sc["key"]] = _sc["way"]
    MUSIC[_sc["key"]] = _sc["music"]
    scene_defs.append((_sc["key"], _sc["bg"], _sc["name"],
                       SCENE_START_ACTION[_sc["key"]]))
WAY_ID = {key: i for i, key in enumerate(WAY_DEFS)}
scenes_container = ET.SubElement(root, "Scenes")
scenes_container.set("newId", str(len(scene_defs)))
scenes_container.set("versionedId", "-1")
scenes_container.set("tableId", str(T["scenes"]))
for sid, (key, bg, name, start_action) in enumerate(scene_defs):
    sc = ET.SubElement(scenes_container, "Scene")
    sc.set("name", key)
    sc.set("id", str(sid))
    sc.set("order", str(sid))
    sc.set("lastModified", "-1")
    sc.set("SceneBackgroundMusic", MUSIC[key])
    sc.set("SceneContinueMusic", "F")
    sc.set("CDTrack", "-1")
    sc.set("SceneMusicVolume", "-8")
    sc.set("SceneMusicBalance", "0")
    sc.set("SceneScrollOnEdges", "F")
    sc.set("SceneIsMenu", "T" if key == "menu" else "F")
    sc.set("SceneSavegameScrollStep", "1")
    sc.set("SceneLightMap", "")
    sc.set("SceneSavegameScreenshot", "")
    spr = ET.SubElement(sc, "SceneSprite")
    spr.set("name", "")
    spr.set("pause", "-1")
    spr.set("path", f"graphics/{bg}.png")
    spr.set("Transparency", "2")
    p = ET.SubElement(spr, "position")
    p.set("x", "0")
    p.set("y", "0")
    sn = ET.SubElement(sc, "SceneName")
    sn.set("parentLink", "T")
    sn.set("id", str(SCENE_NAME[key]))
    sn.set("tableId", str(T["texts"]))
    sn.set("LinkAny", "F")
    objs = ET.SubElement(sc, "SceneObjects")
    for o in sorted([o for o in OBJ.values() if o["scene"] == key], key=lambda x: x["z"]):
        l = ET.SubElement(objs, "Link")
        l.set("parentLink", "T")
        l.set("id", str(o["id"]))
        l.set("tableId", str(T["objects"]))
        l.set("LinkAny", "F")
    cur = ET.SubElement(sc, "SceneCursor")
    cur.set("parentLink", "F")
    cur.set("id", "-1")
    cur.set("tableId", "-1")
    cur.set("LinkAny", "F")
    ET.SubElement(sc, "SceneSavegameAreas")
    ET.SubElement(sc, "SceneValues")
    ET.SubElement(sc, "SceneConditions")
    acts = ET.SubElement(sc, "SceneActions")
    if start_action is not None:
        l = ET.SubElement(acts, "Link")
        l.set("parentLink", "T")
        l.set("id", str(start_action))
        l.set("tableId", str(T["actions"]))
        l.set("LinkAny", "F")
    way_id = str(WAY_ID[key])
    ways_el = ET.SubElement(sc, "SceneWaySystems")
    l = ET.SubElement(ways_el, "Link")
    l.set("parentLink", "T")
    l.set("id", way_id)
    l.set("tableId", str(T["waysystems"]))
    l.set("LinkAny", "F")
    for tag in ["SceneSavegameFont", "SceneParticleSystem", "SceneTestCharacter"]:
        e = ET.SubElement(sc, tag)
        e.set("parentLink", "F")
        e.set("id", "-1")
        e.set("tableId", "-1")
        e.set("LinkAny", "F")
    cur_way = ET.SubElement(sc, "SceneCurrentWaySystem")
    cur_way.set("parentLink", "F")
    cur_way.set("id", way_id)
    cur_way.set("tableId", str(T["waysystems"]))
    cur_way.set("LinkAny", "F")
    area = ET.SubElement(sc, "SceneScrollableArea")
    for k, v in {"top": "0", "left": "0", "bottom": "-1", "right": "-1"}.items():
        area.set(k, v)
    ET.SubElement(sc, "SceneActionAreas")
    ET.SubElement(sc, "SceneAudioBusses")
    ET.SubElement(sc, "SceneCurves")
    ET.SubElement(sc, "SceneComponents")

# --- WaySystems (zonas de suelo transitables)
ways_container = ET.SubElement(root, "WaySystems")
ways_container.set("newId", str(len(WAY_DEFS)))
ways_container.set("versionedId", "-1")
ways_container.set("tableId", str(T["waysystems"]))
for key, pts in WAY_DEFS.items():
    ws = ET.SubElement(ways_container, "WaySystem")
    ws.set("name", key)
    ws.set("id", str(WAY_ID[key]))
    ws.set("order", str(WAY_ID[key]))
    ws.set("lastModified", "-1")
    border = ET.SubElement(ws, "WaySystemBorder")
    for x, y in pts:
        p = ET.SubElement(border, "point")
        p.set("x", str(x))
        p.set("y", str(y))
    ET.SubElement(ws, "WaySystemPoints")

# --- tablas vacías intermedias
for tag, table, newid in (("Points", T["points"], 0), ("Dialogs", T["dialogs"], 0),
                          ("DialogParts", T["dialogparts"], 0), ("CommentSets", T["commentsets"], 0)):
    e = ET.SubElement(root, tag)
    e.set("newId", str(newid))
    e.set("versionedId", "-1")
    e.set("tableId", str(table))

# --- Objects
objects_container = ET.SubElement(root, "Objects")
objects_container.set("newId", str(len(OBJ)))
objects_container.set("versionedId", "-1")
objects_container.set("tableId", str(T["objects"]))
for key, o in OBJ.items():
    ob = ET.SubElement(objects_container, "Object")
    ob.set("name", key)
    ob.set("id", str(o["id"]))
    ob.set("order", str(o["order"]))
    ob.set("lastModified", "-1")
    ob.set("ObjectDirection", "-1")
    ob.set("ObjectCenter", "-1")
    ob.set("ObjectIsItem", "F")
    ob.set("ObjectConditionNegate", "T" if o["negate"] else "F")
    ob.set("ObjectIsWalkable", o["walkable"])
    ob.set("ObjectScrollFactorX", "100")
    ob.set("ObjectScrollFactorY", "100")
    ob.set("ObjectModel", "")
    ob.set("ObjectValueOperator", "0")
    ob.set("ObjectValueInt", "0")
    ob.set("ObjectLightmapAffected", "F")
    if o["name"] is not None:
        nm = ET.SubElement(ob, "ObjectName")
        nm.set("parentLink", "T")
        nm.set("id", str(o["name"]))
        nm.set("tableId", str(T["texts"]))
        nm.set("LinkAny", "F")
    else:
        nm = ET.SubElement(ob, "ObjectName")
        nm.set("parentLink", "F")
        nm.set("id", "-1")
        nm.set("tableId", "-1")
        nm.set("LinkAny", "F")
    poly = ET.SubElement(ob, "ObjectPolygon")
    if o.get("rect"):
        x, y, w, h = o["rect"]
        for px, py in ((x + 2, y + 2), (x + w - 2, y + 2),
                       (x + w - 2, y + h - 2), (x + 2, y + h - 2)):
            pt = ET.SubElement(poly, "point")
            pt.set("x", str(px))
            pt.set("y", str(py))
    cond = ET.SubElement(ob, "ObjectCondition")
    if o["cond"] is not None:
        cond.set("parentLink", "F")
        cond.set("id", str(o["cond"]))
        cond.set("tableId", str(T["conditions"]))
    else:
        cond.set("parentLink", "F")
        cond.set("id", "-1")
        cond.set("tableId", "-1")
    cond.set("LinkAny", "F")
    spr = ET.SubElement(ob, "ObjectSprite")
    if o["sprite"] is not None:
        spr.set("parentLink", "T")
        spr.set("id", str(o["sprite"]))
        spr.set("tableId", str(T["sprites"]))
    else:
        spr.set("parentLink", "F")
        spr.set("id", "-1")
        spr.set("tableId", "-1")
    spr.set("LinkAny", "F")
    for tag in ["ObjectAnimation", "ObjectSnoopAnimation"]:
        e = ET.SubElement(ob, tag)
        e.set("parentLink", "F")
        e.set("id", "-1")
        e.set("tableId", "-1")
        e.set("LinkAny", "F")
    acts = ET.SubElement(ob, "ObjectActions")
    if key in OBJ_ACTION:
        l = ET.SubElement(acts, "Link")
        l.set("parentLink", "T")
        l.set("id", str(OBJ_ACTION[key]))
        l.set("tableId", str(T["actions"]))
        l.set("LinkAny", "F")
    conds = ET.SubElement(ob, "ObjectConditions")
    if o["cond"] is not None:
        l = ET.SubElement(conds, "Link")
        l.set("parentLink", "T")
        l.set("id", str(o["cond"]))
        l.set("tableId", str(T["conditions"]))
        l.set("LinkAny", "F")
    ET.SubElement(ob, "ObjectAnimations")
    ET.SubElement(ob, "ObjectValues")
    pos = ET.SubElement(ob, "ObjectPosition")
    pos.set("x", str(o["stand"][0]))
    pos.set("y", str(o["stand"][1]))
    sp = ET.SubElement(ob, "ObjectSnoopAnimationPos")
    sp.set("x", "0")
    sp.set("y", "0")
    val = ET.SubElement(ob, "ObjectValue")
    val.set("parentLink", "F")
    val.set("id", "-1")
    val.set("tableId", "-1")
    val.set("LinkAny", "F")
    ET.SubElement(ob, "ObjectComponents")

# --- Actions
actions_container = ET.SubElement(root, "Actions")
actions_container.set("newId", str(len(actions)))
actions_container.set("versionedId", "-1")
actions_container.set("tableId", str(T["actions"]))
for a in actions:
    ac = ET.SubElement(actions_container, "Action")
    ac.set("name", a["name"])
    ac.set("id", str(a["id"]))
    ac.set("order", str(a["id"]))
    ac.set("lastModified", "-1")
    ac.set("ActionExecutionType", str(a["exec"]))
    fx = ET.SubElement(ac, "ActionFixture")
    fx.set("parentLink", "F")
    fx.set("id", "-1")
    fx.set("tableId", "-1")
    fx.set("LinkAny", "F")
    cm = ET.SubElement(ac, "ActionCommand")
    cm.set("parentLink", "F")
    cm.set("id", "-1")
    cm.set("tableId", "-1")
    cm.set("LinkAny", "F")
    parts = ET.SubElement(ac, "ActionActionParts")
    for pid in a["parts"]:
        l = ET.SubElement(parts, "Link")
        l.set("parentLink", "T")
        l.set("id", str(pid))
        l.set("tableId", str(T["actionparts"]))
        l.set("LinkAny", "F")

# --- ActionParts
aps_container = ET.SubElement(root, "ActionParts")
aps_container.set("newId", str(len(aps)))
aps_container.set("versionedId", "-1")
aps_container.set("tableId", str(T["actionparts"]))
for ap in aps:
    e = ET.SubElement(aps_container, "ActionPart")
    e.set("name", ap["name"])
    e.set("id", str(ap["id"]))
    e.set("order", str(ap["order"]))
    e.set("lastModified", "-1")
    e.set("ActionPartCommand", str(ap["cmd"]))
    e.set("ActionPartPath", "")
    e.set("ActionPartInt", str(ap["i1"]))
    e.set("ActionPartAltInt", str(ap["i2"]))
    e.set("ActionPartAltInt2", str(ap["i3"]))
    e.set("ActionPartString", "")
    e.set("ActionPartDisabled", "F")
    l1 = ET.SubElement(e, "ActionPartLink")
    # parentLink="T" marca el objeto enlazado como *hijo* del ActionPart: el
    # editor lo saca de su lista (p. ej. el personaje desaparece de Characters).
    # Los enlaces de un ActionPart solo referencian objetos, asi que van en "F".
    if ap["l1"]:
        l1.set("parentLink", "F")
        l1.set("id", str(ap["l1"][1]))
        l1.set("tableId", str(ap["l1"][0]))
    else:
        l1.set("parentLink", "F")
        l1.set("id", "-1")
        l1.set("tableId", "-1")
    l1.set("LinkAny", "F")
    l2 = ET.SubElement(e, "ActionPartAltLink")
    if ap["l2"]:
        l2.set("parentLink", "F")
        l2.set("id", str(ap["l2"][1]))
        l2.set("tableId", str(ap["l2"][0]))
    else:
        l2.set("parentLink", "F")
        l2.set("id", "-1")
        l2.set("tableId", "-1")
    l2.set("LinkAny", "F")

# --- Animations
anims_container = ET.SubElement(root, "Animations")
anims_container.set("newId", str(len(animations)))
anims_container.set("versionedId", "-1")
anims_container.set("tableId", str(T["animations"]))
for a in animations:
    e = ET.SubElement(anims_container, "Animation")
    e.set("name", a["name"])
    e.set("id", str(a["id"]))
    e.set("order", str(a["id"]))
    e.set("lastModified", "-1")
    e.set("AnimationLoopRandom", "F")
    e.set("AnimationNumberOfLoops", "0" if a["name"].startswith("walk") else "1")
    e.set("AnimationPause", str(a["pause"]))
    e.set("AnimationDirection", str(a["dir"]))
    e.set("AnimationMove", "F")
    e.set("AnimationUseIndividualPause", "F")
    e.set("AnimationReplay", "0")
    e.set("AnimationModelAnimIndex", "-1")
    e.set("AnimationModelAnimSpeed", "-1")
    e.set("AnimationModelFile", "")
    e.set("AnimationModelName", "")
    e.set("AnimationEndDirection", "-1")
    p = ET.SubElement(e, "AnimationPosition")
    p.set("x", "0")
    p.set("y", "0")
    act = ET.SubElement(e, "AnimationAction")
    act.set("parentLink", "F")
    act.set("id", "-1")
    act.set("tableId", "-1")
    act.set("LinkAny", "F")
    sprites_el = ET.SubElement(e, "AnimationSprites")
    for path in a["sprites"]:
        sprite_el(sprites_el, path)
    mir = ET.SubElement(e, "AnimationMirror")
    if a["mirror"] is not None:
        mir.set("parentLink", "T")
        mir.set("id", str(a["mirror"]))
        mir.set("tableId", str(T["animations"]))
    else:
        mir.set("parentLink", "F")
        mir.set("id", "-1")
        mir.set("tableId", "-1")
    mir.set("LinkAny", "F")
    c = ET.SubElement(e, "AnimationCenter")
    c.set("x", str(a["center"][0]))
    c.set("y", str(a["center"][1]))
    ET.SubElement(e, "AnimationPropertyFrames")
    ET.SubElement(e, "AnimationWalkSteps")
    ET.SubElement(e, "AnimationPauses")

# --- Conditions
conds_container = ET.SubElement(root, "Conditions")
conds_container.set("newId", str(len(conditions)))
conds_container.set("versionedId", "-1")
conds_container.set("tableId", str(T["conditions"]))
for c in conditions:
    e = ET.SubElement(conds_container, "Condition")
    e.set("name", c["name"])
    e.set("id", str(c["id"]))
    e.set("order", str(c["id"]))
    e.set("lastModified", "-1")
    e.set("ConditionIsVariable", "T")
    e.set("ConditionValue", "T" if c["value"] else "F")
    e.set("ConditionReturnNegate", "F")
    e.set("ConditionOperator", "0")
    ET.SubElement(e, "ConditionConditions")

# --- Sprites
sprites_container = ET.SubElement(root, "Sprites")
sprites_container.set("newId", str(len(sprites)))
sprites_container.set("versionedId", "-1")
sprites_container.set("tableId", str(T["sprites"]))
for s in sprites:
    e = ET.SubElement(sprites_container, "Sprite")
    e.set("name", s["name"])
    e.set("id", str(s["id"]))
    e.set("order", str(s["id"]))
    e.set("lastModified", "-1")
    sprite_el(e, s["path"], s["x"], s["y"], tag="SpriteSprite")

# --- Texts
texts_container = ET.SubElement(root, "Texts")
texts_container.set("newId", str(len(texts)))
texts_container.set("versionedId", "-1")
texts_container.set("tableId", str(T["texts"]))
for t in texts:
    e = ET.SubElement(texts_container, "Text")
    e.set("name", t["name"])
    e.set("id", str(t["id"]))
    e.set("order", str(t["id"]))
    e.set("lastModified", "-1")
    tl = ET.SubElement(e, "TextTextLanguages")
    te = ET.SubElement(tl, "text")
    te.set("Text", t["text"])
    te.set("path", "")
    te.set("int", "0")

# --- Cursors
cursors = ET.SubElement(root, "Cursors")
cursors.set("newId", "1")
cursors.set("versionedId", "-1")
cursors.set("tableId", str(T["cursors"]))
e = ET.SubElement(cursors, "Cursor")
e.set("name", "Flecha")
e.set("id", "0")
e.set("order", "0")
e.set("lastModified", "-1")
for tag, anim in (("CursorActiveAnimation", CUR_A), ("CursorInactiveAnimation", CUR_B)):
    l = ET.SubElement(e, tag)
    l.set("parentLink", "T")
    l.set("id", str(anim))
    l.set("tableId", str(T["animations"]))
    l.set("LinkAny", "F")

# --- Outfits
outfits = ET.SubElement(root, "Outfits")
outfits.set("newId", "1")
outfits.set("versionedId", "-1")
outfits.set("tableId", str(T["outfits"]))
o = ET.SubElement(outfits, "Outfit")
o.set("name", "Haru")
o.set("id", "0")
o.set("order", "0")
o.set("lastModified", "-1")
o.set("OutfitCharacterSpeed", "300")
o.set("OutfitModel", "")
o.set("OutfitCameraHeight", "0")
o.set("OutfitCameraAngle", "0")
o.set("OutfitUseLight", "F")
o.set("OutfitLightPosX", "1.000000")
o.set("OutfitLightPosY", "1.000000")
o.set("OutfitLightPosZ", "1.000000")
o.set("OutfitLightColor", "9345433")
o.set("OutfitModelScaleFactor", "100")
o.set("OutfitModelUseToonShading", "F")
o.set("OutfitModelToonNuances", "3")
o.set("OutfitModelShowOutline", "F")
o.set("OutfitModelOutlineColor", "0")
o.set("OutfitModelOutlineWidth", "5")
o.set("OutfitAmbientLightColor", "6717311")
o.set("OutfitModelShadowVisibility", "50")
o.set("OutfitRandomMinTime", "10000")
o.set("OutfitRandomMaxTime", "30000")
o.set("OutfitModelShadow", "2")
o.set("OutfitModelAmbientOcclusion", "50")
o.set("OutfitSlideWalkAnimation", "T")
o.set("OutfitModelTurnSpeed", "100")
for tag, ids in (("OutfitWalkAnimations", [WALK_L, WALK_R]), ("OutfitTalkAnimations", []),
                 ("OutfitRandomAnimations", []), ("OutfitCharacterAnimations", []),
                 ("OutfitStandingAnimations", [IDLE_L, IDLE_R])):
    e = ET.SubElement(o, tag)
    for aid in ids:
        l = ET.SubElement(e, "Link")
        l.set("parentLink", "T")
        l.set("id", str(aid))
        l.set("tableId", str(T["animations"]))
        l.set("LinkAny", "F")
ET.SubElement(o, "OutfitModelTextures")
ET.SubElement(o, "OutfitModelFiles")
ET.SubElement(o, "OutfitTurnAnimations")

# --- Languages
langs = ET.SubElement(root, "Languages")
langs.set("newId", "1")
langs.set("versionedId", "-1")
langs.set("tableId", str(T["languages"]))
e = ET.SubElement(langs, "Language")
e.set("name", "Español")
e.set("id", "0")
e.set("order", "0")
e.set("lastModified", "-1")

# --- Values
vals = ET.SubElement(root, "Values")
vals.set("newId", str(len(values)))
vals.set("versionedId", "-1")
vals.set("tableId", str(T["values"]))
for v in values:
    e = ET.SubElement(vals, "Value")
    e.set("name", v["name"])
    e.set("id", str(v["id"]))
    e.set("order", str(v["id"]))
    e.set("lastModified", "-1")
    e.set("ValueInt", str(v["value"]))
    e.set("ValueRandom", "F")
    e.set("ValueRandomMin", "-1")
    e.set("ValueRandomMax", "-1")
    e.set("ValueString", "")
    e.set("ValueFloat", f"{float(v['value']):.6f}")

# --- Scripts (cursor dibujado por el juego)
CURSOR_SCRIPT = """local cursorSprite = nil

-- Autoavance de los diálogos: cada texto dura en pantalla según su longitud
-- (y se puede saltar con un clic, como siempre).
function nagasakiTextStarted(text)
  local body = text and text.CurrentText or ""
  if text then
    local dur = 1300 + #body * 28
    if dur > 5200 then dur = 5200 end
    if dur < 1500 then dur = 1500 end
    text.TimeToWait = dur
  end
end

registerEventHandler("textStarted", "nagasakiTextStarted")

function nagasakiCursor()
  if not cursorSprite then
    cursorSprite = graphics.loadFromFile("vispath:graphics/cursor_arrow.png")
  end
  if cursorSprite then
    local p = getCursorPos()
    cursorSprite.position = {x = p.x - 8, y = p.y - 6}
    graphics.drawSprite(cursorSprite, 1.0)
  end
end

graphics.addDrawFunc("nagasakiCursor()", 1)"""

# --- Teclado: ESC abre y cierra el menú de pausa ---------------------------
KEY_SCRIPT = """-- ESC: abrir / cerrar el menú de pausa
-- TAB: abrir el mapa
function nagasakiKeyHandler(eventType, character, keycode, modifiers)
  if keycode == eKeyTab and eventType == eEvtKeyDown then
    local enMenu = Conditions["en_menu"] and Conditions["en_menu"].Value
    if enMenu then return false end
    local pv = Conditions["pausa"] and Conditions["pausa"].Value
    if pv then return false end
    startAction(Actions["Ir al mapa"])
    return true
  end
  if keycode == eKeyEscape and eventType == eEvtKeyDown then
    local enMenu = Conditions["en_menu"] and Conditions["en_menu"].Value
    if enMenu then return false end
    local pv = Conditions["pausa"] and Conditions["pausa"].Value
    if pv then
      startAction(Actions["Cerrar pausa"])
    else
      startAction(Actions["Abrir pausa"])
    end
    return true
  end
  return false
end

registerEventHandler("keyEvent", "nagasakiKeyHandler")"""

CURSOR_SCRIPT = CURSOR_SCRIPT + "\n\n" + KEY_SCRIPT

scripts_container = ET.SubElement(root, "Scripts")
scripts_container.set("newId", "1")
scripts_container.set("versionedId", "-1")
scripts_container.set("tableId", str(T["scripts"]))
sc_el = ET.SubElement(scripts_container, "Script")
sc_el.set("name", "Cursor visible")
sc_el.set("id", "0")
sc_el.set("order", "0")
sc_el.set("lastModified", "-1")
sc_el.set("ScriptScript", CURSOR_SCRIPT.replace("\n", "<br/>"))
sc_el.set("ScriptType", "1")

# --- tablas vacías restantes
for tag, table in (("Particles", 22), ("ParticleContainers", 23), ("CommentSetEntries", 27),
                   ("AnimationFrames", 28), ("ActionAreas", 32), ("AreaActions", 33),
                   ("Shaders", 36), ("AudioBusses", 37), ("Events", 38), ("Plugins", 39),
                   ("BlockContainers", 40), ("Blocks", 41), ("Curves", 42), ("Components", 43)):
    e = ET.SubElement(root, tag)
    e.set("newId", "0")
    e.set("versionedId", "-1")
    e.set("tableId", str(table))

# --- InterfaceClasses
ic = ET.SubElement(root, "InterfaceClasses")
ic.set("newId", "5")
ic.set("versionedId", "-1")
ic.set("tableId", str(T["interfaceclasses"]))
for i, name in enumerate(["MainInterface", "Inventory", "SecondaryInterface",
                          "OptionsInterface", "Miscellaneous"]):
    e = ET.SubElement(ic, "InterfaceClass")
    e.set("name", "Unnamed")
    e.set("id", str(i))
    e.set("order", str(i))
    e.set("lastModified", "-1")
    e.set("InterfaceClassName", name)

# --- Listas de links del juego.
# El player no las necesita (resuelve las escenas por el contenedor <Scenes>),
# pero el editor de Visionaire construye los paneles de cada seccion recorriendo
# estas listas (p. ej. la seccion "Scenes" lista \eScenes).  Si quedan vacias,
# el editor carga el proyecto pero los paneles aparecen sin contenido.
def _fill_game_links(game_tag, root_tag, table_id, keep=None):
    holder = game.find(game_tag)
    container = root.find(root_tag)
    if holder is None or container is None:
        return
    for child in list(holder):
        holder.remove(child)
    for obj in container:
        if keep is not None and not keep(obj):
            continue
        link = ET.SubElement(holder, "Link")
        link.set("parentLink", "T")
        link.set("id", obj.get("id", "0"))
        link.set("tableId", str(table_id))
        link.set("LinkAny", "F")


_fill_game_links("GameSceneLinks", "Scenes", T["scenes"])
_fill_game_links("GameCharacterLinks", "Characters", T["characters"])
_fill_game_links("GameFontLinks", "Fonts", T["fonts"])
_fill_game_links("GameInterfaces", "Interfaces", T["interfaces"])
_fill_game_links("GameCursors", "Cursors", T["cursors"])
_fill_game_links("GameItems", "Objects", T["objects"],
                 keep=lambda o: o.get("IsItem") == "T")

ET.indent(root, space="\t")
out = os.path.join(GAME, "Nagasaki1641.ved")
with open(out, "wb") as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    f.write(ET.tostring(root, encoding="utf-8"))
print("Escrito:", out)
print("Textos:", len(texts), "Acciones:", len(actions), "ActionParts:", len(aps),
      "Objetos:", len(OBJ), "Sprites:", len(sprites))
