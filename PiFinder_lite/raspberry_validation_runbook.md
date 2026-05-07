# Raspberry Validation Runbook

Manual para desplegar PiFinder Lite en la Raspberry y ejecutar la prueba de:

```text
Android -> upload JPEG -> Raspberry guarda -> quality score -> diagnostic solve
```

Issue relacionada: #42.

## 0. Punto Importante Antes De Empezar

La Raspberry debe tener el código actualizado con los cambios de esta rama.

Si todavía no has hecho commit/push desde el PC, la Pi no podrá hacer `git pull`
de estos cambios. En ese caso, primero haz commit/push desde el PC o copia la
carpeta actual a la Pi.

## 1. Actualizar Código En La Raspberry

En la Raspberry:

```bash
cd ~/PiFinder_mobile_sensors
git fetch
git checkout <tu-rama>
git pull
```

Si el repo está en otra carpeta:

```bash
cd /ruta/al/repo
```

Comprueba que existen estos archivos:

```bash
ls PiFinder_lite/score_mobile_frame.py
ls PiFinder_lite/diagnostic_solve_mobile_frame.py
ls PiFinder_lite/mobile_bridge_api_v0.md
```

## 2. Preparar Entorno Python

En la Raspberry:

```bash
cd python
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si `.venv` ya existía:

```bash
cd python
source .venv/bin/activate
pip install -r requirements.txt
```

Si Tetra3 no está instalado editable y falla el solver:

```bash
pip install -e PiFinder/tetra3
```

Vuelve a la raíz del repo:

```bash
cd ..
```

## 3. Arrancar PiFinder Lite

### Opción Segura Para Validar Bridge/Web

Usa fake hardware y cámara debug:

```bash
cd python
source .venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

### Opción Con Hardware Real Pero Sin Keypad

Cuando quieras usar la Raspberry más parecida al PiFinder real:

```bash
cd python
source .venv/bin/activate
python -m PiFinder.main --keyboard none -x
```

Si GPS real no está listo:

```bash
python -m PiFinder.main --gps fake --keyboard none -x
```

## 4. Encontrar IP Y Puerto

En otra terminal de la Raspberry:

```bash
hostname -I
```

PiFinder normalmente sirve en:

```text
http://<ip-raspberry>/
```

Si no puede usar puerto 80, cae a:

```text
http://<ip-raspberry>:8080/
```

Prueba desde el móvil o navegador:

```text
http://<ip-raspberry>:8080/remote
```

## 5. Configurar Android

Instala la APK debug actual:

```text
mobile/app/build/outputs/apk/debug/app-debug.apk
```

En la app:

```text
PiFinder Remote -> Base URL
```

Pon una de estas:

```text
http://<ip-raspberry>
http://<ip-raspberry>:8080
```

Pulsa:

```text
Test Connection
```

Debe responder OK y mostrar `mobile-bridge-v0`.

## 6. Capturar Y Subir JPEG Desde Android

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

## 7. Confirmar Que La Raspberry Guardó El Frame

En la Raspberry:

```bash
ls -lh ~/PiFinder_data/mobile/frames
```

Debes ver pares:

```text
<frame_id>.jpg
<frame_id>.json
```

Ver el último JSON:

```bash
ls -t ~/PiFinder_data/mobile/frames/*.json | head -1
```

Opcional:

```bash
python -m json.tool "$(ls -t ~/PiFinder_data/mobile/frames/*.json | head -1)"
```

## 8. Ejecutar Quality Score En La Raspberry

Desde la raíz del repo:

```bash
source python/.venv/bin/activate
python PiFinder_lite/score_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames"
```

Resultados esperados:

```text
Scored N JPEG frames
Accepted for diagnostic solve: N
PiFinder_lite/phase2_camera_analysis/mobile_frame_quality_scores.md
```

Lee el informe:

```bash
cat PiFinder_lite/phase2_camera_analysis/mobile_frame_quality_scores.md
```

## 9. Ejecutar Diagnostic Solve

Desde la raíz del repo:

```bash
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
PiFinder_lite/phase2_camera_analysis/mobile_frame_diagnostic_solves.md
```

Lee el informe:

```bash
cat PiFinder_lite/phase2_camera_analysis/mobile_frame_diagnostic_solves.md
```

## 10. Qué Datos Apuntar En La Issue #42

Copia en la issue:

```text
Pi model:
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

## 11. Interpretación Rápida

### Caso Bueno

```text
Upload OK
Score HIGH/MEDIUM
Diagnostic solve OK
Solve time razonable
```

Conclusión:

```text
La cadena Android -> Pi -> score -> solve funciona.
```

Siguiente paso:

```text
Crear workflow guiado más automático.
```

### Caso Upload Falla

Revisar:

- móvil y Pi en la misma red;
- IP/puerto correctos;
- `/mobile/status`;
- firewall/red;
- logs de PiFinder.

### Caso Score LOW

Posibles causas:

- nubes;
- frame movido;
- fondo demasiado brillante;
- ISO demasiado alto;
- enfoque pobre;
- farolas/obstrucciones.

Repetir con cielo más oscuro o mejor apoyo.

### Caso Score HIGH/MEDIUM Pero Solve Falla

Revisar:

- FOV metadata;
- camera ID;
- orientación;
- si el frame tiene estrellas reales;
- probar `--solve-timeout-ms 3000`;
- repetir con móvil fijo.

## 12. Guardrail

Esta prueba es diagnóstica.

No debe:

- alimentar el integrator;
- actualizar apuntado vivo;
- reemplazar el solver clásico;
- asumir todavía que la cámara móvil ya es producción.
