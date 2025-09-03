from flask import Flask, request, jsonify, render_template
from ai_component import *

# ----------------------------
# Flask app & routes
# ----------------------------
app = Flask(__name__)

import os
import tempfile
import pdfplumber
import docx
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {"pdf", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_file(file_path):
    ext = file_path.rsplit(".", 1)[1].lower()
    text = ""
    if ext == "pdf":
        # First try pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
        # Fallback to PyMuPDF
        if not text.strip():
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text("text") + "\n"
    elif ext == "docx":
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---- Company endpoints ----
@app.route("/company", methods=["POST"])
def create_company():
    data = request.get_json(force=True)
    company_id = int(data.get("company_id"))
    name = data.get("name", f"company-{company_id}")
    requirements = data.get("requirements", {})
    companies[company_id] = Company(company_id, name, requirements)
    return jsonify({"message": "company upserted", "company": asdict(companies[company_id])})


@app.route("/company/<int:company_id>", methods=["GET"])
def get_company(company_id: int):
    c = companies.get(company_id)
    if not c:
        return jsonify({"error": "not found"}), 404
    return jsonify(asdict(c))


# ---- Candidate endpoints ----
@app.route("/candidate", methods=["POST"])
def create_candidate():
    data = request.get_json(force=True)
    candidate_id = int(data.get("candidate_id"))
    name = data.get("name", f"candidate-{candidate_id}")
    resume_text = data.get("resume_text", "")
    candidates[candidate_id] = Candidate(candidate_id, name, resume_text)
    return jsonify({"message": "candidate upserted", "candidate": asdict(candidates[candidate_id])})


@app.route("/candidate/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id: int):
    c = candidates.get(candidate_id)
    if not c:
        return jsonify({"error": "not found"}), 404
    return jsonify(asdict(c))


# ---- Analyze endpoints ----
@app.route("/analyze", methods=["POST"])
def analyze_pair():
    """Analyze by passing raw requirements + resume_text.
    Body: { requirements: {...}, resume_text: "..." }
    """
    data = request.get_json(force=True)
    requirements = data.get("requirements", {})
    resume_text = data.get("resume_text", "")

    overall, breakdown = compute_fit(requirements, resume_text)
    quality = resume_quality(resume_text)

    return jsonify({
        "fit_score": overall,
        "fit_breakdown": breakdown,
        "resume_quality": quality,
    })


@app.route("/analyze/by-id", methods=["POST"])
def analyze_by_id():
    """Analyze using stored company_id and candidate_id.
    Body: { company_id: int, candidate_id: int }
    """
    data = request.get_json(force=True)
    company_id = int(data["company_id"])  # will raise if missing
    candidate_id = int(data["candidate_id"])  # will raise if missing

    comp = companies.get(company_id)
    cand = candidates.get(candidate_id)
    if not comp or not cand:
        return jsonify({"error": "company or candidate not found"}), 404

    overall, breakdown = compute_fit(comp.requirements, cand.resume_text)
    quality = resume_quality(cand.resume_text)

    return jsonify({
        "company": {"company_id": comp.company_id, "name": comp.name},
        "candidate": {"candidate_id": cand.candidate_id, "name": cand.name},
        "fit_score": overall,
        "fit_breakdown": breakdown,
        "resume_quality": quality,
    })


# ---- Bulk screening (many candidates for one company) ----
@app.route("/analyze/bulk", methods=["POST"])
def analyze_bulk():
    """
    Screen many candidates against one company's requirements.
    Body: { company_id: int } OR { requirements: {...} }
    Optionally include candidates: [candidate_id,...] To filter.
    """
    data = request.get_json(force=True)
    comp = None
    requirements = data.get("requirements")
    if "company_id" in data:
        comp = companies.get(int(data["company_id"]))
        if not comp:
            return jsonify({"error": "company not found"}), 404
        requirements = comp.requirements

    if not requirements:
        return jsonify({"error": "missing requirements"}), 400

    ids = data.get("candidates") or list(candidates.keys())
    results = []
    for cid in ids:
        cand = candidates.get(int(cid))
        if not cand:
            continue
        score, breakdown = compute_fit(requirements, cand.resume_text)
        quality = resume_quality(cand.resume_text)
        results.append({
            "candidate_id": cand.candidate_id,
            "name": cand.name,
            "fit_score": score,
            "fit_breakdown": breakdown,
            "resume_quality": quality,
        })

    # Sort by fit score desc
    results.sort(key=lambda x: x["fit_score"], reverse=True)
    return jsonify({"results": results, "count": len(results)})


@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        try:
            resume_text = extract_text_from_file(file_path)
        except Exception as e:
            return jsonify({"error": f"Failed to extract text: {str(e)}"}), 500

        quality = resume_quality(resume_text)

        return jsonify({
            "extracted_text": resume_text[:1000],  # Preview only
            "resume_quality": quality
        })

    return jsonify({"error": "Invalid file type (only pdf/docx allowed)"}), 400


@app.route("/companies", methods=["GET"])
def list_companies():
    return jsonify([asdict(c) for c in companies.values()])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/company_page")
def company_page():
    return render_template("company.html")


@app.route("/candidate_page")
def candidate_page():
    return render_template("candidate.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# ----------------------------
# requirements.txt (for reference)
# ----------------------------
# flask
# scikit-learn
# nltk
# textstat
# language_tool_python # optional; requires Java runtime
