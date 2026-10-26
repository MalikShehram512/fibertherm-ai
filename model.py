
"""FiberTherm AI: simplified fiber-laser thermal modeling.

Important:
This is an exploratory engineering model, not a validated reproduction
of the equations or numerical results in the referenced research paper.
"""

from __future__ import annotations

import numpy as np


def simulate_end_pumped(
    fiber_length_m: float = 5.0,
    pump_power_w: float = 1000.0,
    forward_fraction: float = 0.5,
    absorption_db_per_m: float = 0.5,
    pump_wavelength_nm: float = 976.0,
    signal_wavelength_nm: float = 1080.0,
    core_radius_um: float = 10.0,
    thermal_radius_mm: float = 1.0,
    thermal_conductivity_w_mk: float = 1.4,
    ambient_temperature_c: float = 25.0,
    points: int = 500,
) -> dict:
    """Estimate axial heating and temperature for two-end pumping."""

    if fiber_length_m <= 0:
        raise ValueError("Fiber length must be positive.")
    if pump_power_w < 0:
        raise ValueError("Pump power cannot be negative.")
    if not 0 <= forward_fraction <= 1:
        raise ValueError("Forward fraction must be between 0 and 1.")
    if absorption_db_per_m < 0:
        raise ValueError("Absorption cannot be negative.")
    if pump_wavelength_nm <= 0 or signal_wavelength_nm <= 0:
        raise ValueError("Wavelengths must be positive.")
    if core_radius_um <= 0 or thermal_radius_mm <= 0:
        raise ValueError("Thermal radii must be positive.")
    if thermal_conductivity_w_mk <= 0:
        raise ValueError("Thermal conductivity must be positive.")
    if points < 2:
        raise ValueError("At least two spatial points are required.")

    z = np.linspace(0.0, fiber_length_m, points)

    # Convert absorption from dB/m to the exponential attenuation coefficient.
    alpha = absorption_db_per_m * np.log(10.0) / 10.0

    forward_power = pump_power_w * forward_fraction
    backward_power = pump_power_w * (1.0 - forward_fraction)

    # Remaining pump power traveling from each end.
    pump_forward = forward_power * np.exp(-alpha * z)
    pump_backward = backward_power * np.exp(-alpha * (fiber_length_m - z))
    pump_total = pump_forward + pump_backward

    # Simplified quantum-defect heat fraction.
    heat_fraction = max(
        0.0, 1.0 - pump_wavelength_nm / signal_wavelength_nm
    )

    # Absorbed pump power per unit length (W/m).
    absorbed_power_per_m = alpha * pump_total

    # Approximate thermal resistance per unit length (K*m/W).
    core_radius_m = core_radius_um * 1e-6
    outer_radius_m = thermal_radius_mm * 1e-3

    if outer_radius_m <= core_radius_m:
        raise ValueError(
            "Thermal radius must be larger than the core radius."
        )

    thermal_resistance_per_m = (
        np.log(outer_radius_m / core_radius_m)
        / (2.0 * np.pi * thermal_conductivity_w_mk)
    )

    heat_per_m = heat_fraction * absorbed_power_per_m
    temperature_c = (
        ambient_temperature_c
        + heat_per_m * thermal_resistance_per_m
    )

    absorbed_total_w = float(
        np.trapezoid(absorbed_power_per_m, z)
    )
    estimated_heat_w = float(np.trapezoid(heat_per_m, z))

    return {
        "z_m": z,
        "pump_forward_w": pump_forward,
        "pump_backward_w": pump_backward,
        "pump_total_w": pump_total,
        "absorbed_power_per_m": absorbed_power_per_m,
        "heat_per_m": heat_per_m,
        "temperature_c": temperature_c,
        "max_temperature_c": float(np.max(temperature_c)),
        "min_temperature_c": float(np.min(temperature_c)),
        "temperature_rise_c": float(
            np.max(temperature_c) - ambient_temperature_c
        ),
        "absorbed_total_w": absorbed_total_w,
        "estimated_heat_w": estimated_heat_w,
        "heat_fraction": heat_fraction,
        "alpha_per_m": alpha,
        "thermal_resistance_per_m": thermal_resistance_per_m,
    }


def simulate_distributed_heating(
    fiber_length_m: float = 5.0,
    pump_power_w: float = 1000.0,
    absorption_db_per_m: float = 0.5,
    pump_wavelength_nm: float = 976.0,
    signal_wavelength_nm: float = 1080.0,
    core_radius_um: float = 10.0,
    thermal_radius_mm: float = 1.0,
    thermal_conductivity_w_mk: float = 1.4,
    ambient_temperature_c: float = 25.0,
    points: int = 500,
) -> dict:
    """Idealized uniform-heating benchmark, not a distributed-pump solver.

    It assumes total absorbed pump power is deposited uniformly along the
    fiber. Real distributed pumping requires a spatial pump propagation
    model, which this function does not implement.
    """

    if fiber_length_m <= 0 or pump_power_w < 0:
        raise ValueError("Length must be positive and power nonnegative.")
    if absorption_db_per_m < 0:
        raise ValueError("Absorption cannot be negative.")
    if points < 2:
        raise ValueError("At least two spatial points are required.")
    if pump_wavelength_nm <= 0 or signal_wavelength_nm <= 0:
        raise ValueError("Wavelengths must be positive.")
    if core_radius_um <= 0 or thermal_radius_mm <= 0:
        raise ValueError("Thermal radii must be positive.")
    if thermal_conductivity_w_mk <= 0:
        raise ValueError("Thermal conductivity must be positive.")

    z = np.linspace(0.0, fiber_length_m, points)
    alpha = absorption_db_per_m * np.log(10.0) / 10.0

    # Approximate absorption of the specified total incident pump power.
    absorbed_total_w = pump_power_w * (
        1.0 - np.exp(-alpha * fiber_length_m)
    )

    heat_fraction = max(
        0.0, 1.0 - pump_wavelength_nm / signal_wavelength_nm
    )
    estimated_heat_w = absorbed_total_w * heat_fraction
    heat_per_m = np.full(
        points, estimated_heat_w / fiber_length_m
    )

    core_radius_m = core_radius_um * 1e-6
    outer_radius_m = thermal_radius_mm * 1e-3

    if outer_radius_m <= core_radius_m:
        raise ValueError(
            "Thermal radius must be larger than the core radius."
        )

    thermal_resistance_per_m = (
        np.log(outer_radius_m / core_radius_m)
        / (2.0 * np.pi * thermal_conductivity_w_mk)
    )
    temperature_c = (
        ambient_temperature_c
        + heat_per_m * thermal_resistance_per_m
    )

    return {
        "z_m": z,
        "heat_per_m": heat_per_m,
        "temperature_c": temperature_c,
        "max_temperature_c": float(np.max(temperature_c)),
        "min_temperature_c": float(np.min(temperature_c)),
        "temperature_rise_c": float(
            np.max(temperature_c) - ambient_temperature_c
        ),
        "absorbed_total_w": float(absorbed_total_w),
        "estimated_heat_w": float(estimated_heat_w),
        "heat_fraction": heat_fraction,
        "alpha_per_m": alpha,
        "thermal_resistance_per_m": thermal_resistance_per_m,
    }


def optimize_pump_split(
    fiber_length_m: float = 5.0,
    pump_power_w: float = 1000.0,
    absorption_db_per_m: float = 0.5,
    pump_wavelength_nm: float = 976.0,
    signal_wavelength_nm: float = 1080.0,
    core_radius_um: float = 10.0,
    thermal_radius_mm: float = 1.0,
    thermal_conductivity_w_mk: float = 1.4,
    ambient_temperature_c: float = 25.0,
    candidates: int = 101,
) -> dict:
    """Find the lowest peak temperature in a grid of pump-power splits."""

    if candidates < 2:
        raise ValueError("At least two candidates are required.")

    fractions = np.linspace(0.0, 1.0, candidates)
    peak_temperatures = []

    for fraction in fractions:
        result = simulate_end_pumped(
            fiber_length_m=fiber_length_m,
            pump_power_w=pump_power_w,
            forward_fraction=float(fraction),
            absorption_db_per_m=absorption_db_per_m,
            pump_wavelength_nm=pump_wavelength_nm,
            signal_wavelength_nm=signal_wavelength_nm,
            core_radius_um=core_radius_um,
            thermal_radius_mm=thermal_radius_mm,
            thermal_conductivity_w_mk=thermal_conductivity_w_mk,
            ambient_temperature_c=ambient_temperature_c,
        )
        peak_temperatures.append(result["max_temperature_c"])

    best_index = int(np.argmin(peak_temperatures))

    return {
        "best_forward_fraction": float(fractions[best_index]),
        "best_backward_fraction": float(1.0 - fractions[best_index]),
        "best_peak_temperature_c": float(
            peak_temperatures[best_index]
        ),
        "fractions": fractions,
        "peak_temperatures_c": np.asarray(peak_temperatures),
    }
