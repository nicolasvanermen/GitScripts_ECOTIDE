# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------------------------------
# 1.calculate_dd - PRJ_Reservegebieden.py
# 
# Created on 25/01/2020 by Amber Mertens; edited by Nicolas Vanermen
# Last edited on: 31/07/2026
# Last run: 06/08/2026 - 14:00
#
# Version: Python 27
#
# Description: this script produces a mosaic raster for 19 DD intervals (from 0 to 95% in steps of 5)  
# as input in the bird model of ECOTIDE
#
# Remark: the script only runs through ArcGIS (Python window)!
# Remark: run takes about 8 minutes per interval, and another hour for the MosaicToNewRaster exercise
# ----------------------------------------------------------------------------------------------------

# -----------------------
# ----- Preparation -----
# -----------------------

# Import arcpy module
import arcpy
from arcpy.sa import Raster, Con, Int
from arcpy import env

# Import numpy
import numpy as np

# Import os
import os

# Import sys & time
# import sys
# import time

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

# Set data and input directories
data_dir = r"Q:\Projects\PRJ_Schelde\Ecotide\Vogels\PRJ_Reservegebieden\Data\INPUT DD SLOPE"
output_dir = r"Q:\Projects\PRJ_Schelde\Ecotide\Vogels\PRJ_Reservegebieden\Output"

alloc_dir = r"Q:\Projects\PRJ_Schelde\Ecotide\Basis\Data\Allocatiegrid"
alloc_gdb = os.path.join(alloc_dir, "Allocatiegrid.gdb")

dtm_dir = r"Q:\Projects\PRJ_Schelde\Ecotide\Habitats\PRJ_Reservegebieden\Data\Combigrids"
dtm_gdb = os.path.join(dtm_dir, "Combigrids.gdb")

# Set output geodatabase
gdb_name = "input_DD_" + alternative_scenario + ".gdb"
output_gdb = os.path.join(output_dir, gdb_name)

if not arcpy.Exists(output_gdb):
    arcpy.CreateFileGDB_management(output_dir, gdb_name)

# Set environment settings (scratch workspace should be the same as current workspace to avoid issues with map algebra)
env.workspace = env.scratchWorkspace = output_gdb
env.overwriteOutput = True
env.addOutputsToMap = False
env.parallelProcessingFactor = "25%"

# --------------------
# ------ INPUTS ------
# --------------------
print("Inputs")

# ---- Allocatielayer ----
# Make a temporary layer from the allocatielayer
feature_class = os.path.join(alloc_gdb, "AllocatieAspntScheldeRupelbekken_BL_ECOTIDE")
arcpy.MakeFeatureLayer_management(feature_class, "allocatie_lyr")

# ---- DTM ----
dtm_path = os.path.join(dtm_gdb, "Combigrid_16B_mTAW_" + alternative)
dtm = Raster(dtm_path)
env.cellSize = dtm

# ---- Data table ----
table_name = "dd_interpolated_" + alternative_scenario + ".xlsx"
sheet_name = "Sheet1"
excel_table = os.path.join(data_dir, table_name)

# -------------------
# ----- PROCESS -----
# -------------------
print("... Processing")

# Convert .xls sheet to table
out_table = os.path.join(output_gdb, "dd_interpolated_table")
arcpy.ExcelToTable_conversion(excel_table, out_table, sheet_name)

# Join dd table
arcpy.AddJoin_management("allocatie_lyr", "AllocNR", out_table, "AllocNR", "KEEP_COMMON")

percentages = np.arange(5, 100, 5)

# start_time = time.time()

# Start the loop
for p in percentages:

    # elapsed = time.time() - start_time
    # print("... ... Running DD %d %% | Time: %.1fs" % (p, elapsed))

    # Polygon to Raster
    dd_output_raster = "DD" + str(p) + "_minus_DTM" # output
    field_to_rasterize = "DD_" + str(p)
    table_name = (out_table.split("\\"))[-1]  # the table name is the last part of the path for the table_to_join
    arcpy.PolygonToRaster_conversion(in_features = "allocatie_lyr",
                                     value_field = table_name + "." + field_to_rasterize,
                                     out_rasterdataset = dd_output_raster,
                                     cell_assignment = "CELL_CENTER", 
                                     priority_field = "NONE", 
                                     cellsize = dtm)

    # Subtract dtm
    dd_min = Raster(dd_output_raster) - dtm

    # Reclassify
    if p == 5:
        # If dd_min <= 0 -> 5, else -> 0
        Reclass_DD_raster = Int(Con(dd_min <= 0, p, 0))
    else:
        # If dd_min <= 0 -> p, else -> NoData
        Reclass_DD_raster = Int(Con(dd_min <= 0, p))

    reclass_path = os.path.join(output_gdb, "Reclass_DD" + str(p))
    Reclass_DD_raster.save(reclass_path)
    
    del dd_min
    del Reclass_DD_raster
    arcpy.Delete_management(dd_output_raster)

# Remove Join
arcpy.RemoveJoin_management("allocatie_lyr")

# Mosaic to new raster
print("... Executing MosaicToNewRaster")

DD_Schelde = "Vogelmodel_DD_" + alternative_scenario  # output
all_files = arcpy.ListRasters("Reclass*")
arcpy.MosaicToNewRaster_management(input_rasters = all_files, 
                                   output_location = env.workspace, 
                                   raster_dataset_name_with_extension = DD_Schelde,
                                   pixel_type = "8_BIT_UNSIGNED", 
                                   number_of_bands = 1,
                                   mosaic_method = "MAXIMUM",
                                   mosaic_colormap_mode = "FIRST")

print("Output saved!")

# ----------------------
# ----- (optional) -----
# ----------------------
files_to_delete = arcpy.ListRasters("Reclass*")

for item in files_to_delete:
    arcpy.management.Delete(item)

print("Redundant raster files deleted")