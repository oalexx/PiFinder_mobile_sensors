# Raspberry Validation Runbook

Manual para desplegar PiFinder Lite en la Raspberry y ejecutar la prueba:

```text
Android -> upload JPEG -> Raspberry guarda -> quality score -> diagnostic solve
```

Issue relacionada: #42.

## 0. Validacion Base

Validacion conseguida el 2026-05-07:

```text
Raspberry Pi OS Trixie
Python 3.13.5
PiFinder branch: phase4-mobile-camera-diagnostic
Startup command: python -m PiFinder.main -fh --camera debug --keyboard none -x
Web remote: http://192.168.8.182:8080/remote
Result: PiFinder reached Event Loop and /remote worked from mobile
```

El puerto observado fue `8080`. Si otra instalacion usa puerto 80, ajusta las
URLs de este runbook.

## 1. Actualizar Codigo En La Raspberry

En la Raspberry:

```bash
cd ~/PiFinder_mobile_sensors
git fetch
git checkout phase4-mobile-camera-diagnostic
git pull
```

Si la rama remota fue reescrita y Git avisa de ramas divergentes:

```bash
git fetch origin
git reset --hard origin/phase4-mobile-camera-diagnostic
```

Comprueba que existen estos archivos:

```bash
ls PiFinder_lite/score_mobile_frame.py
ls PiFinder_lite/diagnostic_solve_mobile_frame.py
ls PiFinder_lite/mobile_bridge_api_v0.md
```

## 2. Preparar Entorno Python En Trixie

En Raspberry Pi OS Trixie / Python 3.13, no instales el `requirements.txt`
original sin revisar: algunas versiones fijadas son antiguas para NumPy 2 y
Python 3.13. Usa la receta completa de:

```text
PiFinder_lite/raspberry_lite_install.md
```

Resumen del entorno validado:

```bash
sudo apt update
xargs -a PiFinder_lite/apt-packages-trixie-py313.txt \
  sudo apt -o Acquire::ForceIPv4=true install -y

cd ~/PiFinder_mobile_sensors/python
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r ../PiFinder_lite/requirements-trixie-py313.txt
```

## 3. Inicializar Tetra3

```bash
cd ~/PiFinder_mobile_sensors
git submodule update --init --recursive --depth 1 python/PiFinder/tetra3

cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
pip install -e PiFinder/tetra3 --no-deps
python -c "import tetra3; print('tetra3 ok')"
```

## 4. Descargar Catalogo Hipparcos

`astro_data/hip_main.dat` no va en Git. Es necesario para que PiFinder cargue
el modulo de chart.

```bash
cd ~/PiFinder_mobile_sensors
wget -O astro_data/hip_main.dat \
  https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat
ls -lh astro_data/hip_main.dat
```

El tamano esperado es aproximadamente 51 MiB.

## 5. Compatibilidad Python 3.13

Esta rama ya incluye los dos cambios de codigo encontrados durante la
validacion Trixie:

- `python/PiFinder/utils.py`: resuelve automaticamente el layout importable de
  Tetra3.
- `python/PiFinder/ui/marking_menus.py`: usa `field(default_factory=...)` para
  evitar el error de dataclass mutable en Python 3.13.

La solucion para timezone en Python 3.13 es `timezonefinder==8.2.4`, incluida
en `requirements-trixie-py313.txt`. No uses `timezonefinder==6.1.9` en Trixie;
esa version intento usar un camino antiguo de `h3` durante la validacion.

Estos cambios estan documentados en:

```text
PiFinder_lite/upstream_change_log.md
```

## 6. Validar Importaciones

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -c "from google.protobuf import runtime_version; print('protobuf ok')"
python -c "import grpc; print(grpc.__version__)"
python -c "import skyfield, numpy; print('skyfield/numpy ok', numpy.__version__)"
python -c "import luma.core.device, luma.oled.device, luma.lcd.device; print('luma ok')"
python -c "import PiFinder.main; print('main import ok')"
```

## 7. Arrancar PiFinder Lite

Opcion segura para validar bridge/web:

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

Resultado esperado:

```text
Web Interface on port 8080
SkySafari server started and listening
Event Loop
```

## 8. Probar Desde El Movil

En otra terminal de la Raspberry:

```bash
hostname -I
```

Desde el movil:

```text
http://<ip-raspberry>:8080/remote
http://<ip-raspberry>:8080/mobile/status
```

Si `/remote` carga y responde, la base PiFinder Lite esta validada.

## 9. Configurar Android

Instala la APK debug actual:

```text
mobile/app/build/outputs/apk/debug/app-debug.apk
```

En la app:

```text
PiFinder Remote -> Base URL -> http://<ip-raspberry>:8080
Test Connection
Open Remote
```

Debe responder OK y mostrar `mobile-bridge-v0`.

## 10. Capturar Y Subir JPEG Desde Android

En la app:

```text
Camera Lab
Save Folder
Run Diagnostic Burst
Upload Last JPEG
```

Resultado esperado en Android:

```text
Camera frame uploaded
Frame ID: ...
Bytes: ...
Elapsed: ... ms
```

## 11. Confirmar Que La Raspberry Guardo El Frame

En la Raspberry:

```bash
ls -lh ~/PiFinder_data/mobile/frames
ls -t ~/PiFinder_data/mobile/frames/*.json | head -1
python -m json.tool "$(ls -t ~/PiFinder_data/mobile/frames/*.json | head -1)"
```

Debes ver pares:

```text
<frame_id>.jpg
<frame_id>.json
```

## 12. Ejecutar Quality Score En La Raspberry

Desde la raiz del repo:

```bash
cd ~/PiFinder_mobile_sensors
source python/.venv/bin/activate
python PiFinder_lite/score_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames"
```

Resultados esperados:

```text
Scored N JPEG frames
Accepted for diagnostic solve: N
```

## 13. Ejecutar Diagnostic Solve

Desde la raiz del repo:

```bash
cd ~/PiFinder_mobile_sensors
source python/.venv/bin/activate
python PiFinder_lite/diagnostic_solve_mobile_frame.py \
  --input "$HOME/PiFinder_data/mobile/frames" \
  --max-frames 12 \
  --solve-timeout-ms 1000 \
  --preprocess-modes baseline,background_subtract
```

Resultados esperados:

```text
Scored N JPEG frames
Attempted diagnostic solve on N frames
Solved N unique frames
```

## 14. Datos Para La Issue #42

Copia en la issue:

```text
Pi model:
Pi OS:
Python:
PiFinder branch/commit:
Startup command:
Android model:
App build/APK date:
PiFinder URL:
Upload result:
Stored frame path:
Stored metadata path:
Frame bytes:
Quality grade:
Quality score:
Accepted for diagnostic solve: yes/no
Diagnostic solve: OK/fail
Matches:
FOV:
Solve time:
Sky conditions:
Notes/errors:
```

## 15. Interpretacion Rapida

Caso bueno:

```text
Upload OK
Score HIGH/MEDIUM
Diagnostic solve OK
Solve time razonable
```

Conclusion:

```text
La cadena Android -> Pi -> score -> solve funciona.
```

Caso upload falla:

- movil y Pi en la misma red;
- IP/puerto correctos;
- `/mobile/status`;
- firewall/red;
- logs de PiFinder.

Caso score LOW:

- nubes;
- frame movido;
- fondo demasiado brillante;
- ISO demasiado alto;
- enfoque pobre;
- farolas/obstrucciones.

Caso score HIGH/MEDIUM pero solve falla:

- revisar FOV metadata;
- probar `--solve-timeout-ms 3000`;
- repetir con movil fijo;
- probar cielo mas oscuro.

## 16. Guardrail

Esta prueba es diagnostica.

No debe:

- alimentar el integrator;
- actualizar apuntado vivo;
- reemplazar el solver clasico;
- asumir todavia que la camara movil ya es produccion.
