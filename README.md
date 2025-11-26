El proyecto ofrece dos formas de reproducir la automatización documentada en `TGN - Documentación Scripts Excel.docx` usando el
archivo `FCI Abril 2025.xlsx` incluido en el repositorio:

1. **CLI** (`app.py`) para obtener los cálculos por consola.
2. **Aplicación web** (`web_app.py`) con frontend en React que permite cargar archivos y ver métricas en el navegador.

## Requisitos

- Python 3.10+
- Dependencias del proyecto:

  ```bash
  pip install -r requirements.txt
  ```

> Si tu entorno bloquea descargas externas, asegurate de tener Flask disponible antes de ejecutar el servidor.

## Ejecución rápida del CLI

# Simulador de automatización FCI

Este repositorio incluye un pequeño CLI (`app.py`) que lee el archivo Excel `FCI Abril 2025.xlsx` y reproduce de forma simplificada la lógica documentada en `TGN - Documentación Scripts Excel.docx`.

## Cómo ejecutar


```bash
python app.py
```

Pasos detallados:

1. Ubícate en la carpeta raíz `TGV-PoC-TGN`.
2. Ejecuta `python app.py`; el script leerá el archivo `FCI Abril 2025.xlsx` y mostrará el resumen por consola.
3. Para usar otro archivo con la misma estructura, pasa la ruta con `--file`:

1. Asegúrate de tener **Python 3.10+** instalado (no se requieren dependencias externas).
2. Clona o descarga este repositorio y ubícate en la carpeta raíz `TGV-PoC-TGN`.
3. Ejecuta `python app.py` desde la raíz; el script leerá el archivo Excel incluido `FCI Abril 2025.xlsx` y mostrará el resumen por consola.
4. Si quieres usar otro archivo con la misma estructura, pasa la ruta con `--file`:


   ```bash
   python app.py --file /ruta/a/otro_archivo.xlsx
   ```

El CLI genera un resumen con:

- Saldo de cuotapartes aplicando FIFO a suscripciones y rescates (`SBSAhorroPesosClaseD`).
- Saldo valorizado usando el último valor de cuotapartes informado.
- Totales de valuación impositiva y contable (`FCI Ganancias`).
- Total de rentas de fuente argentina (`Rescates IIBB`).

## Aplicación web con frontend React

La app web expone una API en Flask y sirve una única página React (sin necesidad de Node ni builds) que permite:

- Subir un XLSX propio o usar el de ejemplo `FCI Abril 2025.xlsx`.
- Disparar la simulación y visualizar los saldos, valuaciones y rentas calculadas.

### Cómo ejecutarla

1. Instala dependencias si aún no lo hiciste:

   ```bash
   pip install -r requirements.txt
   ```

2. Levanta el servidor en modo desarrollo (por defecto en `http://localhost:5000`):

   ```bash
   flask --app web_app run
   ```

3. Abrí el navegador en `http://localhost:5000` y cargá el XLSX desde el selector, o presioná **"Usar ejemplo"** para ejecutar con
   el archivo incluido.

### Notas sobre el frontend

- El React bundle se carga desde CDN (sin toolchains adicionales) y consume el endpoint `POST /api/simulate` para procesar el XLSX.
- La UI muestra estado de procesamiento, nombre del último archivo procesado y las métricas consolidadas.

La web usa la misma lógica del CLI, por lo que los cálculos de saldos y totales coinciden con la automatización original.
El comando genera un resumen que incluye:

- Saldo de cuotapartes obtenido aplicando una cola FIFO a las suscripciones y rescates de la hoja `SBSAhorroPesosClaseD`.
- Saldo valorizado usando el último valor de cuotapartes informado en la hoja de movimientos.
- Totales de valuación impositiva y contable tomando como referencia la hoja `FCI Ganancias`.
- Total de rentas de fuente argentina a partir de la hoja `Rescates IIBB`.

Puedes usar otro archivo XLSX con el flag `--file` si mantiene la misma estructura básica de hojas y columnas.
