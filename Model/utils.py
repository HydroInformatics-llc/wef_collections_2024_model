# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2024 Bryant E. McDonnell - Hydroinformatics, LLC
#
# Licensed under the terms of the MIT License
# See LICENSE.txt for details
# -----------------------------------------------------------------------------
import warnings
warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pyswmm import Simulation, Links, Nodes, SystemStats, RainGages

import swmmio
from swmmio import find_network_trace
from swmmio import (build_profile_plot, add_hgl_plot, add_node_labels_plot,
                    add_link_labels_plot)

u_convert=7.481/1.e6 # ft3->M

def post_process_table(sim_handle):
    sim = sim_handle
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

    # for n in Nodes(sim):
    #     if n.statistics['flooding_volume'] > 0:
    #         print(n.nodeid, n.statistics['flooding_volume'])

    return table_info

class ControlCurve():
    def __init__(self, X, Y):
        self._x = X
        self._y = Y

    def __call__(self, input):
        x = input
        X = self._x
        Y = self._y
        if x <= X[0]:
            setting = Y[0]
        elif x >= X[-1]:
            setting = Y[-1]
        else:
            i = 0
            while i < len(X):
                if X[i] <= x and x <= X[i+1]:
                    break
                i += 1
            x1, x2 = X[i], X[i+1]
            delta = x2 - x1
            proportion = (x - x1) / delta
            y1, y2 = Y[i], Y[i+1]
            y_delta = y2 - y1
            setting = y1 + y_delta * proportion
        return setting

def profile_plots(inp_path_base=r"Hartfordville_1.inp", rpt_path_base="Hartfordville_1.rpt", rpt_path_ctrl="Hartfordville_ctrl.rpt"):
    # Profile Plotter Demo
    rpt = swmmio.rpt(rpt_path_base)
    profile_depths_no_control = rpt.node_depth_summary.MaxNodeDepthReported
    rpt = swmmio.rpt(rpt_path_ctrl)
    profile_depths_w_control = rpt.node_depth_summary.MaxNodeDepthReported

    mymodel = swmmio.Model(inp_path_base)
    fig = plt.figure(figsize=(11,6))
    fig.suptitle("Max HGL")
    ax = fig.add_subplot(6,1,(1,6))
    path_selection = find_network_trace(mymodel, 'WATER_SUPPLY_RESERVOIR', 'WESTRIVER_TP')
    profile_config = build_profile_plot(ax, mymodel, path_selection)
    add_hgl_plot(ax, profile_config, depth=profile_depths_no_control, label="No Control")
    add_hgl_plot(ax, profile_config, depth=profile_depths_w_control, color='green',label="With Control")
    add_node_labels_plot(ax, mymodel, profile_config)
    add_link_labels_plot(ax, mymodel, profile_config)
    leg = ax.legend()
    ax.grid('xy')
    ax.get_xaxis().set_ticklabels([])
    ax.grid('xy')
    fig.tight_layout()
    plt.show()
    fig.savefig("WRI_PROFILE.png")
    plt.close()


    fig = plt.figure(figsize=(11,6))
    fig.suptitle("Max HGL")
    ax = fig.add_subplot(6,1,(1,6))
    path_selection = find_network_trace(mymodel, 'J18', 'CSO9')
    profile_config = build_profile_plot(ax, mymodel, path_selection)
    add_hgl_plot(ax, profile_config, depth=profile_depths_no_control, label="No Control")
    add_hgl_plot(ax, profile_config, depth=profile_depths_w_control, color='green',label="With Control")
    add_node_labels_plot(ax, mymodel, profile_config)
    add_link_labels_plot(ax, mymodel, profile_config)
    leg = ax.legend()
    ax.grid('xy')
    ax.get_xaxis().set_ticklabels([])
    ax.grid('xy')
    fig.tight_layout()
    plt.show()
    fig.savefig("CSO9_PROFILE.png")
    plt.close()


    fig = plt.figure(figsize=(11,6))
    fig.suptitle("Max HGL")
    ax = fig.add_subplot(6,1,(1,6))
    path_selection = find_network_trace(mymodel, 'J22', 'EASTRIVER_TP')
    profile_config = build_profile_plot(ax, mymodel, path_selection)
    add_hgl_plot(ax, profile_config, depth=profile_depths_no_control, label="No Control")
    add_hgl_plot(ax, profile_config, depth=profile_depths_w_control, color='green',label="With Control")
    add_node_labels_plot(ax, mymodel, profile_config)
    add_link_labels_plot(ax, mymodel, profile_config)
    leg = ax.legend()
    ax.grid('xy')
    ax.get_xaxis().set_ticklabels([])
    ax.grid('xy')
    fig.tight_layout()
    plt.show()
    fig.savefig("ERI_PROFILE.png")
    plt.close()


def print_table(summary_model1, summary_model2):
    # TABLE OUTPUT
    print("|{:27s}|{:15s}|{:15s}|".format(" Volume Type  "," No Control (MG) ", " W Control (MG)  "))
    print("|---------------------------|-----------------|-----------------|")
    for key in summary_model1.keys():
        print("| {:25s} | {:15.3f} | {:15.3f} |".format(key,
                                                        summary_model1[key],
                                                        summary_model2[key]))
