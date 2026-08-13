import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# PAGE
# =========================================================

st.title("State Point Analysis")

st.write(
    "Standalone secondary clarifier state point analysis."
)


# =========================================================
# 1. MODEL INPUTS
# =========================================================

st.header("Inputs")


col1, col2 = st.columns(2)


with col1:

    Qi = st.number_input(
        "Influent Flow Qi (m³/hr)",
        min_value=0.0,
        value=100.0
    )

    Qr = st.number_input(
        "Recycle Flow Qr (m³/hr)",
        min_value=0.0,
        value=40.5
    )

    A = st.number_input(
        "Clarifier Area A (m²)",
        min_value=0.01,
        value=55.0
    )


with col2:

    MLSS = st.number_input(
        "MLSS (kg/m³)",
        min_value=0.0,
        value=3.0
    )

    SVI = st.number_input(
        "SVI (mL/g)",
        min_value=0.0,
        value=150.0
    )

    max_mlss = st.number_input(
        "Maximum concentration shown (kg/m³)",
        min_value=1.0,
        value=20.0
    )


# =========================================================
# 2. CONCENTRATION RANGE
# =========================================================

x_range = np.linspace(
    0,
    max_mlss,
    1000
)


# =========================================================
# 3. BASIC HYDRAULICS
# =========================================================

# State point total applied solids flux

j_tap = (
    (Qi + Qr)
    * MLSS
    / A
)


# Overflow velocity

vi = (
    Qi
    / A
)


# Underflow / recycle velocity

vr = (
    Qr
    / A
)


# Recycle ratio

if Qi > 0:

    recycle_ratio = (
        Qr
        / Qi
    )

else:

    recycle_ratio = 0.0


# =========================================================
# 4. SETTLING RELATIONSHIP
# =========================================================

# Existing empirical correlation from old script

v_0 = (
    17.4
    * np.exp(
        -0.0113
        * SVI
    )
)


p_hin = (

    -0.9834

    * np.exp(
        -0.00581
        * SVI
    )

    + 1.043
)


# Vesilind settling velocity across concentration range

v_s = (

    v_0

    * np.exp(
        -p_hin
        * x_range
    )
)


# =========================================================
# 5. SOLIDS FLUX CURVES
# =========================================================

# Gravity solids flux

j_grav = (
    v_s
    * x_range
)


# Overflow operating line

j_over = (
    vi
    * x_range
)


# Underflow operating line

j_under = (

    -vr
    * x_range

    + j_tap
)


# =========================================================
# 6. STATE POINT
# =========================================================

j_state_point = (
    vi
    * MLSS
)


# =========================================================
# 7. SHC2 CHECK
# =========================================================

# Overflow flux at actual MLSS

j_overflowAtMLSS = (

    vi
    * MLSS
)


# Gravity flux at actual MLSS

j_gravityAtMLSS = (

    v_0

    * np.exp(
        -p_hin
        * MLSS
    )

    * MLSS
)


if (
    j_overflowAtMLSS
    < j_gravityAtMLSS
):

    SHC2 = True

else:

    SHC2 = False


# =========================================================
# 8. UNDERFLOW X-INTERCEPT
# =========================================================

# This is where:
#
# j_under = 0
#
# therefore:
#
# x = j_tap / vr

if vr > 0:

    underflow_concentration = (
        j_tap
        / vr
    )

else:

    underflow_concentration = np.nan


# =========================================================
# 9. RESULTS SUMMARY
# =========================================================

st.header("Results")


results = pd.DataFrame({

    "Parameter": [

        "Influent Flow",

        "Recycle Flow",

        "Recycle Ratio",

        "Clarifier Area",

        "MLSS",

        "SVI",

        "Overflow Velocity",

        "Recycle Velocity",

        "v₀",

        "Hindered Settling Parameter",

        "Overflow Flux at MLSS",

        "Gravity Flux at MLSS",

        "Underflow Concentration",

        "SHC2"
    ],

    "Value": [

        f"{Qi:.2f} m³/hr",

        f"{Qr:.2f} m³/hr",

        f"{recycle_ratio:.3f}",

        f"{A:.2f} m²",

        f"{MLSS:.2f} kg/m³",

        f"{SVI:.0f} mL/g",

        f"{vi:.3f} m/hr",

        f"{vr:.3f} m/hr",

        f"{v_0:.3f} m/hr",

        f"{p_hin:.3f}",

        f"{j_overflowAtMLSS:.3f} kg/m².hr",

        f"{j_gravityAtMLSS:.3f} kg/m².hr",

        (
            f"{underflow_concentration:.2f} kg/m³"
            if not np.isnan(
                underflow_concentration
            )
            else "N/A"
        ),

        "PASS" if SHC2 else "FAIL"
    ]
})


st.dataframe(
    results,
    hide_index=True,
    width="stretch"
)


# =========================================================
# 10. SIMPLE STATUS DISPLAY
# =========================================================

if SHC2:

    st.success(
        "SHC2 satisfied: overflow flux at MLSS is below the gravity flux."
    )

else:

    st.error(
        "SHC2 not satisfied: overflow flux at MLSS exceeds the gravity flux."
    )


# =========================================================
# 11. STATE POINT PLOT
# =========================================================

st.header("State Point Diagram")


fig, ax = plt.subplots(
    figsize=(8, 6)
)


# Gravity flux curve

ax.plot(
    x_range,
    j_grav,
    label="Gravity Flux"
)


# Overflow line

ax.plot(
    x_range,
    j_over,
    label="Overflow"
)


# Underflow line

ax.plot(
    x_range,
    j_under,
    label="Underflow"
)


# State point

ax.scatter(
    MLSS,
    j_state_point,
    s=80,
    label="State Point"
)


# Underflow concentration intercept

if not np.isnan(
    underflow_concentration
):

    ax.scatter(
        underflow_concentration,
        0,
        s=60,
        label="Underflow Concentration"
    )


# Labels

ax.set_xlabel(
    "Solids Concentration (kg/m³)"
)

ax.set_ylabel(
    "Solids Flux (kg/m².hr)"
)

ax.set_title(
    "State Point Analysis"
)

ax.legend()

ax.set_ylim(
    0,
    None
)

ax.set_xlim(
    0,
    max_mlss
)

ax.grid(
    True
)


st.pyplot(fig)


# =========================================================
# 12. OPTIONAL CALCULATION DATA
# =========================================================

with st.expander(
    "Show Calculation Data"
):

    calculation_data = pd.DataFrame({

        "Concentration (kg/m³)":
            x_range,

        "Settling Velocity (m/hr)":
            v_s,

        "Gravity Flux (kg/m².hr)":
            j_grav,

        "Overflow Flux (kg/m².hr)":
            j_over,

        "Underflow Flux (kg/m².hr)":
            j_under
    })


    st.dataframe(
        calculation_data,
        hide_index=True,
        width="stretch"
    )
