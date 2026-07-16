# -*- coding: utf-8 -*-
import arcpy
import os
import csv
from arcpy.sa import *
from arcpy import env

# Check out Spatial Analyst
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    print("Spatial Extension not available")
    exit()

import sys
if 'functions' in sys.modules:
    del sys.modules['functions']

try:
    import functions as f
    print("... functions.py succesvol ingeladen")
except ImportError:
    print ("FOUT: functions.py niet gevonden.")
    exit()

# ------------------------------------------------------
# ----- alternative & scenario definiëren -----
# ------------------------------------------------------

# !! aanpassen indien nodig
alternative = "REF_2020"
#scenario = "HIC"
scenario = "Scaldis"

alternative_scenario = alternative + "_" + scenario

# ----------------------------------------------------------
# ----- Paden definiëren -----
# ----------------------------------------------------------

base_input =     r"Q:\Projects\PRJ_Schelde\Ecotide\Basis\Data"
base_input_gdb = r"Q:\Projects\PRJ_Schelde\Ecotide\Habitats\PRJ_Reservegebieden\Output\Fysiotopen"
base_output =    r"Q:\Projects\PRJ_Schelde\Ecotide\Habitats\PRJ_Reservegebieden\Output\Fysiotopen\habitat_kenmerken"

# verwijzing naar allocgrid > km nu naar Dist laten verwijzen (/1000!) alsook naar segment (rivierstuk) om dubbele Dists te vermijden
km_kaart =     os.path.join(base_input, "Allocatiegrid", "Allocatiegrid.gdb", "AllocatieAspntScheldeRupelbekken_L")
mask_ref_noC = os.path.join(base_input, "Mask_gebiedsindeling" , "Mask2020_REF.gdb", "Habmap_Intplan_Zeeschelde_Mask_2020REF")

# !! aanpassen indien nodig
#hab_map_gdb = os.path.join(base_input_gdb, "Habitatkaart_HIC_INBO.gdb")
hab_map_gdb = os.path.join(base_input_gdb, "Habitatkaart_IPscen_INBO.gdb")
habitat_map = os.path.join(hab_map_gdb, "Habmap_2020REF_16B")

db_name = "Scaldis_vs_HIC_TEMP.gdb"
geodatabase = os.path.join(base_output, db_name)
# !! OPGELET !! om het script te laten lopen met een nieuwe ecotopenkaart moet de copy in deze gdb worden verwijderd

table_path = os.path.join(base_output, "tabellen_Scaldis_vs_HIC")

# ----------------------------------------------------------
# ----- Initialisatie -----
# ----------------------------------------------------------
out_gdb_dir = os.path.dirname(geodatabase)
if not arcpy.Exists(out_gdb_dir): os.makedirs(out_gdb_dir)
if not arcpy.Exists(geodatabase): arcpy.CreateFileGDB_management(out_gdb_dir, db_name)
if not os.path.exists(table_path): os.makedirs(table_path)

env.workspace = geodatabase
env.overwriteOutput = True

try:
    print("--- Start verwerking scenario: " + alternative_scenario + " ---")

    # 1. Voorbereiding Habitatkaart
    habitat_map_copy = "Habmap_copy_" + alternative_scenario
    if not arcpy.Exists(habitat_map_copy):
        print("... Kopieer habitatkaart en bereken Habmap2")
        arcpy.CopyFeatures_management(habitat_map, habitat_map_copy)
        arcpy.AddField_management(habitat_map_copy, "Habmap2", "TEXT")
        codeblock_h2 = """def Habmap2(Habmap):
            h = Habmap.lower() if Habmap else ""
            if "slik" in h: return "slik"
            elif "ondiep subtidaal" in h: return "ondiep subtidaal"
            elif "matig diep subtidaal" in h: return "matig diep subtidaal"
            elif "diep subtidaal" in h: return "diep subtidaal"
            else: return Habmap"""
        arcpy.CalculateField_management(habitat_map_copy, "Habmap2", "Habmap2(!Habmap!)", "PYTHON_9.3", codeblock_h2)
    else:
        print("... Skip voorbereiding: " + habitat_map_copy + " bestaat al.")

    # --- DEEL A: KM-ANALYSE ---
    km_csv = os.path.join(table_path, "Habmap_" + alternative_scenario + "_km.csv")
    habitat_map_km_singlepart = "Habmap_km_singlepart_" + alternative_scenario

    print("... Stap A: Kilometer analyse")
    if not os.path.exists(km_csv):
        habitat_map_km = "Habmap_km_" + alternative_scenario
        arcpy.Intersect_analysis([habitat_map_copy, km_kaart], habitat_map_km)

        # 1. Voeg het 'km' veld toe aan de geïntersecteerde laag
        print("... Voeg km-veld toe")
        arcpy.AddField_management(habitat_map_km, "km", "DOUBLE")

        # 2. Bereken de km's op basis van het 'Dist' veld (meters / 1000)
        print("... Bereken km op basis van 'Dist' (/1000)")
        arcpy.CalculateField_management(habitat_map_km, "km", "!Dist! / 1000.0", "PYTHON_9.3")

        diss_fields_km = ["ModelGebied_C", "SalZone", "Omessegment", "KRWzone", "km", "SegmentID", "Habmap", "Habmap2"]
        actual_diss_km = [field.name for field in arcpy.ListFields(habitat_map_km) if field.name in diss_fields_km]

        arcpy.Dissolve_management(habitat_map_km, habitat_map_km_singlepart, actual_diss_km, "", "SINGLE_PART")

        f.export_to_csv(habitat_map_km_singlepart, km_csv, actual_diss_km)
    else:
        print("    -> Skip Stap A: Output CSV bestaat al.")

    # --- DEEL B: CLIP NAAR MASKER (ZONDER C) ---
    # !!! export is inactief; evalueren of deze stap relevant is binnen PRJ_reservegebieden
    km_noC_csv = os.path.join(table_path, "Habmap_zonderC_" + alternative_scenario + "_km.csv")
    habitat_map_km_noC = "Habmap_km_zonderC_" + alternative_scenario

    print("... Stap B: Clip naar Masker (zonder C) -> !!! WAARSCHUWING: er wordt geen export uitgevoerd")
    if not os.path.exists(km_noC_csv):
        # We hebben de singlepart van A nodig; als die door de skip niet is gemaakt, moeten we die even checken
        if not arcpy.Exists(habitat_map_km_singlepart):
            raise Exception(
                "Fout: Stap B heeft " + habitat_map_km_singlepart + " nodig uit stap A, maar deze ontbreekt.")

        arcpy.Clip_analysis(habitat_map_km_singlepart, mask_ref_noC, habitat_map_km_noC)

        # Gebruik velden van de input
        actual_diss_km = [field.name for field in arcpy.ListFields(habitat_map_km_noC) if
                          field.name in ["ModelGebied", "SalZone", "OMES", "KRWzone", "km", "SegmentID", "Habmap", "Habmap2"]]
        # f.export_to_csv(habitat_map_km_noC, km_noC_csv, actual_diss_km)
    else:
        print("    -> Skip Stap B: Output CSV bestaat al.")

    # --- DEEL C: OMES-ANALYSE ---
    # !!! export is inactief; evalueren of deze stap relevant is binnen PRJ_reservegebieden
    
    print("... Stap C: OMES analyse -> !!! WAARSCHUWING: er wordt geen export uitgevoerd")
    omes_xls = os.path.join(table_path, "Habmap_OMES_analysis_" + alternative_scenario + ".xls")
    out_omes_single = "Habmap_OMES_singlepart_" + alternative_scenario
    out_omes_multi = "Habmap_OMES_multipart_" + alternative_scenario

    if not os.path.exists(omes_xls) or not arcpy.Exists(out_omes_multi):
        # 1. SCAN DE BRON (habitat_map_copy) - VEILIG MET field
        all_fields_src = [field.name for field in arcpy.ListFields(habitat_map_copy)]
        print("DEBUG: Velden in BRON ({0}): {1}".format(habitat_map_copy, str(all_fields_src)))

        # Zoek de juiste namen in de bron
        m_f_src = next((field for field in all_fields_src if field.lower() in ["modelgebied", "modelgebied_c"]), None)
        o_f_src = next((field for field in all_fields_src if "omes" in field.lower()), None)
        h_f_src = next((field for field in all_fields_src if field.lower() == "habmap2"), None)

        # Maak lijst voor dissolve
        actual_diss_omes = [field for field in [m_f_src, o_f_src, h_f_src, "SalZone", "KRWzone"] if field]
        print("... Gebruikte velden voor Dissolve: " + str(actual_diss_omes))

        # 2. Check of OMES wel gevonden is
        if o_f_src is None:
            print("!!! WAARSCHUWING: Geen OMES-veld gevonden in bron!")

        # 3. Maak de Singlepart
        if not arcpy.Exists(out_omes_single):
            print("... Bezig met Dissolve naar Singlepart")
            arcpy.Dissolve_management(habitat_map_copy, out_omes_single, actual_diss_omes, "", "SINGLE_PART")

        # 4. Naar Excel
        if not os.path.exists(omes_xls):
            print("... Conversie naar Excel")
                # arcpy.TableToExcel_conversion(out_omes_single, omes_xls)

        # 5. Naar Multipart & Berekening
        if not arcpy.Exists(out_omes_multi):
            print("... Bezig met final dissolve naar Multipart")
            arcpy.Dissolve_management(out_omes_single, out_omes_multi, actual_diss_omes, "", "MULTI_PART")

            # Voeg veld toe aan de zojuist gemaakte laag
            arcpy.AddField_management(out_omes_multi, "ModGeb_OMES_Hbm2", "TEXT", field_length=200)

            # Check velden in de NIEUWE tabel
            final_fields = [field.name for field in arcpy.ListFields(out_omes_multi)]
            m_f = next((field for field in final_fields if field.lower() in ["modelgebied", "modelgebied_c"]), None)
            o_f = next((field for field in final_fields if "omes" in field.lower()), None)
            h_f = next((field for field in final_fields if field.lower() == "habmap2"), None)

            if None in [m_f, o_f, h_f]:
                print("FOUT: Velden niet gevonden in multipart! M:{0}, O:{1}, H:{2}".format(m_f, o_f, h_f))
            else:
                code_block = """def combine(m, o, h):
                                    m_val = str(m) if m is not None else "Unknown"
                                    o_val = str(o) if o is not None else "0"
                                    h_val = str(h) if h is not None else "Unknown"
                                    return m_val + ":" + o_val + ":" + h_val"""

                exp = "combine(!{0}!, !{1}!, !{2}!)".format(m_f, o_f, h_f)
                print("... Berekenen met expressie: " + exp)
                arcpy.CalculateField_management(out_omes_multi, "ModGeb_OMES_Hbm2", exp, "PYTHON_9.3", code_block)
    else:
        print("    -> Skip Stap C: Excel en Multipart bestaan al.")

except Exception as e:
    print("FOUT opgetreden: " + str(e))

print("--- Script klaar ---")