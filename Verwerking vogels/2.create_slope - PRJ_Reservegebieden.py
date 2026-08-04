# -*- coding: utf-8 -*-
#
# ---------------------------------------------------------------------------
# 2.create_slope_ECOTIDE.py
# 
# Created on 17/11/2020 by Amber Mertens; edited by Nicolas Vanermen
# Last edited on: 31/07/2026
# Last run: 03/08/2026 - 17:30
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
import os
import arcpy
from arcpy import env
from arcpy.sa import Raster, Slope

# Check out Spatial Analyst extension
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    print("Warning: spatial extension is not available")
    exit()


# --------------------------------------
# ----- Set alternative & scenario -----
# --------------------------------------
print("Set alternative & scenario")

alternative = "REF_2020"
# scenario = "HIC"
scenario = "Scaldis"

alternative_scenario = alternative + "_" + scenario


# ----------------------------------------------------------
# ----- Set working directory and environment settings -----
# ----------------------------------------------------------
print("Set working directory and environment settings")

# Set in- and output gdb directory
input_dir = r"Q:\Projects\PRJ_Schelde\ECOTIDE\Habitats\PRJ_Reservegebieden\Data\Combigrids"
output_dir = r"Q:\Projects\PRJ_Schelde\ECOTIDE\Vogels\PRJ_Reservegebieden\Output"

# Specify geodatabase to store slope result
slope_gdb_name = "input_slope_" + alternative_scenario + ".gdb"
slope_gdb = os.path.join(output_dir, slope_gdb_name)

if not arcpy.Exists(slope_gdb):
    arcpy.CreateFileGDB_management(output_dir, slope_gdb_name)

# Set output raster directory
slope_raster_path = os.path.join(slope_gdb, "Vogelmodel_slope_" + alternative_scenario)

# Set environment settings
env.workspace = slope_gdb
env.overwriteOutput = True
env.addOutputsToMap = False


# --------------------
# ------ INPUTS ------
# --------------------
print("Inputs")

dtm_gdb = os.path.join(input_dir, "Combigrids.gdb")
dtm_path = os.path.join(dtm_gdb, "Combigrid_16B_mTAW_" + alternative)
dtm = Raster(dtm_path)


# -------------------
# ----- PROCESS -----
# -------------------
print("... Processing")

outSlope_BOZ = Slope(dtm, "PERCENT_RISE", 1)

# ----------------
# ----- SAVE -----
# ----------------
print("... Saving")

outSlope_BOZ.save(slope_raster_path)

print("Output saved!")