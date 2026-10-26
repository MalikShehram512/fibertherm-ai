# FiberTherm AI

**AI-assisted fiber laser thermal modeling and visualization**

FiberTherm AI is an exploratory research portfolio project for studying simplified thermal behavior in ytterbium-doped fiber lasers. It combines numerical modeling, interactive visualizations, parameter exploration, pump-split optimization, and optional LLM-assisted interpretation.

## Research Motivation

High-power ytterbium-doped double-clad (YDDC) fiber lasers can experience thermal effects caused by energy conversion and pump absorption. Understanding how pump configuration and model parameters influence heat deposition is important when studying thermal management.

This project provides an interactive environment for exploring these relationships and developing a foundation for more detailed computational modeling.

## Features

- Interactive thermal simulation with adjustable parameters
- Forward and backward pump power profiles
- Estimated heat deposition along the fiber
- Temperature profile visualization
- Idealized uniform-heating benchmark
- Grid-search exploration of forward/backward pump splitting
- Interactive diagrams describing the calculation workflow
- CSV export of simulation data
- Optional AI-generated explanations of selected results
- Streamlit web interface

## Technology Stack

- Python
- Streamlit
- NumPy
- Pandas
- Plotly
- OpenAI API (optional)

## Model Overview

The current two-end pumping model estimates the remaining pump power along a fiber using exponential attenuation:

P_forward(z) = P_forward(0) exp(-alpha z)

P_backward(z) = P_backward(L) exp(-alpha (L - z))

The absorption coefficient is converted from decibels per meter to an exponential attenuation coefficient.

The model estimates absorbed pump power per unit length and applies a simplified quantum-defect heat fraction:

heat fraction = max(0, 1 - pump wavelength / signal wavelength)

An effective radial thermal resistance is then used to estimate a temperature rise above ambient temperature.

The optimization function evaluates a grid of forward/backward pump-power splits and returns the split with the lowest estimated peak temperature under the current model assumptions.

## Scientific Limitations

**This is an exploratory simplified model, not a validated reproduction of a published fiber-laser model.**

The current implementation does not fully model:

- Coupled pump and signal propagation
- Laser gain, inversion, and stimulated emission
- Detailed cladding-pump absorption
- Longitudinal and radial temperature coupling
- Temperature-dependent material properties
- Cooling boundary conditions and complete heat-transfer physics
- Experimental uncertainty or validation against measured results

The uniform-heating function is an idealized benchmark. It is not a physical distributed-pumping solver.

Numerical outputs should be interpreted as illustrative estimates. They should not be reported as validated research findings without checking the equations, parameters, assumptions, and results against authoritative sources or experimental data.

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/fibertherm-ai.git
cd fibertherm-ai
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Launch the application

```bash
streamlit run app.py
```

Streamlit will display a local URL in your terminal.

## Optional AI Explainer Setup

The simulation and visualization features work without an API key.

To enable AI explanations, create a local file at `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-api-key"
```

Keep this file private and do not commit it to GitHub.

On Streamlit Community Cloud, add `OPENAI_API_KEY` under the deployed app's Secrets settings instead of uploading the local secrets file.

API usage may incur charges depending on your account and usage.

## Deployment

1. Push the project files to a GitHub repository.
2. Sign in to Streamlit Community Cloud.
3. Create a new app and select the repository.
4. Set the main file path to `app.py`.
5. Add the optional API key through the app's Secrets settings.
6. Deploy and test the public application.

## Future Research Development

Potential next steps include:

- Extracting and implementing the governing equations from the target paper
- Validating numerical results against published figures or tables
- Implementing a physically grounded distributed-pump propagation model
- Adding parameter sensitivity analysis
- Comparing model predictions with experimental or trusted reference data
- Adding retrieval-augmented generation (RAG) over relevant research papers

## Project Status

Exploratory prototype — under development.

The model, assumptions, and numerical results require further verification before research-grade conclusions can be drawn.
