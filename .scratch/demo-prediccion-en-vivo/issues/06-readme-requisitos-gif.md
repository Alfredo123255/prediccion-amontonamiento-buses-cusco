# 06: README de la demo, requisitos y GIF de respaldo

**What to build:** Cualquier integrante del grupo puede preparar y presentar la demo siguiendo el README. Además queda un GIF o video corto de la demo funcionando, para mostrarlo si falla la laptop o el proyector el viernes 27-nov.

**Blocked by:** 02 (Rango P10–P90 calibrado con CQR), 03 (Decisión del clima en validación), 04 (Reloj ▶ x60 y mapa en vivo), 05 (MAE acumulado del día)

**Status:** ready-for-agent

- [x] El README de la demo explica dónde poner los CSV, cómo entrenar y cómo lanzar la app, en 3 a 5 pasos.
- [x] Streamlit está en los requisitos del proyecto y no se agregaron otras dependencias.
- [x] El README del proyecto apunta a la demo, que ya no figura "en construcción".
- [x] Las pruebas pasan con un solo comando.
- [x] Hay un GIF o video de unos 30–60 s: reloj avanzando en hora punta, bus elegido, rango y llegada real dentro, MAE acumulado. No muestra datos crudos.
- [x] El GIF no se versiona si pesa demasiado o contiene datos de los docentes. Si no se versiona, queda guardado donde el grupo lo encuentre.

## Comments

- 2026-11-23, `demo/README.md` reescrito (4 pasos, guía de la expo, pruebas, respaldo); el README raíz apunta a la demo. Streamlit ya estaba en `requirements.txt` (pydeck viene con él); no se agregaron dependencias.
- Pruebas: `python demo/test_nucleo.py`.
- Respaldo grabado con Playwright headless (Chromium del sistema) y ffmpeg: `demo/respaldo/demo_respaldo.gif` (5,6 MB) y `.mp4` (0,8 MB), ignorados por git. Falta subirlos a la carpeta compartida del grupo.
