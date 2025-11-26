# Simulador de automatización FCI

Este repositorio incluye un pequeño CLI (`app.py`) que lee el archivo Excel `FCI Abril 2025.xlsx` y reproduce de forma simplificada la lógica documentada en `TGN - Documentación Scripts Excel.docx`.

## Cómo ejecutar

```bash
python app.py
```

Pasos detallados:

1. Asegúrate de tener **Python 3.10+** instalado (no se requieren dependencias externas).
2. Clona o descarga este repositorio y ubícate en la carpeta raíz `TGV-PoC-TGN`.
3. Ejecuta `python app.py` desde la raíz; el script leerá el archivo Excel incluido `FCI Abril 2025.xlsx` y mostrará el resumen por consola.
4. Si quieres usar otro archivo con la misma estructura, pasa la ruta con `--file`:

   ```bash
   python app.py --file /ruta/a/otro_archivo.xlsx
   ```

El comando genera un resumen que incluye:

- Saldo de cuotapartes obtenido aplicando una cola FIFO a las suscripciones y rescates de la hoja `SBSAhorroPesosClaseD`.
- Saldo valorizado usando el último valor de cuotapartes informado en la hoja de movimientos.
- Totales de valuación impositiva y contable tomando como referencia la hoja `FCI Ganancias`.
- Total de rentas de fuente argentina a partir de la hoja `Rescates IIBB`.

Puedes usar otro archivo XLSX con el flag `--file` si mantiene la misma estructura básica de hojas y columnas.
