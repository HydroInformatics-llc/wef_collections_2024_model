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
from pyswmm import Simulation, Links, Nodes

with Simulation('./Hartfordville_1.inp') as sim:

    # Creating Handles to Controllable Assets
    old_wwtp_primary_inflow = Links(sim)['OLD_WWTP_PRIMARY_DIVERSION_GATE']
    old_wwtp_primary_dewater = Links(sim)['OLD_WWTP_PRIMARY_DEWATER_PUMP']

    # Pushing initial settings
    def init_settings():
        old_wwtp_primary_inflow.target_setting = 0
        old_wwtp_primary_dewater.target_setting = 0

    sim.add_before_start(init_settings)

    for step in sim:
        pass
