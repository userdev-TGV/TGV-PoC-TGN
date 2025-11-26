"""Aplicación CLI que simula la automatización documentada usando el archivo Excel del repositorio.

El objetivo es mostrar cómo se calcularían saldos, valores y totales
sin dependencias externas, leyendo directamente el XLSX con la librería estándar.
"""
from __future__ import annotations

import argparse
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import xml.etree.ElementTree as ET

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


# --------------------------- utilidades de parsing ---------------------------

def column_index_from_ref(cell_ref: str) -> int:
    """Convierte referencias de celda ("A1", "BC5") en índices de columna base 0."""
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return len(cell_ref)  # fallback simple
    col = 0
    for ch in match.group(1):
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col - 1


def normalize_number(text: str) -> Optional[float]:
    """Convierte números con separadores latinoamericanos a float.

    - Elimina separadores de miles (.).
    - Usa la coma como separador decimal cuando existe.
    - Devuelve None si el valor no es numérico.
    """
    if text is None:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace(" ", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


# ----------------------------- lector de XLSX -------------------------------

class Workbook:
    def __init__(self, path: Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(path)
        self._zip = zipfile.ZipFile(self.path)
        self.shared_strings = self._load_shared_strings()
        self.sheets = self._load_sheet_map()

    def _load_shared_strings(self) -> List[str]:
        strings: List[str] = []
        with self._zip.open("xl/sharedStrings.xml") as fh:
            root = ET.fromstring(fh.read())
        for si in root.findall(f"{{{NS}}}si"):
            text = "".join(t.text or "" for t in si.iter(f"{{{NS}}}t"))
            strings.append(text)
        return strings

    def _load_sheet_map(self) -> Dict[str, str]:
        """Retorna un dict {nombre_hoja: ruta_xml_relativa}."""
        with self._zip.open("xl/workbook.xml") as fh:
            wb_root = ET.fromstring(fh.read())
        with self._zip.open("xl/_rels/workbook.xml.rels") as fh:
            rel_root = ET.fromstring(fh.read())
        rels = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rel_root}
        sheets: Dict[str, str] = {}
        for sheet in wb_root.find(f"{{{NS}}}sheets"):
            name = sheet.attrib["name"]
            rel_id = sheet.attrib[f"{{http://schemas.openxmlformats.org/officeDocument/2006/relationships}}id"]
            sheets[name] = rels[rel_id]
        return sheets

    def read_sheet(self, name: str) -> List[List[str]]:
        """Lee una hoja en forma de matriz de strings."""
        target = self.sheets[name]
        with self._zip.open(f"xl/{target}") as fh:
            root = ET.fromstring(fh.read())
        rows: List[List[str]] = []
        for row in root.iter(f"{{{NS}}}row"):
            current: List[str] = []
            for cell in row.findall(f"{{{NS}}}c"):
                ref = cell.attrib.get("r", "")
                idx = column_index_from_ref(ref)
                while len(current) < idx:
                    current.append("")
                value = ""
                node = cell.find(f"{{{NS}}}v")
                if node is not None:
                    value = node.text or ""
                    if cell.attrib.get("t") == "s":
                        value = self.shared_strings[int(value)]
                current.append(value)
            rows.append(current)
        return rows


# ------------------------- estructuras de simulación ------------------------

@dataclass
class Movement:
    fecha: str
    concepto: str
    cuotapartes: float
    valor: Optional[float]
    importe: Optional[float]


class AutomationSimulator:
    def __init__(self, workbook: Workbook):
        self.workbook = workbook

    def run(self) -> Dict[str, float]:
        movimientos = self._load_movements()
        saldo_cuotas, saldo_valorizado = self._simulate_fifo(movimientos)
        totales_fci = self._sum_table("FCI Ganancias")
        totales_rescates = self._sum_table("Rescates IIBB")
        return {
            "saldo_cuotapartes": saldo_cuotas,
            "saldo_valorizado": saldo_valorizado,
            "total_valuacion_impositiva": totales_fci.get("Valuación Impositiva", 0.0),
            "total_valuacion_contable": totales_fci.get("Valuación Contable", 0.0),
            "total_rentas_fuente_arg": totales_rescates.get("Rdo Imp X VTA", 0.0),
        }

    def _load_movements(self) -> List[Movement]:
        rows = self.workbook.read_sheet("SBSAhorroPesosClaseD")
        # Buscar cabecera
        header: Optional[List[str]] = None
        data_rows: List[List[str]] = []
        for row in rows:
            if not any(row):
                continue
            if header is None and len(row) >= 4:
                header = row
                continue
            if header:
                data_rows.append(row)
        movements: List[Movement] = []
        for row in data_rows:
            if len(row) < 4:
                continue
            fecha, concepto = row[0], row[1]
            if concepto.lower().startswith("total"):
                continue
            cuotapartes = normalize_number(row[2]) or 0.0
            valor = normalize_number(row[3])
            importe = normalize_number(row[4]) if len(row) > 4 else None
            movements.append(Movement(fecha, concepto, cuotapartes, valor, importe))
        return movements

    def _simulate_fifo(self, movements: Iterable[Movement]) -> Tuple[float, float]:
        """Aplica un FIFO simple sobre suscripciones/rescates para estimar saldos."""
        lotes: List[Tuple[float, float]] = []  # (cuotas, valor)
        ultimo_valor: float = 0.0
        for mov in movements:
            if mov.valor is not None:
                ultimo_valor = mov.valor
            if mov.concepto.upper().startswith("SUSCRIPCION"):
                lotes.append((mov.cuotapartes, mov.valor or ultimo_valor))
            elif mov.concepto.upper().startswith("RESCATE"):
                faltante = abs(mov.cuotapartes)
                while faltante > 1e-9 and lotes:
                    cuotas, valor = lotes[0]
                    toma = min(cuotas, faltante)
                    cuotas -= toma
                    faltante -= toma
                    if cuotas <= 1e-9:
                        lotes.pop(0)
                    else:
                        lotes[0] = (cuotas, valor)
        saldo_cuotas = sum(c for c, _ in lotes)
        saldo_valorizado = saldo_cuotas * ultimo_valor
        return saldo_cuotas, saldo_valorizado

    def _sum_table(self, sheet_name: str) -> Dict[str, float]:
        rows = self.workbook.read_sheet(sheet_name)
        # detect header on third row usually
        header: List[str] = []
        totals: Dict[str, float] = {}
        for row in rows:
            if not row:
                continue
            if header and len(row) == len(header):
                for name, value in zip(header, row):
                    number = normalize_number(value)
                    if number is not None:
                        totals[name] = totals.get(name, 0.0) + number
            elif not header:
                # buscar fila que tenga al menos 2 columnas de texto
                texts = [cell for cell in row if cell]
                if len(texts) >= 2:
                    header = row
        return totals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulador de automatización para FCI")
    parser.add_argument(
        "--file",
        default="FCI Abril 2025.xlsx",
        type=Path,
        help="Archivo XLSX de entrada (por defecto se usa el que viene en el repo)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    workbook = Workbook(args.file)
    simulator = AutomationSimulator(workbook)
    report = simulator.run()
    print("\n== Resumen de simulación ==")
    print(f"Saldo de cuotapartes: {report['saldo_cuotapartes']:.2f}")
    print(f"Saldo valorizado (FIFO): {report['saldo_valorizado']:.2f}")
    print("Totales consolidados de FCI:")
    print(
        f"  Valuación Impositiva: {report['total_valuacion_impositiva']:.2f}\n"
        f"  Valuación Contable:   {report['total_valuacion_contable']:.2f}"
    )
    print(f"Rentas de fuente argentina (IIBB): {report['total_rentas_fuente_arg']:.2f}")


if __name__ == "__main__":
    main()
