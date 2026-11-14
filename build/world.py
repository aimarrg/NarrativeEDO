# -*- coding: utf-8 -*-
"""
MAPA DEL MUNDO de "Nagasaki 1641".

Este archivo es el único que necesitas tocar para cambiar la estructura del
juego: el orden de las escenas, las salidas entre ellas, los objetos clicables
y las condiciones de la historia.

Después de editarlo ejecuta:

    py build\\make_ved.py

No hace falta tocar make_ved.py (el generador) ni el editor de Visionaire.

--------------------------------------------------------------------------
CÓMO REORDENAR LA HISTORIA
--------------------------------------------------------------------------
* Las escenas se crean en el orden de la lista SCENES. Da igual el orden para
  jugar: la navegación la definen las salidas de cada clicable ("scene_to").
  Lo que sí cambia es el orden en que aparecen en el editor.
* El juego empieza en START_SCENE.
* Para cambiar el recorrido (por ejemplo, puerto antes que mercado), edita los
  "scene_to" de las salidas. No hay ninguna lógica cableada: todo son enlaces.

--------------------------------------------------------------------------
CÓMO AÑADIR UN CLICABLE
--------------------------------------------------------------------------
Copia un bloque de CLICKABLES y ajusta:

    key       nombre interno único (no repetir)
    scene     escena donde aparece
    name      clave de TEXTS con el nombre que se ve al pasar el ratón
    sprite    clave de un sprite generado por make_art.py (opcional)
    pos       (x, y) donde se dibuja el sprite (opcional)
    rect      (x, y, ancho, alto) de la zona de clic (opcional; si no, el sprite)
    stand     (x, y) donde se coloca Haru al interactuar
    order     orden de dibujo (mayor = más adelante)
    cond      condición para que aparezca (opcional)
    negate    True = aparece cuando la condición es FALSA
    walk      True = Haru camina hasta el objeto antes de actuar
    text      clave de TEXTS con la frase que se muestra
    set       lista de condiciones que se ponen a verdadero
    unset     lista de condiciones que se ponen a falso
    value     ("nombre", operador, número) para cambiar un valor
    set_first True = aplica condiciones antes del texto
    hide_char True = oculta a Haru durante la acción
    show_char True = vuelve a mostrar a Haru durante la acción
    scene_to  clave de escena a la que se cambia al terminar
    quit      True = cierra el juego

Las condiciones están en CONDITIONS. Para "abrir" las tabernas desde cualquier
otro clicable basta añadir  "set": ["tabernas_abiertas"].
"""

# ---------------------------------------------------------------------------
# Punto de partida
# ---------------------------------------------------------------------------
# El juego empieza con la cinemática del castillo; al terminar, la propia
# cinemática encadena con la casa (campo "start_scene_to" de la escena).
START_SCENE = "castillo"

# ---------------------------------------------------------------------------
# Escenas (el orden de esta lista es el orden en el editor)
# ---------------------------------------------------------------------------
SCENES = [
    {
        "key": "castillo",
        "name": "Castillo del Shogun",
        "bg": "bg_castle",
        "music": "audio/castle.ogg",
        "way": [(0, 600), (1280, 600), (1280, 714), (0, 714)],
        "entry": (760, 660),
        # --- cinemática inicial (edita las frases en TEXTS) -----------------
        # Cada elemento es una clave de TEXTS. Un bloque {"set": "condición"}
        # cambia la escena a mitad de la cinemática (aquí, el golpe del filo).
        "start_hide_char": True,
        "cinematic": [
            "castillo_1", "castillo_2", "castillo_3", "castillo_4",
            "castillo_5", "castillo_6",
            {"set": "ejecutado"},
            "castillo_7", "castillo_8", "castillo_9",
        ],
        "start_show_char": True,
        "start_scene_to": "casa",
        # en la cinemática, CONTINUAR no debe sacar a Haru de pie en el cadalso
        "pause_show_char": False,
    },
    {
        "key": "casa",
        "name": "Casa de Haru",
        "bg": "bg_home",
        "music": "audio/warehouse.ogg",
        "way": [(0, 585), (1280, 585), (1280, 714), (0, 714)],
        "entry": (640, 690),
        "start_texts": [],
    },
    {
        "key": "mercado",
        "name": "Mercado de Nagasaki",
        "bg": "bg_street",
        "music": "audio/market.ogg",
        "way": [(0, 585), (1280, 585), (1280, 714), (0, 714)],
        "entry": (150, 690),
        "start_texts": [],
    },
    {
        "key": "puerto",
        "name": "Puerto de Nagasaki",
        "bg": "bg_port",
        "music": "audio/market.ogg",
        "way": [(0, 590), (1280, 590), (1280, 714), (0, 714)],
        "entry": (150, 690),
        "start_texts": [],
    },
    {
        "key": "casa_pescador",
        "name": "Casa del pescador",
        "bg": "bg_fisher",
        "music": "audio/warehouse.ogg",
        "way": [(0, 600), (1280, 600), (1280, 714), (0, 714)],
        "entry": (300, 690),
        "start_texts": [],
    },
]

# ---------------------------------------------------------------------------
# Condiciones y valores de la historia
# ---------------------------------------------------------------------------
CONDITIONS = {
    "viendo_foto": False,        # la foto está ampliada
    "tabernas_abiertas": False,  # las dos tabernas están cerradas al principio
    "hablo_pescador": False,     # ejemplo de marca de diálogo
    "pausa": False,              # menú de pausa abierto
    "ejecutado": False,          # el filo ha caído en la cinemática inicial
}

VALUES = {
    "final": 0,
}

# ---------------------------------------------------------------------------
# Textos: nombres y frases (edita libremente)
# ---------------------------------------------------------------------------
TEXTS = {
    # --- nombres que se ven al pasar el ratón ---
    "n_foto": "Foto de familia",
    "n_nota": "Nota de tu padre",
    "n_cerrar_foto": "Cerrar la foto",
    "n_salir_casa": "Salir a la calle",
    "n_volver_casa": "Volver a casa",
    "n_ir_puerto": "Bajar al puerto",
    "n_volver_mercado": "Volver al mercado",
    "n_casa_pescador": "Casa del pescador",
    "n_volver_puerto": "Volver al puerto",
    "n_taberna_a": "Taberna de la Grulla",
    "n_taberna_b": "Taberna del Farol",
    "n_pescador": "Pescador",
    "n_red": "Red de pesca",
    "n_barco": "Barco holandés",
    "n_cajas": "Cajas del muelle",
    "n_continuar": "Continuar",
    "n_menu": "Menú principal",
    "n_salir": "Salir",
    "n_nueva": "Nueva partida",
    "n_abandonar": "Salir del juego",
    "haru": "Haru",

    # --- cinemática inicial (castillo del Shogun) ---
    "castillo_1": "Castillo del Shogun. Amanecer del décimo día del octavo mes.",
    "castillo_2": "El patio huele a tierra mojada. Nadie habla.",
    "castillo_3": ("Haru espera de rodillas junto al cepo. Las manos le tiemblan "
                   "detrás de la espalda."),
    "castillo_4": ("«Haru, hijo de comerciantes de Nagasaki: acusado de tratar "
                   "con extranjeros.»"),
    "castillo_5": ("La multitud contiene el aliento. El verdugo comprueba la "
                   "cuerda."),
    "castillo_6": "La hoja sube. Un instante de silencio.",
    "castillo_7": "El filo cae.",
    "castillo_8": "Y todo se apaga.",
    "castillo_9": ("Despiertas en tu casa. Aún es de noche y todo sigue en su "
                   "sitio."),

    # --- frases (sustitúyelas por tus diálogos) ---
    "foto": ("Tu familia, retratada el año del incendio. Tu madre sostiene el abanico "
             "que aún guardas; tu padre finge no sonreír."),
    "nota": ("«Haru: si lees esto, es que ya eres el hombre de la casa. Te quiero más "
             "de lo que supe decirte. Cuida el negocio y cuídate tú. — Tu padre»"),
    "taberna_cerrada": ("La puerta está cerrada con una cuerda y un cartel: "
                        "«Cerrado hasta la noche»."),
    "taberna_abierta": "(Aquí irá tu diálogo de la taberna.)",
    "pescador": "(Aquí irá tu diálogo con el pescador.)",
    "red": "(Aquí irá el texto de la red de pesca.)",
    "barco": "(Aquí irá el texto del barco holandés.)",
    "cajas": "(Aquí irá el texto de las cajas del muelle.)",
}

# ---------------------------------------------------------------------------
# Clicables
# ---------------------------------------------------------------------------
CLICKABLES = [
    # -------------------------------------------------------------- CASTILLO
    # Decorado de la cinemática. No tienen acción: solo se dibujan.
    {
        "key": "guillotine_up",
        "scene": "castillo",
        "sprite": "guillotine_up",
        "pos": (635, 193),
        "stand": (700, 660),
        "order": 5,
        "cond": "ejecutado",
        "negate": True,
    },
    {
        "key": "guillotine_down",
        "scene": "castillo",
        "sprite": "guillotine_down",
        "pos": (635, 193),
        "stand": (700, 660),
        "order": 5,
        "cond": "ejecutado",
    },
    {
        "key": "verdugo",
        "scene": "castillo",
        "sprite": "verdugo",
        "pos": (872, 289),
        "stand": (900, 660),
        "order": 6,
    },
    {
        "key": "haru_reo",
        "scene": "castillo",
        "sprite": "haru_reo",
        "pos": (650, 419),
        "stand": (700, 660),
        "order": 7,
        "cond": "ejecutado",
        "negate": True,
    },

    # ------------------------------------------------------------------ CASA
    {
        "key": "foto",
        "scene": "casa",
        "name": "n_foto",
        "sprite": "photo",
        "pos": (300, 190),
        "stand": (375, 712),
        "order": 5,
        "cond": "viendo_foto",
        "negate": True,
        "text": "foto",
        "set": ["viendo_foto"],
        "set_first": True,
        "hide_char": True,
    },
    {
        "key": "foto_zoom",
        "scene": "casa",
        "name": "n_cerrar_foto",
        "sprite": "photo_zoom",
        "pos": (0, 0),
        "rect": (0, 0, 1280, 720),
        "stand": (375, 690),
        "order": 900,
        "cond": "viendo_foto",
        "walk": False,
        "unset": ["viendo_foto"],
        "show_char": True,
    },
    {
        "key": "nota",
        "scene": "casa",
        "name": "n_nota",
        "sprite": "note",
        "pos": (392, 598),
        "stand": (470, 712),
        "order": 6,
        "cond": "viendo_foto",
        "negate": True,
        "text": "nota",
    },
    {
        "key": "salir_casa",
        "scene": "casa",
        "name": "n_salir_casa",
        "rect": (1030, 160, 190, 420),
        "stand": (1015, 690),
        "order": 2,
        "scene_to": "mercado",
    },

    # --------------------------------------------------------------- MERCADO
    {
        "key": "taberna_a_cerrada",
        "scene": "mercado",
        "name": "n_taberna_a",
        "sprite": "tavern_a_closed",
        "pos": (40, 250),
        "stand": (220, 690),
        "order": 5,
        "cond": "tabernas_abiertas",
        "negate": True,
        "text": "taberna_cerrada",
    },
    {
        "key": "taberna_a_abierta",
        "scene": "mercado",
        "name": "n_taberna_a",
        "sprite": "tavern_a_open",
        "pos": (40, 250),
        "stand": (220, 690),
        "order": 5,
        "cond": "tabernas_abiertas",
        "text": "taberna_abierta",
    },
    {
        "key": "taberna_b_cerrada",
        "scene": "mercado",
        "name": "n_taberna_b",
        "sprite": "tavern_b_closed",
        "pos": (880, 250),
        "stand": (1060, 690),
        "order": 5,
        "cond": "tabernas_abiertas",
        "negate": True,
        "text": "taberna_cerrada",
    },
    {
        "key": "taberna_b_abierta",
        "scene": "mercado",
        "name": "n_taberna_b",
        "sprite": "tavern_b_open",
        "pos": (880, 250),
        "stand": (1060, 690),
        "order": 5,
        "cond": "tabernas_abiertas",
        "text": "taberna_abierta",
    },
    {
        "key": "volver_casa",
        "scene": "mercado",
        "name": "n_volver_casa",
        "rect": (0, 530, 80, 184),
        "stand": (100, 690),
        "order": 2,
        "scene_to": "casa",
    },
    {
        "key": "ir_puerto",
        "scene": "mercado",
        "name": "n_ir_puerto",
        "rect": (1200, 530, 80, 184),
        "stand": (1180, 690),
        "order": 2,
        "scene_to": "puerto",
    },

    # ---------------------------------------------------------------- PUERTO
    {
        "key": "volver_mercado",
        "scene": "puerto",
        "name": "n_volver_mercado",
        "rect": (0, 530, 80, 184),
        "stand": (100, 690),
        "order": 2,
        "scene_to": "mercado",
    },
    {
        "key": "ir_casa_pescador",
        "scene": "puerto",
        "name": "n_casa_pescador",
        "rect": (1090, 260, 190, 340),
        "stand": (1075, 690),
        "order": 2,
        "scene_to": "casa_pescador",
    },
    {
        "key": "barco",
        "scene": "puerto",
        "name": "n_barco",
        "rect": (700, 210, 400, 250),
        "stand": (900, 690),
        "order": 3,
        "text": "barco",
    },
    {
        "key": "cajas",
        "scene": "puerto",
        "name": "n_cajas",
        "rect": (170, 460, 250, 130),
        "stand": (295, 690),
        "order": 3,
        "text": "cajas",
    },

    # -------------------------------------------------------- CASA PESCADOR
    {
        "key": "pescador",
        "scene": "casa_pescador",
        "name": "n_pescador",
        "sprite": "fisher",
        "pos": (760, 377),
        "stand": (990, 690),
        "order": 5,
        "text": "pescador",
        "set": ["hablo_pescador"],
    },
    {
        "key": "red",
        "scene": "casa_pescador",
        "name": "n_red",
        "sprite": "net",
        "pos": (250, 300),
        "stand": (370, 690),
        "order": 4,
        "text": "red",
    },
    {
        "key": "salir_pescador",
        "scene": "casa_pescador",
        "name": "n_volver_puerto",
        "rect": (30, 230, 170, 370),
        "stand": (235, 690),
        "order": 2,
        "scene_to": "puerto",
    },
]
