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
from pyswmm import Simulation, Links, Nodes, SystemStats

u_convert=7.481/1.e6 # ft3->MG
def post_process_table(sim_handle):
    table_info = {}
    # CSO_Volume
    outfalls = ['CSO3', 'CSO4', 'CSO9']
    for of in outfalls:
        table_info[of] = Nodes(sim)[of].cumulative_inflow * u_convert

    # Treated Volume
    table_info['WESTRIVER_TP'] = Nodes(sim)['WESTRIVER_TP'].cumulative_inflow * u_convert
    table_info['WESTRIVER_GRAVITY_BYPASS'] = Nodes(sim)['WESTRIVER_GRAVITY_BYPASS'].cumulative_inflow * u_convert
    table_info['EASTRIVER_TP'] = Nodes(sim)['EASTRIVER_TP'].cumulative_inflow * u_convert
    table_info['EASTRIVER_GRAVITY_BYPASS'] = Nodes(sim)['EASTRIVER_GRAVITY_BYPASS'].cumulative_inflow * u_convert

    # System Flooding
    system_stats = SystemStats(sim)
    table_info['FLOODING_VOLUME (KGal)'] = system_stats.routing_stats['flooding'] * u_convert *1000

    return table_info


with Simulation('./Hartfordville_1.inp') as sim:

    # Creating Handles to Controllable Assets
    old_wwtp_primary_inflow = Links(sim)['OLD_WWTP_PRIMARY_DIVERSION_GATE']
    old_wwtp_primary_dewater = Links(sim)['OLD_WWTP_PRIMARY_DEWATER_PUMP']
    lake_level_control_gate = Links(sim)['LAKE_LEVEL_CONTROL_GATE']
    bridge_river_cross_pump = Links(sim)['BRIDGE_RIVER_CROSS_PUMP']
    cso_9_overflow_regulator = Links(sim)['CSO9_REG']

    # Pushing initial settings
    old_wwtp_primary_inflow.target_setting = 0
    old_wwtp_primary_dewater.target_setting = 0
    lake_level_control_gate.target_setting = 0

    # Run Simulation
    sim.step_advance(300)
    for step in sim:
        pass

    summary_model1 = post_process_table(sim)

with Simulation('./Hartfordville_1.inp', \
                './Hartfordville_ctrl.rpt',
                './Hartfordville_ctrl.out') as sim:

    # Creating Handles to Controllable Assets
    old_wwtp_primary_inflow = Links(sim)['OLD_WWTP_PRIMARY_DIVERSION_GATE']
    old_wwtp_primary_dewater = Links(sim)['OLD_WWTP_PRIMARY_DEWATER_PUMP']
    lake_level_control_gate = Links(sim)['LAKE_LEVEL_CONTROL_GATE']
    bridge_river_cross_pump = Links(sim)['BRIDGE_RIVER_CROSS_PUMP']
    cso_9_overflow_regulator = Links(sim)['CSO9_REG']
    cso_9_underflow_gate = Links(sim)['C23_1']

    # Pushing initial settings
    old_wwtp_primary_inflow.target_setting = 0
    old_wwtp_primary_dewater.target_setting = 0
    lake_level_control_gate.target_setting = 0
    cso_9_overflow_regulator.target_setting = 0

    # Run Simulation
    sim.step_advance(300)
    for step in sim:
        cso_9_overflow_regulator.target_setting = 0
        bridge_river_cross_pump.target_setting = 0.15
        cso_9_underflow_gate.target_setting = 0.5

    summary_model2 = post_process_table(sim)

# TABLE OUTPUT
print("|{:27s}|{:15s}|{:15s}|".format(" Volume Type  "," No Control (MG) ", " W Control (MG)  "))
print("|---------------------------|-----------------|-----------------|")
for key in summary_model1.keys():
    print("| {:25s} | {:15.3f} | {:15.3f} |".format(key,
                                                    summary_model1[key],
                                                    summary_model2[key]))
