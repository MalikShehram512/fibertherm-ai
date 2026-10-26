
"""FiberTherm AI — interactive fiber-laser thermal research dashboard."""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from model import (
    optimize_pump_split,
    simulate_distributed_heating,
    simulate_end_pumped,
)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


st.set_page_config(
    page_title="FiberTherm AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.5rem 1.6rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px;
        margin-bottom: 1rem;
        background: linear-gradient(
            120deg, rgba(40,110,170,.13), rgba(20,160,140,.07)
        );
    }
    .muted {color: #7b8794; font-size: .92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔬 FiberTherm AI")
st.caption(
    "Interactive thermal modeling and AI-assisted interpretation "
    "for ytterbium-doped fiber-laser research"
)

st.markdown(
    """
    <div class="hero">
      <h3>Explore the relationship between pump configuration and heat</h3>
      <p>
        Change the laser and thermal parameters, inspect spatial profiles,
        compare simplified scenarios, and ask an AI assistant to explain
        the resulting plots.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Model parameters")
    st.caption("Change a value to update the simulation.")

    fiber_length_m = st.slider(
        "Fiber length (m)", 0.5, 20.0, 5.0, 0.5
    )
    pump_power_w = st.slider(
        "Total incident pump power (W)", 100, 5000, 1000, 100
    )
    forward_fraction = st.slider(
        "Forward pump fraction", 0.0, 1.0, 0.5, 0.05,
        help="The remaining pump power is assigned to the opposite end.",
    )
    absorption_db_per_m = st.slider(
        "Pump absorption (dB/m)", 0.01, 3.0, 0.5, 0.01
    )
    pump_wavelength_nm = st.slider(
        "Pump wavelength (nm)", 900, 1050, 976, 1
    )
    signal_wavelength_nm = st.slider(
        "Signal wavelength (nm)", 1050, 1150, 1080, 1
    )

    st.divider()
    st.subheader("Thermal assumptions")

    core_radius_um = st.number_input(
        "Core radius (µm)", min_value=1.0, max_value=100.0,
        value=10.0, step=1.0
    )
    thermal_radius_mm = st.number_input(
        "Outer thermal radius (mm)", min_value=0.1, max_value=10.0,
        value=1.0, step=0.1
    )
    thermal_conductivity_w_mk = st.number_input(
        "Effective conductivity (W/m·K)", min_value=0.1,
        max_value=1000.0, value=1.4, step=0.1
    )
    ambient_temperature_c = st.number_input(
        "Ambient temperature (°C)", min_value=-50.0, max_value=100.0,
        value=25.0, step=1.0
    )

    st.divider()
    st.caption(
        "These inputs control a simplified exploratory model. "
        "They are not a substitute for material-specific measurements."
    )


try:
    result = simulate_end_pumped(
        fiber_length_m=fiber_length_m,
        pump_power_w=float(pump_power_w),
        forward_fraction=forward_fraction,
        absorption_db_per_m=absorption_db_per_m,
        pump_wavelength_nm=float(pump_wavelength_nm),
        signal_wavelength_nm=float(signal_wavelength_nm),
        core_radius_um=core_radius_um,
        thermal_radius_mm=thermal_radius_mm,
        thermal_conductivity_w_mk=thermal_conductivity_w_mk,
        ambient_temperature_c=ambient_temperature_c,
    )

    distributed = simulate_distributed_heating(
        fiber_length_m=fiber_length_m,
        pump_power_w=float(pump_power_w),
        absorption_db_per_m=absorption_db_per_m,
        pump_wavelength_nm=float(pump_wavelength_nm),
        signal_wavelength_nm=float(signal_wavelength_nm),
        core_radius_um=core_radius_um,
        thermal_radius_mm=thermal_radius_mm,
        thermal_conductivity_w_mk=thermal_conductivity_w_mk,
        ambient_temperature_c=ambient_temperature_c,
    )
except ValueError as exc:
    st.error(f"Please check the model inputs: {exc}")
    st.stop()


# ---------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------

m1, m2, m3, m4 = st.columns(4)
m1.metric("Peak estimated temperature", f"{result['max_temperature_c']:.2f} °C")
m2.metric("Temperature rise", f"{result['temperature_rise_c']:.2f} °C")
m3.metric("Absorbed pump estimate", f"{result['absorbed_total_w']:.1f} W")
m4.metric("Estimated heat", f"{result['estimated_heat_w']:.1f} W")

st.info(
    "Scientific scope: this dashboard uses simplified equations. "
    "The thermal estimate assumes a constant effective radial thermal "
    "resistance and a quantum-defect heat fraction. It does not solve "
    "the complete laser gain, signal-power, cladding-pump, or radial "
    "temperature equations from the original research paper."
)

tab_overview, tab_sim, tab_diagram, tab_optimize, tab_ai = st.tabs(
    [
        "Overview",
        "Thermal simulation",
        "Diagram studio",
        "Pump optimization",
        "AI explainer",
    ]
)


def make_line_chart(
    x,
    y_series,
    title,
    x_title,
    y_title,
):
    fig = go.Figure()
    for y, name in y_series:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=name,
                line={"width": 3},
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12},
        margin={"l": 20, "r": 20, "t": 70, "b": 20},
    )
    return fig


with tab_overview:
    st.subheader("Simulation overview")
    left, right = st.columns([1.5, 1])

    with left:
        temperature_fig = make_line_chart(
            result["z_m"],
            [
                (result["temperature_c"], "Two-end pump model"),
                (distributed["temperature_c"], "Uniform-heating benchmark"),
            ],
            "Estimated temperature along the fiber",
            "Position along fiber (m)",
            "Temperature (°C)",
        )
        st.plotly_chart(temperature_fig, use_container_width=True)

    with right:
        st.markdown("#### Current assumptions")
        st.write(f"Fiber length: **{fiber_length_m:.2f} m**")
        st.write(f"Incident pump power: **{pump_power_w:.0f} W**")
        st.write(f"Forward fraction: **{forward_fraction:.0%}**")
        st.write(f"Backward fraction: **{1 - forward_fraction:.0%}**")
        st.write(f"Absorption coefficient: **{result['alpha_per_m']:.4f} m⁻¹**")
        st.write(f"Estimated heat fraction: **{result['heat_fraction']:.2%}**")

        st.download_button(
            "Download current simulation (CSV)",
            data=pd.DataFrame(
                {
                    "position_m": result["z_m"],
                    "pump_forward_w": result["pump_forward_w"],
                    "pump_backward_w": result["pump_backward_w"],
                    "pump_total_w": result["pump_total_w"],
                    "absorbed_power_per_m_w_m": result["absorbed_power_per_m"],
                    "heat_per_m_w_m": result["heat_per_m"],
                    "temperature_c": result["temperature_c"],
                }
            ).to_csv(index=False).encode("utf-8"),
            file_name="fibertherm_simulation.csv",
            mime="text/csv",
        )

    st.markdown("#### Pump power along the fiber")
    pump_fig = make_line_chart(
        result["z_m"],
        [
            (result["pump_forward_w"], "Forward pump"),
            (result["pump_backward_w"], "Backward pump"),
            (result["pump_total_w"], "Combined remaining pump"),
        ],
        "Remaining pump power",
        "Position along fiber (m)",
        "Pump power (W)",
    )
    st.plotly_chart(pump_fig, use_container_width=True)


with tab_sim:
    st.subheader("Thermal simulation lab")
    chart_choice = st.selectbox(
        "Choose a profile",
        [
            "Temperature",
            "Heat deposition",
            "Pump power",
        ],
    )

    if chart_choice == "Temperature":
        fig = make_line_chart(
            result["z_m"],
            [
                (result["temperature_c"], "Two-end pump model"),
                (distributed["temperature_c"], "Uniform-heating benchmark"),
            ],
            "Temperature profile",
            "Position (m)",
            "Temperature (°C)",
        )
    elif chart_choice == "Heat deposition":
        fig = make_line_chart(
            result["z_m"],
            [(result["heat_per_m"], "Estimated heat deposition")],
            "Estimated heat deposition per unit length",
            "Position (m)",
            "Heat (W/m)",
        )
    else:
        fig = make_line_chart(
            result["z_m"],
            [
                (result["pump_forward_w"], "Forward pump"),
                (result["pump_backward_w"], "Backward pump"),
                (result["pump_total_w"], "Combined remaining pump"),
            ],
            "Pump power distribution",
            "Position (m)",
            "Pump power (W)",
        )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View simulation data"):
        table = pd.DataFrame(
            {
                "Position (m)": result["z_m"],
                "Temperature (°C)": result["temperature_c"],
                "Heat deposition (W/m)": result["heat_per_m"],
                "Forward pump (W)": result["pump_forward_w"],
                "Backward pump (W)": result["pump_backward_w"],
            }
        )
        st.dataframe(table, use_container_width=True, hide_index=True)


with tab_diagram:
    st.subheader("Diagram studio")
    st.write(
        "This conceptual diagram shows the calculation pathway used by "
        "the current simplified model. It is not a complete laser-system "
        "schematic."
    )

    nodes = [
        (0.08, 0.72, "Pump inputs", "Power, wavelength"),
        (0.37, 0.72, "Pump propagation", "Attenuation along fiber"),
        (0.66, 0.72, "Absorption", "Pump power lost per meter"),
        (0.66, 0.25, "Heat estimate", "Quantum-defect fraction"),
        (0.37, 0.25, "Thermal estimate", "Effective radial resistance"),
        (0.08, 0.25, "Temperature profile", "Ambient + temperature rise"),
    ]

    diagram = go.Figure()
    for x, y, title, subtitle in nodes:
        diagram.add_shape(
            type="rect",
            x0=x,
            y0=y,
            x1=x + 0.22,
            y1=y + 0.16,
            line={"width": 1.5, "color": "#2878B5"},
            fillcolor="rgba(40,120,181,0.10)",
            layer="below",
        )
        diagram.add_annotation(
            x=x + 0.11,
            y=y + 0.105,
            text=f"<b>{title}</b>",
            showarrow=False,
            font={"size": 12},
        )
        diagram.add_annotation(
            x=x + 0.11,
            y=y + 0.045,
            text=subtitle,
            showarrow=False,
            font={"size": 9},
        )

    arrows = [
        ((0.30, 0.80), (0.37, 0.80)),
        ((0.59, 0.80), (0.66, 0.80)),
        ((0.77, 0.72), (0.77, 0.41)),
        ((0.66, 0.33), (0.59, 0.33)),
        ((0.37, 0.33), (0.30, 0.33)),
    ]
    for start, end in arrows:
        diagram.add_annotation(
            x=end[0],
            y=end[1],
            ax=start[0],
            ay=start[1],
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=1.5,
            arrowcolor="#2878B5",
        )

    diagram.update_layout(
        height=440,
        xaxis={"visible": False, "range": [0, 1], "fixedrange": True},
        yaxis={"visible": False, "range": [0, 1], "fixedrange": True},
        template="plotly_white",
        margin={"l": 5, "r": 5, "t": 20, "b": 5},
        showlegend=False,
    )
    st.plotly_chart(diagram, use_container_width=True)

    st.markdown("#### Diagram interpretation")
    st.write(
        "The model estimates the pump remaining along the fiber, derives "
        "absorbed pump power per unit length, applies an approximate "
        "heat fraction, and converts that heat into an estimated "
        "temperature rise using an effective thermal resistance."
    )


with tab_optimize:
    st.subheader("Pump-split exploration")
    st.write(
        "Searches a grid of forward/backward pump fractions and selects "
        "the fraction with the lowest estimated peak temperature under "
        "the current simplified model."
    )

    optimization = optimize_pump_split(
        fiber_length_m=fiber_length_m,
        pump_power_w=float(pump_power_w),
        absorption_db_per_m=absorption_db_per_m,
        pump_wavelength_nm=float(pump_wavelength_nm),
        signal_wavelength_nm=float(signal_wavelength_nm),
        core_radius_um=core_radius_um,
        thermal_radius_mm=thermal_radius_mm,
        thermal_conductivity_w_mk=thermal_conductivity_w_mk,
        ambient_temperature_c=ambient_temperature_c,
    )

    a, b, c = st.columns(3)
    a.metric(
        "Best forward fraction",
        f"{optimization['best_forward_fraction']:.0%}",
    )
    b.metric(
        "Best backward fraction",
        f"{optimization['best_backward_fraction']:.0%}",
    )
    c.metric(
        "Lowest estimated peak temperature",
        f"{optimization['best_peak_temperature_c']:.2f} °C",
    )

    optimization_fig = go.Figure()
    optimization_fig.add_trace(
        go.Scatter(
            x=optimization["fractions"] * 100,
            y=optimization["peak_temperatures_c"],
            mode="lines",
            name="Peak temperature",
        )
    )
    optimization_fig.add_vline(
        x=optimization["best_forward_fraction"] * 100,
        line_dash="dash",
        annotation_text="Best grid point",
    )
    optimization_fig.update_layout(
        title="Estimated peak temperature versus forward pump fraction",
        xaxis_title="Forward pump fraction (%)",
        yaxis_title="Peak temperature (°C)",
        template="plotly_white",
    )
    st.plotly_chart(optimization_fig, use_container_width=True)

    st.caption(
        "This is a grid-search result, not a universal physical optimum. "
        "The result depends on the assumptions and the chosen objective."
    )


with tab_ai:
    st.subheader("AI research explainer")
    st.write(
        "Ask for a plain-language explanation of the selected plot, "
        "the model assumptions, or the trend in your results."
    )

    selected_subject = st.selectbox(
        "What should the AI explain?",
        [
            "Temperature profile",
            "Pump power profile",
            "Heat deposition profile",
            "Pump-split optimization",
            "Model diagram",
        ],
    )

    question = st.text_area(
        "Your question",
        value=(
            "Explain the physical meaning of this result, describe the "
            "main trend, and state the limitations of the simplified model."
        ),
        height=100,
    )

    if st.button("Explain with AI", type="primary"):
        api_key = os.getenv("OPENAI_API_KEY")
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", api_key)
        except Exception:
            pass

        if not api_key:
            st.warning(
                "No API key was found. Add OPENAI_API_KEY to Streamlit "
                "Cloud → App settings → Secrets, or set it in your local "
                "environment. The simulation itself works without an API key."
            )
        elif OpenAI is None:
            st.error(
                "The OpenAI package is unavailable. Install the dependencies "
                "from requirements.txt and restart the app."
            )
        else:
            if selected_subject == "Temperature profile":
                context = (
                    f"Peak temperature: {result['max_temperature_c']:.3f} °C; "
                    f"ambient: {ambient_temperature_c:.3f} °C; "
                    f"estimated rise: {result['temperature_rise_c']:.3f} °C."
                )
            elif selected_subject == "Pump power profile":
                context = (
                    f"Incident pump power: {pump_power_w:.1f} W; "
                    f"forward fraction: {forward_fraction:.2f}; "
                    f"backward fraction: {1-forward_fraction:.2f}; "
                    f"absorption: {absorption_db_per_m:.3f} dB/m."
                )
            elif selected_subject == "Heat deposition profile":
                context = (
                    f"Estimated total heat: {result['estimated_heat_w']:.3f} W; "
                    f"estimated heat fraction: {result['heat_fraction']:.4f}."
                )
            elif selected_subject == "Pump-split optimization":
                context = (
                    f"Grid-search forward fraction: "
                    f"{optimization['best_forward_fraction']:.3f}; "
                    f"estimated minimum peak temperature: "
                    f"{optimization['best_peak_temperature_c']:.3f} °C."
                )
            else:
                context = (
                    "The diagram represents pump inputs, pump attenuation, "
                    "absorbed pump power, estimated heat, effective thermal "
                    "resistance, and an estimated temperature profile."
                )

            system_prompt = """
You are a careful research assistant helping explain a simplified
fiber-laser thermal model.

Use accessible scientific language. Distinguish calculated outputs from
experimentally validated facts. Do not claim this model reproduces a
specific paper. Explain assumptions, units, and likely limitations.
Do not invent experimental results, citations, or missing parameters.
If a conclusion cannot be supported by the supplied context, say so.
"""

            user_prompt = f"""
Selected subject: {selected_subject}

Current model context:
{context}

User question:
{question}

Explain the result in a clear, structured way. Include:
1. What the result means.
2. The physical intuition.
3. What it does not prove.
4. One useful next validation step.
"""

            try:
                client = OpenAI(api_key=api_key)
                with st.spinner("Preparing explanation..."):
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.2,
                    )
                st.markdown(response.choices[0].message.content)
            except Exception as exc:
                st.error(
                    "The AI request failed. Check the API key, account "
                    "access, model availability, and network connection. "
                    f"Technical detail: {exc}"
                )

st.divider()
st.caption(
    "FiberTherm AI | Exploratory research prototype | "
    "Validate equations and parameters before using results in research claims."
)
