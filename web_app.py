from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template, request

from app import AutomationSimulator, Workbook

BASE_DIR = Path(__file__).parent
SAMPLE_XLSX = BASE_DIR / "FCI Abril 2025.xlsx"

app = Flask(__name__)
app.secret_key = "dev-key"


def run_simulation(file_path: Path) -> dict:
    workbook = Workbook(file_path)
    simulator = AutomationSimulator(workbook)
    return simulator.run()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", sample_name=SAMPLE_XLSX.name)


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    use_default = request.form.get("use_default") == "1"
    uploaded = request.files.get("file")
    filename: Optional[str] = None
    file_path: Optional[Path] = None

    if use_default:
        file_path = SAMPLE_XLSX
        filename = SAMPLE_XLSX.name
    elif uploaded and uploaded.filename:
        if not uploaded.filename.lower().endswith(".xlsx"):
            return jsonify({"error": "Solo se aceptan archivos XLSX"}), 400
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            uploaded.save(tmp.name)
            file_path = Path(tmp.name)
            filename = uploaded.filename
    else:
        return jsonify({"error": "Subí un archivo o usa el ejemplo incluido"}), 400

    results = run_simulation(file_path)
    return jsonify({"filename": filename, "results": results})


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    app.run(debug=True)
