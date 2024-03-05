# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2024 Bryant E. McDonnell - Hydroinformatics, LLC
#
# Licensed under the terms of the MIT License
# See LICENSE.txt for details
# -----------------------------------------------------------------------------
"""
This code / model was develoed for the Water Environment Federation - Collection
Systems 2024 Conference.  This concept was to create a real-world hydrologic and
hydraulic network with some adverse hydraulic conditions (flooding, surcharging,
combined sewer overflows).  The attendees of the workshop are to be guided to
propose and leverage available assets within the hydraulic network by use of real
time controls.

This scope of this code is to run the model as well as be a space where new control
logic can be developed to operate the various controllable facilities.
"""
import datetime
from pyswmm import Simulation, Links, Nodes, RainGages
from utils import post_process_table, ControlCurve, print_table, profile_plots

# Benchmark Model
with Simulation('./Hartfordville_1.inp') as sim:

    # Creating Handles to Controllable Assets
    old_wwtp_primary_inflow = Links(sim)['OLD_WWTP_PRIMARY_DIVERSION_GATE']
    old_wwtp_primary_dewater = Links(sim)['OLD_WWTP_PRIMARY_DEWATER_PUMP']
    lake_level_control_gate = Links(sim)['LAKE_LEVEL_CONTROL_GATE']
    bridge_river_cross_pump = Links(sim)['BRIDGE_RIVER_CROSS_PUMP']
    cso_9_overflow_regulator = Links(sim)['CSO9_REG']
    cso_9_underflow_gate = Links(sim)['C23_1']

    # Run Simulation
    sim.step_advance(300)
    for ind, step in enumerate(sim):
        if ind == 0:
            cso_9_overflow_regulator.target_setting = 0.0
            old_wwtp_primary_inflow.target_setting = 0
            old_wwtp_primary_dewater.target_setting = 0
            lake_level_control_gate.target_setting = 0.1
            cso_9_overflow_regulator.target_setting = 0.5
            cso_9_underflow_gate.target_setting = 1

    summary_model1 = post_process_table(sim)

# Controls Model
with Simulation('./Hartfordville_1.inp', \
                './Hartfordville_ctrl.rpt',
                './Hartfordville_ctrl.out') as sim:

    # Monitoring points
    C11_1 = Links(sim)["C11_1"]
    j21 = Nodes(sim)["J21"]
    rg = RainGages(sim)["Raingage"]
    wr_wet_well = Nodes(sim)["WR_WET_WELL"]
    er_wet_well = Nodes(sim)["ER_WETWELL"]
    water_res = Nodes(sim)["WATER_SUPPLY_RESERVOIR"]
    cso4_level = Nodes(sim)["INT_CSO4"]

    # Creating Handles to Controllable Assets
    old_wwtp_primary_inflow = Links(sim)['OLD_WWTP_PRIMARY_DIVERSION_GATE']
    old_wwtp_primary_dewater = Links(sim)['OLD_WWTP_PRIMARY_DEWATER_PUMP']
    lake_level_control_gate = Links(sim)['LAKE_LEVEL_CONTROL_GATE']
    bridge_river_cross_pump = Links(sim)['BRIDGE_RIVER_CROSS_PUMP']
    cso_9_overflow_regulator = Links(sim)['CSO9_REG']
    cso_9_underflow_gate = Links(sim)['C23_1']

    wtrp_control_curve = ControlCurve([0,3,5],[0,0,1])
    cso_9_reg_control_curve = ControlCurve([0,3.2,3.7],[1,1,0.15])
    cso_9_dam_control_curve = ControlCurve([0,7.3,7.8],[0,0,0.1])

    # Run Simulation
    sim.step_advance(300)
    for ind, step in enumerate(sim):
        if ind == 0:
            # Pushing initial settings
            old_wwtp_primary_inflow.target_setting = 0
            old_wwtp_primary_dewater.target_setting = 0.1
            cso_9_overflow_regulator.target_setting = 0.0

        # Dewater Reservoir before storm event!
        if sim.current_time <= datetime.datetime(2024, 4, 9, 8, 0, 0):
            lake_level_control_gate.target_setting = 1
        else:
            lake_level_control_gate.target_setting = 0.2

        bridge_river_cross_pump.target_setting = wtrp_control_curve(wr_wet_well.depth)
        cso_9_underflow_gate.target_setting  = cso_9_reg_control_curve(cso4_level.depth)
        # Flood Prevention CSO 9
        cso_9_overflow_regulator.target_setting = cso_9_dam_control_curve(j21.depth)

        # CSO 9 Prevention - Last Ditch Effort!
        if j21.depth > 7:
            bridge_river_cross_pump.target_setting = 0.1
            old_wwtp_primary_inflow.target_setting = 1
        else:
            old_wwtp_primary_inflow.target_setting = 0

    summary_model2 = post_process_table(sim)

print_table(summary_model1, summary_model2)
