# FieldScribe: Offline Voice & Manual Text-to-Structured Clinical Note Generator

**Jatayu Season 6 · Use Case: Field-to-Record · Team Codecrafters**  
**Authors**: Ojha Architha · Adina Isran · Godishala Kruthik Roshan  

[![Live Demo](https://img.shields.io/badge/Live%20App-Firebase%20Hosting-blue?style=for-the-badge&logo=firebase&logoColor=white)](https://fieldscribe-voice-to-text.web.app)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/kruthikroshan/Field-to-Record-Voice-to-Structured-Clinical-Note-Generator)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Standards](https://img.shields.io/badge/Interoperability-HL7%20FHIR%20R4-orange.svg)](https://hl7.org/fhir/)
[![Security](https://img.shields.io/badge/Integrity-SHA--256%20Audit%20Chain-teal.svg)](#cryptographic-audit-chain)
[![Tests](https://img.shields.io/badge/Tests-24%20Passed-brightgreen.svg)](#running-tests)

> **🚀 Live Web Deployment**: [https://fieldscribe-voice-to-text.web.app](https://fieldscribe-voice-to-text.web.app)  
> **💻 Source Code Repository**: [https://github.com/kruthikroshan/Field-to-Record-Voice-to-Structured-Clinical-Note-Generator](https://github.com/kruthikroshan/Field-to-Record-Voice-to-Structured-Clinical-Note-Generator)  
> **🔥 Firebase Project Console**: [https://console.firebase.google.com/project/fieldscribe-voice-to-text/overview](https://console.firebase.google.com/project/fieldscribe-voice-to-text/overview)

---


## 📌 Executive Summary

During critical medical emergencies—such as cardiac arrests, trauma resuscitations, and mass-casualty incidents—emergency medical responders (EMTs, paramedics, flight nurses) operate under intense cognitive load in network dead-zones (e.g. basements, tunnels, rural highways, disaster zones). 

Current emergency documentation relies heavily on memory or scribbled notes on gloves and tape, leading to:
- **Delayed & incomplete charting**: Vital medication administration times and dosages are often reconstructed hours later.
- **Medication dosage errors**: Accidental misinterpretation of spoken verbal orders under stress.
- **Lost chain of custody**: Inability to prove exact sequence and timestamps of interventions for legal, billing, and clinical handover.

**FieldScribe** solves this problem as a **100% offline, on-device clinical documentation engine**. It converts spoken audio or manual text entries into structured, validated medication and procedure records, anchors each intervention in a **tamper-evident SHA-256 cryptographic audit chain**, and generates both interoperable **HL7 FHIR R4 JSON bundles** and court-ready **PDF incident summaries**.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FIELD DOCUMENTATION ENGINE                      │
└────────────────────────────────────────────────────────────────────────┘
          │                                              │
          ▼ [Audio / Voice]                              ▼ [Manual Typing]
   Microphone / WAV                               Text Box / Quick Snippets
          │                                       / Structured Form
          ▼                                              │
  faster-whisper ASR (int8 CPU)                          │
  (Offline Neural Speech-to-Text)                        │
          │                                              │
          └──────────────────────┬───────────────────────┘
                                 │
                                 ▼
                     Text Normalization Pipeline
                     (Numbers, units, timestamps)
                                 │
                                 ▼
                   Clinical Rule-Based NER Engine
              (Drugs, doses, routes, procedures, typos)
                                 │
                                 ▼
                    Safety & Validation Filter
             (Dose ranges, negation detection, missing data)
                                 │
                                 ▼
                   Clinician Verification Screen
                  (Review, edit, untick, add manual)
                                 │
                                 ▼
                  SHA-256 Hash Chain Generator
                   (Immutable tamper-evident ledger)
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
     HL7 FHIR Bundle         PDF Report         Store & Forward
    (FHIR-lite R4 JSON)    (ReportLab Note)     (Hospital EHR Sync)
```

---

## ✨ Key Features & Capabilities

### 1. 🎙️ Offline Speech-to-Text (ASR)
- **Local Neural Inference**: Powered by `faster-whisper` (`base.en` model running with int8 quantization on standard CPUs).
- **Zero Cloud Latency & Zero Leakage**: Operates completely disconnected from the Internet; no audio or patient data ever leaves the local device.
- **Browser Mic Recording**: Built-in `MediaRecorder` audio capture with live recording timers and real-time playback previews.

### 2. ✍️ Robust Manual Typing & Clinical Shortcuts
- **Dual-Mode Input**: Seamlessly toggle between natural language notes and direct structured field forms.
- **Emergency Snippets**: 1-click clinical insertion chips (`⏱️ Current Time`, `+ IV Access`, `+ Epi 1 mg IV`, `+ Aspirin 324 mg PO`, `+ Defib 200 J`, `+ Normal Saline`).
- **Dynamic Table Additions**: Add, edit, or delete medications and procedures directly inside the review table.

### 3. 🧠 Clinical NER & Negation Detection
- **Entity Extraction**: Rule-based regex and clinical lexicon matching that maps spoken aliases (e.g., *"epi"* &rarr; Epinephrine, *"morphin"* &rarr; Morphine) to canonical clinical names.
- **Levenshtein Typo Tolerance**: Accurately corrects common transcription and spelling slips without inventing hallucinated drugs.
- **Negation Awareness**: Detects patient refusals (e.g. *"patient refused aspirin"*) and flags them with safety warnings rather than recording them as administered doses.

### 4. ⚠️ Clinical Safety Validation Engine
- Flags unusual or out-of-protocol doses (`DOSE_OUT_OF_RANGE`).
- Catches mismatched administration units (`UNIT_MISMATCH`).
- Warns of omitted routes or missing administration times (`ROUTE_MISSING`, `TIME_MISSING`).
- High-visibility color-coded badges ensure mandatory human-in-the-loop review prior to ledger commitment.

### 5. 🔒 Cryptographic SHA-256 Audit Chain
- Implements a tamper-evident blockchain-style hash chain:
  $$\text{Hash}_i = \text{SHA-256}(\text{Hash}_{i-1} \parallel \text{Index}_i \parallel \text{Timestamp}_i \parallel \text{Payload}_i)$$
- Any modification, deletion, or reordering of historical interventions breaks chain validation immediately.
- 1-click cryptographic re-verification in the UI and CLI.

### 6. 🌐 Interoperability & Output Hub
- **HL7 FHIR-lite R4**: Serializes entries into standard `Bundle`, `MedicationAdministration`, and `Procedure` JSON resources.
- **In-App FHIR Inspector**: Inspect formatted JSON bundles in-app with syntax highlighting and 1-click clipboard copy.
- **Printable PDF Note**: Automatically compiles shaded, timestamped clinical notes using ReportLab.
- **Store-and-Forward Hospital EHR Sync**: Queues outbound data and synchronizes to receiving hospital endpoints when cellular/Wi-Fi connection is re-established.

---

## 🛠️ Technology Stack

| Layer | Technologies | Rationale |
|---|---|---|
| **Core Runtime** | Python 3.12+ | High reliability, cross-platform portability across Windows, Linux, and macOS. |
| **Web Server** | Flask 3.1+ | Lightweight, local WSGI web server with zero external CDN dependencies. |
| **Speech-to-Text** | `faster-whisper` 1.2+ (CTranslate2) | High-speed, int8 quantized Whisper models running efficiently on CPU without GPU requirements. |
| **Audio Processing** | PyAV (`av<19`), Wave, HTML5 MediaRecorder | Native cross-platform decoding for WAV, WebM, OGG, and MP3 containers. |
| **Clinical NER** | Custom Regular Expressions + Levenshtein Engine | Deterministic, auditable, sub-millisecond entity recognition with zero LLM hallucination risk. |
| **Security & Integrity** | Python `hashlib` (SHA-256) | Mathematically verifiable hash-chaining for tamper detection. |
| **Standards & Interoperability** | HL7 FHIR R4 JSON Schema | Industry-standard healthcare data interchange format. |
| **Document Generation** | ReportLab 5.1+ | Pure Python programmatic vector PDF generator. |
| **User Interface** | Modern Vanilla HTML5, CSS3, JavaScript (ES6) | Sleek clinical dashboard with dark command ribbon, status indicators, and modal dialogs—100% offline resilient. |
| **Quality Assurance** | `pytest` 9.1+ | Automated test suite covering parsing, security, PDF rendering, and web APIs. |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 to 3.12 installed
- Git installed

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/kruthikroshan/Field-to-Record-Voice-to-Structured-Clinical-Note-Generator.git
cd Field-to-Record-Voice-to-Structured-Clinical-Note-Generator

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python run.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000`**

---

## 💻 Command Line Interface (CLI)

FieldScribe includes a complete CLI for headless automation, evaluation, and edge scripting:

```bash
# 1. Run the end-to-end automated demo (generates demo_output/ PDF & FHIR JSON)
python -m fieldscribe.cli demo

# 2. Parse a freeform dictation string to JSON
python -m fieldscribe.cli parse "Gave epi 1 mg IV at 10:42. Aspirin 324 mg PO at 10:44."

# 3. Record an entry directly to an incident ledger
python -m fieldscribe.cli record INC-001 "Defibrillated 200 J at 10:46"

# 4. Verify cryptographic chain integrity
python -m fieldscribe.cli verify INC-001

# 5. Export incident FHIR JSON and PDF to disk
python -m fieldscribe.cli export INC-001 --out ./exported/

# 6. Transcribe an audio recording from CLI
python -m fieldscribe.cli transcribe sample_dictation.wav
```

---

## 🧪 Testing & Evaluation

Run the automated test suite with pytest:
```bash
pytest -v
```
All **24 tests** covering NER extraction, hash tamper detection, negative assertion flags, FHIR generation, and web endpoints will execute:
```
tests/test_ner.py ........                                        [ 33%]
tests/test_chain.py ......                                        [ 58%]
tests/test_fhir.py ....                                           [ 75%]
tests/test_web.py ......                                          [100%]
============================== 24 passed in 2.96s ==============================
```

To evaluate entity recognition against synthetic benchmarks:
```bash
python evaluation/evaluate.py
```

---

## ☁️ Deployment (Firebase Hosting & Google Cloud Run)

FieldScribe is configured for production deployment using **Google Cloud Run** connected directly to **Firebase Hosting**:

### 1. Prerequisites
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`) installed
- [Firebase CLI](https://firebase.google.com/docs/cli) (`firebase-tools`) installed

### 2. Deploy Container to Cloud Run
From the project root:
```bash
gcloud run deploy fieldscribe \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

### 3. Deploy to Firebase Hosting
1. Login to Firebase CLI:
   ```bash
   npx firebase-tools login
   ```
2. Set active account and project:
   ```bash
   npx firebase-tools login:use 2303A52339@sru.edu.in
   npx firebase-tools use --add fieldscribe-voice-to-text
   ```
3. Deploy static web suite:
   ```bash
   npx firebase-tools deploy --only hosting
   ```
Your app is live and globally accessible at: **[https://fieldscribe-voice-to-text.web.app](https://fieldscribe-voice-to-text.web.app)** (Console: [https://console.firebase.google.com/project/fieldscribe-voice-to-text/overview](https://console.firebase.google.com/project/fieldscribe-voice-to-text/overview)).


## 📂 Project Directory Structure

```
FieldScribe/
├── fieldscribe/                  # Core package
│   ├── asr.py                    # Offline Whisper/Vosk speech-to-text integration
│   ├── chain.py                  # SHA-256 cryptographic audit chain logic
│   ├── cli.py                    # Command-line interface commands
│   ├── config.py                 # System paths, models, and thresholds
│   ├── fhir.py                   # HL7 FHIR-lite R4 Bundle serializer
│   ├── lexicon.py                # Medication aliases, routes, procedures, ranges
│   ├── ner.py                    # Rule-based Clinical NER & negation detector
│   ├── normalize.py              # Spoken number and unit normalizer
│   ├── pdfgen.py                 # ReportLab clinical PDF generator
│   ├── store.py                  # Atomic offline JSON storage
│   ├── sync.py                   # Store-and-forward EHR synchronization
│   ├── validator.py              # Clinical safety and dose protocol checker
│   └── web/                      # Web application
│       ├── app.py                # Flask application & JSON API routes
│       └── templates/
│           └── index.html        # Clinical Suite dashboard interface
├── evaluation/                   # Evaluation dataset and F1 score benchmark
│   └── evaluate.py
├── tests/                        # 24 pytest unit & integration tests
│   ├── test_chain.py
│   ├── test_fhir.py
│   ├── test_ner.py
│   └── test_web.py
├── docs/                         # Architecture slides and solution documents
├── requirements.txt              # Production dependency specifications
├── run.py                        # Web application entry point
├── .gitignore                    # Git exclusion rules
└── README.md                     # Comprehensive project documentation
```

---

## ⚖️ Clinical Disclaimer & Ethics

> **Notice**: FieldScribe is a prototype developed for emergency clinical workflow evaluation and research. Reference dose limits and medication dictionaries provided in the demonstrator are illustrative and require protocol calibration and medical director sign-off prior to real-world patient triage. FieldScribe is designed with a **human-in-the-loop requirement**—no record is permanently committed to an audit chain without explicit practitioner confirmation.

---

## 👥 Authors & Acknowledgments

- **Ojha Architha**
- **Adina Isran**
- **Godishala Kruthik Roshan**

*Developed for Jatayu Season 6 · Field-to-Record Challenge · Team Codecrafters*
