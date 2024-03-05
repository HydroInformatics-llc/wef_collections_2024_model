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
import warnings
warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pyswmm import Simulation, Links, Nodes, SystemStats, RainGages

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

    # Monitoring points
    C11_1 = Links(sim)["C11_1"]
    rg = RainGages(sim)["Raingage"]
    wr_wet_well = Nodes(sim)["WR_WET_WELL"]
    er_wet_well = Nodes(sim)["ER_WETWELL"]
    water_res = Nodes(sim)["WATER_SUPPLY_RESERVOIR"]

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
    lake_level_control_gate.target_setting = 0.2
    cso_9_overflow_regulator.target_setting = 0
    cso_9_underflow_gate.target_setting = 0.5

    # Run Simulation
    sim.step_advance(300)
    for step in sim:
        if C11_1.flow > 13:
            delta_flow = ( C11_1.flow - 13 ) / 20 #
            if delta_flow > 1: delta_flow = 1

            bridge_river_cross_pump.target_setting = delta_flow
            #print(bridge_river_cross_pump.flow, wr_wet_well.depth)
        else:
            bridge_river_cross_pump.target_setting = 0

        # Dewater Reservoir before storm event!
        if sim.current_time <= datetime.datetime(2024, 4, 9, 8, 0, 0):
            lake_level_control_gate.target_setting = 1
        else:
            #print(sim.current_time, water_res.volume*u_convert, water_res.depth)
            lake_level_control_gate.target_setting = 0.2

    summary_model2 = post_process_table(sim)

# TABLE OUTPUT
print("|{:27s}|{:15s}|{:15s}|".format(" Volume Type  "," No Control (MG) ", " W Control (MG)  "))
print("|---------------------------|-----------------|-----------------|")
for key in summary_model1.keys():
    print("| {:25s} | {:15.3f} | {:15.3f} |".format(key,
                                                    summary_model1[key],
                                                    summary_model2[key]))

import swmmio
from swmmio import find_network_trace
from swmmio import (build_profile_plot, add_hgl_plot, add_node_labels_plot,
                    add_link_labels_plot)

# Profile Plotter Demo
rpt = swmmio.rpt("Hartfordville_1.rpt")
profile_depths_no_control = rpt.node_depth_summary.MaxNodeDepthReported
rpt = swmmio.rpt("Hartfordville_ctrl.rpt")
profile_depths_w_control = rpt.node_depth_summary.MaxNodeDepthReported

mymodel = swmmio.Model(r"Hartfordville_1.inp")
fig = plt.figure(figsize=(11,6))
fig.suptitle("Max HGL")
ax = fig.add_subplot(6,1,(1,6))
path_selection = find_network_trace(mymodel, 'WATER_SUPPLY_RESERVOIR', 'WESTRIVER_TP')
profile_config = build_profile_plot(ax, mymodel, path_selection)
add_hgl_plot(ax, profile_config, depth=profile_depths_no_control, label="No Control")
add_hgl_plot(ax, profile_config, depth=profile_depths_w_control, color='green',label="With Control")
add_node_labels_plot(ax, mymodel, profile_config)
#add_link_labels_plot(ax, mymodel, profile_config)
leg = ax.legend()
ax.grid('xy')
ax.get_xaxis().set_ticklabels([])


ax.grid('xy')
fig.tight_layout()
fig.savefig("profiles.png")
plt.close()
