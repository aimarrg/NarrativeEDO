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
# Contenido narrativo
# ---------------------------------------------------------------------------
C_HAS_SEAL = add_cond("tiene_sello")
C_TALK_FISHER = add_cond("hablo_pescador")
C_TALK_MERCHANT = add_cond("hablo_mercader")
C_TALK_HIDDEN = add_cond("hablo_fugitivo")
C_CHOICE = add_cond("decision_disponible")
C_HAS_FISH = add_cond("tiene_pescado")
C_FISH_TAKEN = add_cond("pescado_cogido")
C_GUARD_DISTRACTED = add_cond("guardia_distraido")
C_HAS_EVIDENCE = add_cond("tiene_pruebas")
V_ENDING = add_value("final", 0)

TX = {
    "intro1": add_text("Nagasaki, 1641. El shogunato Tokugawa ha cerrado Japón al mundo. "
                      "Solo Dejima, una isla artificial en el puerto, sigue abierta al comercio."),
    "intro2": add_text("Has heredado el negocio de tu padre. Hoy debes entregar un cargamento "
                      "en el almacén del puerto... y cobrar antes del anochecer."),
    "intro3": add_text("Habla con el pescador, consigue pasar al guardia y revisa la caja. "
                      "El sello del gremio es la llave."),
    "fisher_1": add_text("Pescador: «Los barcos holandeses descargan de noche. Anoche vi linternas "
                         "en el almacén viejo... y gente que no debía estar ahí.»"),
    "fisher_2": add_text("Pescador: «El guardia lleva desde el amanecer con el estómago vacío. "
                         "Ofrécele algo de comer y quizá te deje registrar la caja.»"),
    "fish_pick": add_text("Coges un pescado seco del puesto. Huele fatal, pero es comida."),
    "guard_no": add_text("Guardia: «Alto. Sin el sello del gremio no se pasa al almacén.»"),
    "guard_hungry": add_text("Guardia: «¿Eso es pescado? ... Bueno. El deber puede esperar "
                             "un momento.»"),
    "guard_eating": add_text("El guardia mastica feliz, mirando al mar. La caja queda a tu alcance."),
    "guard_ok": add_text("Guardia: «Ese sello está en regla. El inspector te espera dentro.»"),
    "crate_blocked": add_text("El guardia no te quita ojo. Registrar la caja ahora sería una mala idea."),
    "crate_1": add_text("Bajo la lona hay un sello de madera del gremio de comerciantes. "
                        "Sin él, el guardia no te dejará pasar."),
    "crate_2": add_text("La caja está vacía. Solo queda la marca del sello en el polvo."),
    "edict": add_text("Edicto del shogun: «Ningún japonés abandonará el país. Ningún extranjero "
                      "entrará sin permiso. El que ayude a un fugitivo será castigado.»"),
    "door_no": add_text("El guardia bloquea la puerta con la lanza. No piensas insistir."),
    "door_ok": add_text("Empujas la puerta corredera. Dentro huele a madera húmeda y a especias."),
    "wh_merchant_1": add_text("Mercader holandés: «Ah, el joven Haru. Tu padre y yo teníamos un acuerdo. "
                              "La mercancía está abajo... y también tres polizones.»"),
    "wh_merchant_2": add_text("Mercader holandés: «Nadie tiene que saberlo. Tú cobras, yo desaparezco. "
                              "¿Qué dices?»"),
    "wh_merchant_3": add_text("Mercader holandés: «Piénsalo. Denunciarme te dará una medalla; "
                              "ayudarme, una fortuna. O puedes callar y seguir cobrando.»"),
    "wh_hidden": add_text("Fugitivo: «Nos esconden en cajas. Si nos encuentran, nos matan. "
                          "Por favor... tú no eres como ellos.»"),
    "wh_sack": add_text("Un saco de seda con el sello del inspector. Alguien está cobrando por "
                        "dejar pasar mercancía prohibida."),
    "wh_sack_empty": add_text("El saco ya no guarda nada. Solo queda el sello del inspector "
                              "grabado en la etiqueta."),
    "wh_denounce_no": add_text("Sin una prueba, el inspector se reirá de ti. Registra el almacén "
                               "antes de denunciar."),
    "wh_help_no": add_text("No sabes quiénes son ni adónde irían. Habla antes con el fugitivo."),
    "wh_denounce": add_text("Cierras la puerta y corres a la oficina de inspección. "
                            "Al amanecer, el almacén está rodeado de guardias."),
    "wh_help": add_text("Abres la trampilla del muelle. Los tres fugitivos escapan en la barca "
                        "del pescador antes de que cante el gallo."),
    "wh_silent": add_text("Guardas silencio y apartas la mirada. La seda cambia de manos "
                          "y tú cobras tu parte sin hacer preguntas."),
    "end_denounce": add_text("El inspector es detenido y el mercader holandés expulsado de Dejima. "
                             "Tu negocio sobrevive, pero el puerto te mira con recelo. "
                             "Has elegido la ley."),
    "end_help": add_text("Al amanecer, la barca es solo un punto en el horizonte. Pierdes el cargamento "
                         "y la mitad de tu fortuna... pero nadie muere esa noche. "
                         "Has elegido a las personas."),
    "end_silent": add_text("No haces nada. El cargamento se descarga y el dinero cambia de manos. "
                           "La historia no recordará tu nombre."),
    "fin": add_text("FIN"),
    "replay": add_text("Volver a jugar"),
    "merchant_name": add_text("Mercader holandés"),
    "hidden_name": add_text("Fugitivo"),
    "sack_name": add_text("Saco de seda"),
    "fisher_name": add_text("Pescador"),
    "guard_name": add_text("Guardia del puerto"),
    "guard_eating_name": add_text("Guardia comiendo"),
    "fish_name": add_text("Pescado seco"),
    "crate_name": add_text("Caja de mercancías"),
    "door_name": add_text("Puerta del almacén"),
    "edict_name": add_text("Edicto del shogun"),
    "denounce_name": add_text("Denunciar al inspector"),
    "help_name": add_text("Ayudar a escapar"),
    "silent_name": add_text("Callar y cobrar"),
    "scene_market": add_text("Mercado del puerto"),
    "scene_warehouse": add_text("Almacén del puerto"),
    "scene_epilogue": add_text("Amanecer en Dejima"),
    "menu_new": add_text("Nueva partida"),
    "menu_quit": add_text("Salir"),
    "scene_menu": add_text("Menú principal"),
    "haru": add_text("Haru"),
}


# ---------------------------------------------------------------------------
# Animaciones / personaje / fuente / cursor
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
# Objetos (ids fijos para poder enlazarlos)
# ---------------------------------------------------------------------------
OBJ = {}


def make_object(key, oid, name_text, scene_key, order, condition=None, walkable="F",
                negate=False, stand=None, poly=None):
    m = MANIFEST["objects"][key]
    sid = add_sprite(m["path"], m["x"], m["y"], key)
    rect = poly or (m["x"], m["y"], m["w"], m["h"])
    OBJ[key] = {"id": oid, "name": name_text, "sprite": sid, "scene": scene_key,
                "order": order, "cond": condition, "walkable": walkable,
                "negate": negate, "stand": stand or (m["x"], m["y"]),
                "rect": rect}
    return oid


make_object("fisher", 0, TX["fisher_name"], "market", 0, stand=(385, 676),
            poly=(58, 380, 105, 294))
make_object("fish", 14, TX["fish_name"], "market", 1, condition=C_FISH_TAKEN,
            negate=True, stand=(385, 676))
make_object("edict", 1, TX["edict_name"], "market", 2, stand=(480, 690))
make_object("crate", 2, TX["crate_name"], "market", 3, stand=(600, 690))
make_object("guard", 3, TX["guard_name"], "market", 4, condition=C_GUARD_DISTRACTED,
            negate=True, stand=(900, 690))
make_object("guard_eating", 15, TX["guard_eating_name"], "market", 4,
            condition=C_GUARD_DISTRACTED, stand=(900, 690))
make_object("door", 4, TX["door_name"], "market", 5, stand=(950, 690))
# marcador invisible de inicio
MARK_MARKET = add_sprite("graphics/marker.png", 420, 665, "inicio")
OBJ["start_market"] = {"id": 5, "name": None, "sprite": MARK_MARKET, "scene": "market",
                       "order": 6, "cond": None, "walkable": "T", "negate": False,
                       "stand": (420, 665)}

make_object("hidden", 7, TX["hidden_name"], "warehouse", 0, stand=(380, 690))
make_object("sack", 8, TX["sack_name"], "warehouse", 1, stand=(560, 690))
make_object("merchant", 6, TX["merchant_name"], "warehouse", 2, stand=(860, 690))
make_object("plaque_denounce", 9, TX["denounce_name"], "warehouse", 3,
            condition=C_CHOICE, stand=(380, 690))
make_object("plaque_silent", 16, TX["silent_name"], "warehouse", 4,
            condition=C_CHOICE, stand=(650, 690))
make_object("plaque_help", 10, TX["help_name"], "warehouse", 5,
            condition=C_CHOICE, stand=(950, 690))
MARK_WAREHOUSE = add_sprite("graphics/marker.png", 620, 660, "entrada almacen")
OBJ["entry_warehouse"] = {"id": 11, "name": None, "sprite": MARK_WAREHOUSE, "scene": "warehouse",
                          "order": 6, "cond": None, "walkable": "T", "negate": False,
                          "stand": (620, 660)}

MARK_EPILOGUE = add_sprite("graphics/marker.png", 760, 690, "entrada epilogo")
OBJ["entry_epilogue"] = {"id": 12, "name": None, "sprite": MARK_EPILOGUE, "scene": "epilogue",
                         "order": 0, "cond": None, "walkable": "T", "negate": False,
                         "stand": (760, 690)}
make_object("plaque_replay", 13, TX["replay"], "epilogue", 1, stand=(640, 695))


def make_zone(key, oid, name_text, scene_key, order, rect):
    """Zona clicable sin sprite: solo polígono (botones del menú)."""
    OBJ[key] = {"id": oid, "name": name_text, "sprite": None, "scene": scene_key,
                "order": order, "cond": None, "walkable": "F", "negate": False,
                "stand": (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2),
                "rect": rect}
    return oid


make_zone("menu_new", 17, TX["menu_new"], "menu", 0, (440, 396, 400, 66))
make_zone("menu_quit", 18, TX["menu_quit"], "menu", 1, (440, 486, 400, 66))


def ap_text(text_id, char=0):
    return add_ap(23, "Diálogo", link1=(T["texts"], text_id),
                  link2=(T["characters"], char), i1=0)


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
    return add_ap(31, f"Ir a {obj_key}", link1=(T["characters"], 0), link2=(T["objects"], o["id"]), i1=1)


def ap_scene(entry_key):
    o = OBJ[entry_key]
    return add_ap(10, f"Cambiar a escena {entry_key}", link1=(T["objects"], o["id"]), i1=1, i2=0)


def ap_showchar(char=0):
    return add_ap(98, "Mostrar personaje", link1=(T["characters"], char), i1=0)


def ap_hidechar(char=0):
    return add_ap(98, "Ocultar personaje", link1=(T["characters"], char), i1=1)


# ---------------------------------------------------------------------------
# Acciones de los objetos
# ---------------------------------------------------------------------------
A = {}

A["fisher"] = add_action("Pescador", 7, [
    ap_goto("fisher"),
    ap_if(C_TALK_FISHER, False),
    ap_text(TX["fisher_1"]),
    ap_text(TX["fisher_2"]),
    ap_setcond(C_TALK_FISHER),
    ap_else(),
    ap_text(TX["fisher_2"]),
    ap_endif(),
])

A["fish"] = add_action("Coger pescado", 7, [
    ap_goto("fish"),
    ap_if(C_FISH_TAKEN, False),
    ap_text(TX["fish_pick"]),
    ap_setcond(C_HAS_FISH),
    ap_setcond(C_FISH_TAKEN),
    ap_else(),
    ap_text(TX["crate_2"]),
    ap_endif(),
])

A["edict"] = add_action("Edicto", 7, [ap_goto("edict"), ap_text(TX["edict"])])

A["crate"] = add_action("Caja", 7, [
    ap_goto("crate"),
    ap_if(C_GUARD_DISTRACTED, True),
    ap_if(C_HAS_SEAL, False),
    ap_text(TX["crate_1"]),
    ap_setcond(C_HAS_SEAL),
    ap_else(),
    ap_text(TX["crate_2"]),
    ap_endif(),
    ap_else(),
    ap_text(TX["crate_blocked"]),
    ap_endif(),
])

A["guard"] = add_action("Guardia", 7, [
    ap_goto("guard"),
    ap_if(C_GUARD_DISTRACTED, True),
    ap_text(TX["guard_eating"]),
    ap_else(),
    ap_if(C_HAS_FISH, True),
    ap_text(TX["guard_hungry"]),
    ap_setcond(C_HAS_FISH, 1),
    ap_setcond(C_GUARD_DISTRACTED),
    ap_else(),
    ap_text(TX["guard_no"]),
    ap_endif(),
    ap_endif(),
])

A["door"] = add_action("Puerta del almacén", 7, [
    ap_goto("door"),
    ap_if(C_HAS_SEAL, False),
    ap_text(TX["door_no"]),
    ap_else(),
    ap_text(TX["door_ok"]),
    ap_scene("entry_warehouse"),
    ap_endif(),
])

A["merchant"] = add_action("Mercader", 7, [
    ap_goto("merchant"),
    ap_if(C_TALK_MERCHANT, False),
    ap_text(TX["wh_merchant_1"]),
    ap_setcond(C_TALK_MERCHANT),
    ap_setcond(C_CHOICE),
    ap_else(),
    ap_text(TX["wh_merchant_3"]),
    ap_endif(),
])

A["hidden"] = add_action("Fugitivo", 7, [
    ap_goto("hidden"),
    ap_text(TX["wh_hidden"]),
    ap_setcond(C_TALK_HIDDEN),
])

A["sack"] = add_action("Saco", 7, [
    ap_goto("sack"),
    ap_if(C_HAS_EVIDENCE, False),
    ap_text(TX["wh_sack"]),
    ap_setcond(C_HAS_EVIDENCE),
    ap_else(),
    ap_text(TX["wh_sack_empty"]),
    ap_endif(),
])

A["denounce"] = add_action("Denunciar", 7, [
    ap_goto("plaque_denounce"),
    ap_if(C_HAS_EVIDENCE, True),
    ap_setvalue(V_ENDING, 0, 1),
    ap_text(TX["wh_denounce"]),
    ap_scene("entry_epilogue"),
    ap_else(),
    ap_text(TX["wh_denounce_no"]),
    ap_endif(),
])

A["help"] = add_action("Ayudar", 7, [
    ap_goto("plaque_help"),
    ap_if(C_TALK_HIDDEN, True),
    ap_setvalue(V_ENDING, 0, 2),
    ap_text(TX["wh_help"]),
    ap_scene("entry_epilogue"),
    ap_else(),
    ap_text(TX["wh_help_no"]),
    ap_endif(),
])

A["silent"] = add_action("Callar", 7, [
    ap_goto("plaque_silent"),
    ap_setvalue(V_ENDING, 0, 0),
    ap_text(TX["wh_silent"]),
    ap_scene("entry_epilogue"),
])

A["replay"] = add_action("Volver a jugar", 7, [add_ap(174, "Reiniciar partida")])

# Acciones de inicio de escena
A["start_market"] = add_action("Inicio del mercado", 31, [
    ap_text(TX["intro1"]),
    ap_text(TX["intro2"]),
    ap_text(TX["intro3"]),
])

A["start_warehouse"] = add_action("Inicio del almacén", 31, [
    ap_if(C_TALK_MERCHANT, False),
    ap_text(TX["wh_merchant_2"]),
    ap_endif(),
])

A["start_epilogue"] = add_action("Inicio del epílogo", 31, [
    ap_ifvalue(V_ENDING, 0, 1),
    ap_text(TX["end_denounce"]),
    ap_ifvalue(V_ENDING, 0, 2, elseif=True),
    ap_text(TX["end_help"]),
    ap_else(),
    ap_text(TX["end_silent"]),
    ap_endif(),
    ap_text(TX["fin"]),
])

# ---------------------------------------------------------------------------
# Menú principal
# ---------------------------------------------------------------------------
A["menu_new"] = add_action("Nueva partida", 7, [
    ap_setcond(C_HAS_SEAL, 1),
    ap_setcond(C_TALK_FISHER, 1),
    ap_setcond(C_TALK_MERCHANT, 1),
    ap_setcond(C_TALK_HIDDEN, 1),
    ap_setcond(C_CHOICE, 1),
    ap_setcond(C_HAS_FISH, 1),
    ap_setcond(C_FISH_TAKEN, 1),
    ap_setcond(C_GUARD_DISTRACTED, 1),
    ap_setcond(C_HAS_EVIDENCE, 1),
    ap_setvalue(V_ENDING, 0, 0),
    ap_showchar(),
    ap_scene("start_market"),
])

A["menu_quit"] = add_action("Salir del juego", 7, [add_ap(55, "Salir")])

A["start_menu"] = add_action("Inicio del menú", 31, [ap_hidechar()])

# ---------------------------------------------------------------------------
# Objetos -> acciones
# ---------------------------------------------------------------------------
OBJ_ACTION = {
    "fisher": A["fisher"], "fish": A["fish"], "edict": A["edict"], "crate": A["crate"],
    "guard": A["guard"], "door": A["door"], "merchant": A["merchant"],
    "hidden": A["hidden"], "sack": A["sack"], "plaque_denounce": A["denounce"],
    "plaque_help": A["help"], "plaque_silent": A["silent"], "plaque_replay": A["replay"],
    "menu_new": A["menu_new"], "menu_quit": A["menu_quit"],
}

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
game.set("GameDrawActionText", "1")
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
game.set("GameDialogTextAlignment", "-1")

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
first_char.set("id", "0")
first_char.set("tableId", str(T["characters"]))
first_char.set("LinkAny", "F")
std_lang = ET.SubElement(game, "GameStandardLanguage")
std_lang.set("parentLink", "F")
std_lang.set("id", "0")
std_lang.set("tableId", str(T["languages"]))
std_lang.set("LinkAny", "F")
ET.SubElement(game, "GameActions")
for tag in ["GameStartAction", "GameRightClickAction", "GameLeftDblClickAction", "GameLeftHoldAction",
            "GameLeftHoldingAction"]:
    e = ET.SubElement(game, tag)
    e.set("parentLink", "F")
    e.set("id", "-1")
    e.set("tableId", "-1")
    e.set("LinkAny", "F")
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
for k, v in {"top": "-1", "left": "-1", "bottom": "700", "right": "1260"}.items():
    rect.set(k, v)
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
chars.set("newId", "1")
chars.set("versionedId", "-1")
chars.set("tableId", str(T["characters"]))
ch = ET.SubElement(chars, "Character")
ch.set("name", "Haru")
ch.set("id", "0")
ch.set("order", "0")
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
start.set("id", str(OBJ["start_market"]["id"]))
start.set("tableId", str(T["objects"]))
start.set("LinkAny", "F")
ET.SubElement(ch, "CharacterValues")
ET.SubElement(ch, "CharacterConditions")
for tag in ["CharacterActiveDialogFont", "CharacterInactiveDialogFont",
            "CharacterActiveUsedDialogFont", "CharacterInactiveUsedDialogFont"]:
    e = ET.SubElement(ch, tag)
    e.set("parentLink", "F")
    e.set("id", "-1")
    e.set("tableId", "-1")
    e.set("LinkAny", "F")
area = ET.SubElement(ch, "CharacterDialogArea")
for k, v in {"top": "0", "left": "0", "bottom": "-1", "right": "-1"}.items():
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
WAY_DEFS = {
    "menu": [(0, 640), (1280, 640), (1280, 714), (0, 714)],
    "market": [(0, 592), (240, 584), (520, 586), (800, 584), (1040, 586),
               (1280, 590), (1280, 714), (0, 714)],
    "warehouse": [(0, 602), (320, 596), (640, 598), (980, 596), (1280, 602),
                  (1280, 714), (0, 714)],
    "epilogue": [(0, 652), (320, 646), (640, 650), (980, 646), (1280, 652),
                 (1280, 714), (0, 714)],
}
WAY_ID = {key: i for i, key in enumerate(WAY_DEFS)}

MUSIC = {
    "menu": "audio/menu.ogg",
    "market": "audio/market.ogg",
    "warehouse": "audio/warehouse.ogg",
    "epilogue": "audio/epilogue.ogg",
}

scene_defs = [
    ("menu", "bg_menu", "Menú principal", A["start_menu"]),
    ("market", "bg_market", "Mercado del puerto", A["start_market"]),
    ("warehouse", "bg_warehouse", "Almacén del puerto", A["start_warehouse"]),
    ("epilogue", "bg_epilogue", "Amanecer en Dejima", A["start_epilogue"]),
]
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
    sn.set("id", str(TX[f"scene_{key}"]))
    sn.set("tableId", str(T["texts"]))
    sn.set("LinkAny", "F")
    objs = ET.SubElement(sc, "SceneObjects")
    for o in sorted([o for o in OBJ.values() if o["scene"] == key], key=lambda x: x["order"]):
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
    if ap["l1"]:
        l1.set("parentLink", "F" if ap["cmd"] == 10 else "T")
        l1.set("id", str(ap["l1"][1]))
        l1.set("tableId", str(ap["l1"][0]))
    else:
        l1.set("parentLink", "F")
        l1.set("id", "-1")
        l1.set("tableId", "-1")
    l1.set("LinkAny", "F")
    l2 = ET.SubElement(e, "ActionPartAltLink")
    if ap["l2"] and ap["cmd"] == 31:
        l2.set("parentLink", "T")
        l2.set("id", str(ap["l2"][1]))
        l2.set("tableId", str(ap["l2"][0]))
    elif ap["l2"]:
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

local function logText(msg)
  local f = io.open("C:/Temps/opencode/lua_text.log", "a")
  if f then
    f:write(msg .. "\\n")
    f:close()
  end
end

function nagasakiTextStarted(text)
  local id = "?"
  if text and text.getId then
    local tid = text:getId()
    if tid then id = tostring(tid.id) end
  end
  local body = text and text.CurrentText or ""
  logText(string.format("%.2f textStarted id=%s len=%d current=%s", os.clock(), id, #body, body))
  local names = {"tiene_sello", "hablo_pescador", "hablo_mercader", "hablo_fugitivo",
                 "decision_disponible", "tiene_pescado", "pescado_cogido",
                 "guardia_distraido", "tiene_pruebas"}
  local parts = {}
  for _, n in ipairs(names) do
    local c = Conditions[n]
    if c then parts[#parts + 1] = n .. "=" .. tostring(c.Value) end
  end
  logText("  cond " .. table.concat(parts, " "))
  if text then
    local dur = 1300 + #body * 28
    if dur > 5200 then dur = 5200 end
    if dur < 1500 then dur = 1500 end
    text.TimeToWait = dur
  end
end

function nagasakiTextStopped(text)
  local id = "?"
  if text and text.getId then
    local tid = text:getId()
    if tid then id = tostring(tid.id) end
  end
  logText(string.format("%.2f textStopped id=%s", os.clock(), id))
end

registerEventHandler("textStarted", "nagasakiTextStarted")
registerEventHandler("textStopped", "nagasakiTextStopped")

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

ET.indent(root, space="\t")
out = os.path.join(GAME, "Nagasaki1641.ved")
with open(out, "wb") as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    f.write(ET.tostring(root, encoding="utf-8"))
print("Escrito:", out)
print("Textos:", len(texts), "Acciones:", len(actions), "ActionParts:", len(aps),
      "Objetos:", len(OBJ), "Sprites:", len(sprites))
