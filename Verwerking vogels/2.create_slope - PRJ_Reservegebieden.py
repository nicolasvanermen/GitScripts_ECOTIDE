# -*- coding: utf-8 -*-
#
# ---------------------------------------------------------------------------
# 2.create_slope_ECOTIDE.py
# 
# Created on 17/11/2020 by Amber Mertens; edited by Nicolas Vanermen
# Last edited on: 31/07/2026
# Last run: 31/07/2026 - 14:00
# 
# Version: Python 27
#
# Description: Create a slope raster for the bird model of ECOTIDE
#
# Remark: run takes about 5'
# ---------------------------------------------------------------------------


# -----------------------
# ----- Preparation -----
# -----------------------

# Import modules
import arcpy
from arcpy import env
from arcpy.sa import *

# Import os
# import os

# Check out Spatial Analyst extension
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    print("Warning: spatial extension is not available")
    exit()


# --------------------------------------
# ----- Set alternative & scenario -----
# --------------------------------------
print("... Set alternative & scenario")

alternative = "REF_2020"
# scenario = "HIC"
scenario = "Scaldis"

alternative_scenario = alternative + "_" + scenario


# ----------------------------------------------------------
# ----- Set working directory and environment settings -----
# ----------------------------------------------------------
print("... Set working directory and environment settings")

# Set file directory
project_path = "Q:\\Projects\\PRJ_Schelde\\ECOTIDE\\Vogels\\PRJ_Reservegebieden"

# Specify geodatabase to store slope result
slope_gdb_name = "input_slope_" + alternative_scenario + ".gdb"
slope_gdb = project_path + "\\Output\\" + slope_gdb_name
if not arcpy.Exists(slope_gdb):
    arcpy.CreateFileGDB_management(project_path + "\\Output\\", slope_gdb_name)

# Set environment settings
env.overwriteOutput = True
env.addOutputsToMap = False


# --------------------
# ------ INPUTS ------
# --------------------
print("... Inputs")

dtm_gdb = "Q:\\Projects\\PRJ_Schelde\\Ecotide\\Habitats\\PRJ_Reservegebieden\\Data\\Combigrids\\Combigrids.gdb"
dtm_name = "Combigrid_16B_mTAW_REF_2020"
dtm = Raster(dtm_gdb + "\\" + dtm_name)


# -------------------
# ----- PROCESS -----
# -------------------
print("... Processing")

outSlope_BOZ = Slope(dtm, "PERCENT_RISE", 1)

# ----------------
# ----- SAVE -----
# ----------------
print("... Saving")

outSlope_BOZ.save(slope_gdb + "\\Vogelmodel_slope_" + alternative_scenario)

print("... Output saved!")