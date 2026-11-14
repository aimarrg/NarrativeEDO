"""Arregla el layout del editor de Visionaire Studio 5.

El editor guarda en `%LOCALAPPDATA%\\Visionaire Editor\\viseditor.ini` el
workspace de la ultima seccion que estabas usando (texts, items, busses...).
Si cierras el editor mientras estas en *Texts*, la proxima vez abre solo con
el panel de dialogos y traducciones, sin arbol de proyecto ni editor de escenas.

Este script borra esa linea (`Workspaces=`) para que el editor reconstruya el
layout por defecto la proxima vez que lo abras. Hace copia de seguridad del
`.ini` antes de tocarlo.

Uso:
    py build\\fix_editor_layout.py

Cierra el editor antes de ejecutarlo: si sigue abierto, al salir volvera a
escribir su workspace y el arreglo no servira de nada.
"""

import os
import shutil
import subprocess
import sys
import time

INI = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Visionaire Editor",
    "viseditor.ini",
)


def editor_abierto():
    """True si el proceso viseditor.exe esta en marcha."""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq viseditor.exe"],
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False
    return "viseditor.exe" in out


def main():
    if not os.path.isfile(INI):
        print(f"No encuentro el archivo de configuracion:\n  {INI}")
        print("Abre el editor una vez y vuelve a ejecutar el script.")
        return 1

    if editor_abierto():
        print("El editor de Visionaire esta abierto.")
        print("Cierralo primero: al salir guardaria otra vez el layout roto.")
        return 1

    with open(INI, "rb") as fh:
        original = fh.read()

    lineas = original.split(b"\n")
    quedan = [l for l in lineas if not l.strip().startswith(b"Workspaces=")]

    if len(quedan) == len(lineas):
        print("El .ini ya estaba limpio: el editor abrira con el layout por defecto.")
        print(f"  {INI}")
        return 0

    copia = INI + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(INI, copia)

    with open(INI, "wb") as fh:
        fh.write(b"\n".join(quedan))

    print("Layout del editor reiniciado.")
    print(f"  Copia de seguridad: {copia}")
    print(f"  Editado:            {INI}")
    print("Abre el editor y elige la seccion que quieras en la barra superior.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
