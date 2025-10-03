# Sharko: A Guardian of the Ocean

## 🌊 Dive into the Future of Shark Conservation

![Sharko Project Header Image](https://raw.githubusercontent.com/ShougataDas/Sharko/main/images/sharko_banner.png)  (*You'll want to create or generate a compelling banner image for your repo!*)

**Sharko** is an innovative, AI-powered project dedicated to enhancing shark conservation efforts by predicting dynamic shark habitats and foraging hotspots. Leveraging cutting-edge NASA Earth observation data and advanced machine learning, Sharko aims to provide actionable intelligence for marine protected areas, reduce bycatch, and deepen our understanding of these critical apex predators.

This repository contains the core code for the Sharko predictive models, data processing, and visualization tools, along with the conceptual design for our future-forward **Metabolic Kill Tag (MKT)**.

## ✨ Features

* **Dynamic Habitat Prediction:** Utilizes a cascaded LightGBM model stack to predict shark presence probabilities (`hotspots`) for any location and future date, integrating Sea Surface Temperature (SST), Sea Surface Height Anomaly (SSHA), and Chlorophyll-a data.
* **Two-Tiered AI Architecture:**
    * **Tier 1:** Environmental forecasting models predict future SST, SSHA, and Chlorophyll-a.
    * **Tier 2:** Shark presence classifier uses these predicted environmental conditions to identify potential shark habitats.
* **Interactive Web Application (Operational):** A user-friendly web interface allows for real-time visualization of predicted shark hotspots, empowering conservationists and stakeholders with data-driven insights.
* **Metabolic Kill Tag (MKT) Concept:** A revolutionary ingestible pH sensor tethered to an external satellite tag, designed to confirm actual predation events in real-time and map precise foraging grounds.
* **Comprehensive Data Pipeline:** Robust scripts for data acquisition, cleaning, feature engineering, and model training from NASA satellites (MODIS), Copernicus Marine Service (AVISO), and OBIS.
* **Model Evaluation & Visualization:** Tools to analyze model performance, feature importance, and interactive mapping of predictions.

## 🚀 Getting Started

To explore the Sharko project, clone this repository and follow the instructions below.

### Prerequisites

* Python 3.8+
* `pip` package manager

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/ShougataDas/Sharko.git](https://github.com/ShougataDas/Sharko.git)
    cd Sharko
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You will need to create a `requirements.txt` file by running `pip freeze > requirements.txt` after installing all dependencies, or manually list them.)*

### Data & Models

The predictive models are pre-trained and expected to be located in a specific directory.

1.  **Download Pre-trained Models:**
    * Your pre-trained models (`sst_model_new.joblib`, `ssha_model_robust_dependent_tuned.joblib`, `chloro_model_log_independent_tuned.joblib`, `shark_presence_model_tuned.joblib`) should be placed in the `final_model_data/` directory within your Google Drive, as indicated by `MODEL_PATH = '/content/drive/MyDrive/final_model_data/'` in the scripts.
    * **Important:** The `ssha_model_robust_dependent_tuned.joblib` file contains both the trained SSHA model *and* its target `RobustScaler`. Ensure this file is saved correctly as a dictionary containing both.

    *(Consider adding a direct download link for these `.joblib` files to your README for easier setup, e.g., via Google Drive shareable link or Zenodo.)*

### Running the Visualizations

The `visualization.py` script demonstrates how to load the models, run the prediction cascade, and generate insightful plots.

1.  **Ensure Google Drive is mounted (if running in Colab):**
    ```python
    from google.colab import drive
    drive.mount('/content/drive')
    ```
    *(If running locally, adjust `MODEL_PATH` in `visualization.py` to point to your local model directory.)*

2.  **Execute the visualization script:**
    ```bash
    python visualization.py
    ```

    This script will:
    * Generate a grid of prediction points for a specific date (May 15th, 2025).
    * Run the full predictive cascade to forecast environmental conditions and shark probabilities.
    * Save an interactive map of shark hotspots as `shark_hotspots_map.html`.
    * Save a feature importance plot for the shark presence model as `shark_feature_importance.png`.
    * Attempt to generate an ROC curve (`shark_roc_curve.png`). *(Note: For a valid ROC curve, ensure you replace the dummy data generation with your actual `X_test` and `y_test` from your training pipeline.)*

## ⚙️ Model Architecture

Sharko employs a sophisticated two-tiered machine learning architecture:

### Tier 1: Environmental Forecasting Models

A set of **LightGBM Regressors** predict future oceanographic conditions:

* **Sea Surface Temperature (SST) Model:** Predicts SST based on `latitude`, `longitude`, `day_sin`, `day_cos`.
* **Sea Surface Height Anomaly (SSHA) Model:** Predicts SSHA based on `latitude`, `longitude`, `predicted_sst` (from the SST model), `day_sin`, `day_cos`. This model's *target* (`ssha` values) is pre-scaled using `RobustScaler` and then inverse-transformed after prediction.
* **Chlorophyll-a Model:** Predicts Chlorophyll-a based on `latitude`, `longitude`, `day_sin`, `day_cos`, `predicted_sst`, and `predicted_ssha`.

These models are optimized using Optuna for precise future environmental predictions.

### Tier 2: Shark Presence Prediction Model

A highly-tuned **LightGBM Classifier** takes the predicted environmental conditions from Tier 1, along with geographical and temporal features, to predict the probability of shark presence. This model directly outputs the "shark hotspots" visualized in the web application.

## 🔬 Metabolic Kill Tag (MKT) Concept

Beyond prediction, Sharko envisions a groundbreaking hardware solution for real-time foraging data: the **Metabolic Kill Tag**.

* **Purpose:** To confirm actual predation events and precisely map shark hunting grounds, addressing the "highway vs. hunting ground" challenge.
* **Design:** A two-part system:
    * **External Module:** Dorsal fin-mounted, containing IMU, on-board AI (ARM Cortex-M), battery, Fastloc-GPS, and Argos satellite modem.
    * **Internal Module:** Ingestible pH sensor pill, connected to the external module via a Kevlar-reinforced tether.
* **Operation:** The IMU detects predation attempts, triggering the pH sensor. On-board AI confirms a kill via a characteristic pH spike and transmits a compact "kill confirmed" data packet when the shark surfaces.
* **Future Vision:** Integration of eDNA analysis for specific prey identification.

## 🛰️ NASA Resources & Data

Sharko is built upon crucial NASA Earth observation data:

* **MODIS (Aqua/Terra) Satellite Data:**
    * Sea Surface Temperature (SST)
    * Chlorophyll-a concentration
* **Copernicus Marine Service (AVISO):** Sea Surface Height Anomaly (SSHA) data.
* **Ocean Biodiversity Information System (OBIS):** Global shark occurrence records (`Occurrence.tsv`).

## 🤝 Contributing

We welcome contributions to Sharko\! If you're passionate about marine conservation, AI, or innovative hardware design, please consider:

* Forking the repository.
* Improving existing models or adding new features.
* Enhancing visualizations or the web application.
* Prototyping aspects of the Metabolic Kill Tag.
* Reporting bugs or suggesting improvements.

Please refer to our `CONTRIBUTING.md` (if you create one) for detailed guidelines.

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the `LICENSE` file for details.

##  acknowledgements

This project was developed as part of the NASA Space Apps Challenge [Year] [Challenge Name, e.g., "Sharks from Space"]. We extend our gratitude to NASA and the challenge organizers for providing the data and the platform to innovate for global challenges.

---
