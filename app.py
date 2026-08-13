import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =========================================================
# PAGE
# =========================================================

st.title("State Point Analysis")

st.write(
    "Standalone secondary clarifier state point analysis prototype."
)


# =========================================================
# 1. INPUTS
# =========================================================

st.header("Inputs")


col1, col2 = st.columns(2)


with col1:

    flow_MLd = st.number_input(
        "Influent Flow Q (ML/d)",
        min_value=0.0,
        value=20.0
    )

    recycle_ratio = st.number_input(
        "RAS Recycle Ratio QR/Q",
        min_value=0.0,
        value=0.5
    )

    clarifier_area = st.number_input(
        "Clarifier Area (m²)",
        min_value=0.1,
        value=500.0
    )

    mlss_mgL = st.number_input(
        "MLSS (mg/L)",
        min_value=0.0,
        value=3500.0
    )


with col2:

    vmax = st.number_input(
        "Vmax (m/h)",
        min_value=0.0,
        value=7.0
    )

    k = st.number_input(
        "Vesilind k",
        min_value=0.0,
        value=600.0
    )

    max_concentration_mgL = st.number_input(
        "Maximum Concentration for Plot (mg/L)",
        min_value=1000.0,
        value=15000.0
    )


# =========================================================
# 2. UNIT CONVERSIONS
# =========================================================

# ML/day -> m3/hour

Q = (
    flow_MLd
    * 1000
    / 24
)


# R = QR / Q

QR = (
    recycle_ratio
    * Q
)


# mg/L -> kg/m3
#
# 1000 mg/L = 1 kg/m3

X_MLSS = (
    mlss_mgL
    / 1000
)


# =========================================================
# 3. BASIC HYDRAULICS
# =========================================================

SOR = (
    Q
    / clarifier_area
)


Ub = (
    QR
    / clarifier_area
)


# =========================================================
# 4. CONCENTRATION RANGE
# =========================================================

concentration_mgL = np.linspace(
    0,
    max_concentration_mgL,
    500
)


# Convert to kg/m3 for flux calculations

concentration = (
    concentration_mgL
    / 1000
)


# =========================================================
# 5. SETTLING VELOCITY
# =========================================================

# Vesilind equation:
#
# Vi = Vmax * exp(-(k / 1,000,000) * X)
#
# X is mg/L in this equation

settling_velocity = (

    vmax

    * np.exp(

        -(k / 1_000_000)

        * concentration_mgL
    )
)


# =========================================================
# 6. GRAVITY SOLIDS FLUX
# =========================================================

gravity_flux = (

    concentration

    * settling_velocity
)


# Units:
#
# kg/m3 * m/h
#
# = kg/m2.h


# =========================================================
# 7. STATE POINT
# =========================================================

state_point_flux = (

    SOR

    * X_MLSS
)


# =========================================================
# 8. OVERFLOW OPERATING LINE
# =========================================================

overflow_line = (

    SOR

    * concentration
)


# =========================================================
# 9. UNDERFLOW OPERATING LINE
# =========================================================

underflow_line = (

    state_point_flux

    - Ub
    * (
        concentration
        - X_MLSS
    )
)


# =========================================================
# 10. RAS / UNDERFLOW CONCENTRATION
# =========================================================

if Ub > 0:

    Cu = (

        X_MLSS

        + state_point_flux
        / Ub
    )

else:

    Cu = np.nan


Cu_mgL = (
    Cu
    * 1000
)


# =========================================================
# 11. FEASIBILITY CHECK
# =========================================================

if Ub > 0:

    analysis_mask = (

        (concentration >= X_MLSS)

        &

        (concentration <= Cu)
    )


    gravity_flux_analysis = (
        gravity_flux[
            analysis_mask
        ]
    )


    underflow_analysis = (
        underflow_line[
            analysis_mask
        ]
    )


    difference = (

        underflow_analysis

        - gravity_flux_analysis
    )


    if len(difference) > 0:

        max_exceedance = (
            difference.max()
        )

    else:

        max_exceedance = np.nan


    tolerance = 0.01


    if np.isnan(max_exceedance):

        status = "Unable to assess"

    elif max_exceedance > tolerance:

        status = "FAIL"

    elif max_exceedance > -tolerance:

        status = "CRITICAL"

    else:

        status = "PASS"


else:

    max_exceedance = np.nan

    status = "Unable to assess"


# =========================================================
# 12. SUMMARY RESULTS
# =========================================================

st.header("SPA Results")


results = pd.DataFrame({

    "Parameter": [

        "Influent Flow",

        "RAS Flow",

        "Recycle Ratio",

        "Surface Overflow Rate",

        "Underflow Velocity",

        "MLSS",

        "Calculated RAS Concentration",

        "Maximum Flux Exceedance",

        "SPA Status"
    ],

    "Value": [

        f"{flow_MLd:.2f} ML/d",

        f"{QR * 24 / 1000:.2f} ML/d",

        f"{recycle_ratio:.2f}",

        f"{SOR:.3f} m/h",

        f"{Ub:.3f} m/h",

        f"{mlss_mgL:.0f} mg/L",

        f"{Cu_mgL:.0f} mg/L",

        (
            f"{max_exceedance:.3f} kg/m².h"
            if not np.isnan(max_exceedance)
            else "N/A"
        ),

        status
    ]
})


st.dataframe(
    results,
    hide_index=True,
    width="stretch"
)


# =========================================================
# 13. STATE POINT PLOT
# =========================================================

st.header("State Point Diagram")


fig, ax = plt.subplots()


# Gravity flux curve

ax.plot(
    concentration_mgL,
    gravity_flux,
    label="Gravity Flux"
)


# Overflow operating line

ax.plot(
    concentration_mgL,
    overflow_line,
    label="Overflow Line"
)


# Only show the physically useful portion
# of the underflow operating line

if Ub > 0:

    underflow_plot_mask = (

        (concentration >= X_MLSS)

        &

        (concentration <= Cu)
    )


    ax.plot(

        concentration_mgL[
            underflow_plot_mask
        ],

        underflow_line[
            underflow_plot_mask
        ],

        label="Underflow Line"
    )


# State point

ax.scatter(

    mlss_mgL,

    state_point_flux,

    s=80,

    label="State Point"
)


# RAS concentration intercept

if Ub > 0:

    ax.scatter(

        Cu_mgL,

        0,

        s=60,

        label="RAS Concentration"
    )


ax.set_xlabel(
    "Solids Concentration (mg/L)"
)

ax.set_ylabel(
    "Solids Flux (kg/m².h)"
)

ax.set_title(
    "Secondary Clarifier State Point Analysis"
)

ax.set_xlim(
    0,
    max_concentration_mgL
)

ax.set_ylim(
    bottom=0
)

ax.grid(
    True,
    alpha=0.3
)

ax.legend()


st.pyplot(fig)


# =========================================================
# 14. OPTIONAL RAW CALCULATION TABLE
# =========================================================

with st.expander(
    "Show Flux Calculation Data"
):

    calculation_data = pd.DataFrame({

        "Concentration (mg/L)":
            concentration_mgL,

        "Settling Velocity (m/h)":
            settling_velocity,

        "Gravity Flux (kg/m².h)":
            gravity_flux,

        "Overflow Line (kg/m².h)":
            overflow_line,

        "Underflow Line (kg/m².h)":
            underflow_line
    })


    st.dataframe(
        calculation_data,
        hide_index=True,
        width="stretch"
    )
