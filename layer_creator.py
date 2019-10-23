import arcpy

# Assign variables to common paths



#using output_gdb now, will transition to in memory
output_gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"

if not arcpy.Exists(output_gdb):
    arcpy.CreateFileGDB_management(r"C:\temp", "FFE_working.gdb")


#input_excel = "//besfile1/ASM_Projects/E11166_Msspp/Research/Survey/Excel/Surveyed_E11166_07052019_AddOn.xls"

#excel_sheet = "Table 1"

#output_table = output_gdb + r"\new_ffe"

#sr = arcpy.SpatialReference("NAD 1983 HARN StatePlane Oregon North FIPS 3601 (Intl Feet)")
#ffe_template = output_gdb + "/ffe_template"



egh_public = r"\\oberon\grp117\DAshney\Scripts\connections\egh_public on gisdb1.rose.portland.local.sde"

#master_address = output_gdb + r"\master_address"
master_address = egh_public + r"\ARCMAP_ADMIN.Master_Address_Points_pdx"
address_locator = egh_public + r"\ARCMAP_ADMIN.Streets_Geocoding_pdx_no_zone"

## Creates an empty feature class based on a template and converts the excel input to a table
## Returns the table path
        ## this could be split into 2 functions
def create_ffe_points_layer(input_excel, excel_sheet, output_gdb):
    output_table = output_gdb + r"\new_ffe"

    arcpy.ExcelToTable_conversion(Input_Excel_File= input_excel, Output_Table=output_table, Sheet=excel_sheet)

    return output_gdb + "/new_ffe"


def create_point_feature_class_with_template(name):
    sr = arcpy.SpatialReference("NAD 1983 HARN StatePlane Oregon North FIPS 3601 (Intl Feet)")
    ffe_template = output_gdb + "/ffe_template"
    arcpy.CreateFeatureclass_management(output_gdb, name, "POINT", ffe_template, "DISABLED", "DISABLED", sr)
    return output_gdb + "/" + name


def append_tables_to_single_featureclass(main, additional):
    arcpy.Append_management(additional, main, "NO_TEST")

##Takes the table that does not have geometry, and creates a featureclass from it
##
def geocode_ffe_points_with_master_address_points(input_table, feature_class_path):

    input_table_fields = ["Address", "Elevation", "Basement"]
    address_locator = egh_public + r"\ARCMAP_ADMIN.Streets_Geocoding_pdx_no_zone"
    master_address = egh_public + r"\ARCMAP_ADMIN.Master_Address_Points_pdx"
    insert_cursor = arcpy.da.InsertCursor(feature_class_path, input_table_fields)
    address_list =[]

    with arcpy.da.SearchCursor(input_table, input_table_fields) as search_cursor:
        for row in search_cursor:
            insert_cursor.insertRow(row)
            address_list.append(row[0])

        del search_cursor, insert_cursor

    address_list_2 = [str(r) for r in address_list]
    address_tuple = tuple(address_list_2)

    field_list = ["ADDRESS_FULL", "@SHAPE"]
    query = "COUNTY NOT IN( 'COLUMBIA' , 'MARION' , 'WASHINGTON' ) AND ADDRESS_FULL in %s" % (address_tuple,)

    #arcpy.Delete_management(input_table)
    # Create a layer that has the matching addresses and save it
    arcpy.MakeFeatureLayer_management(master_address, "qt", query)

    geometries = {key:value for (key,value) in arcpy.da.SearchCursor("qt", ["ADDRESS_FULL", 'Shape'])}

    notfound = []

    #Update B with geometries from A where ID:s match
    with arcpy.da.UpdateCursor(feature_class_path, ["Address", 'SHAPE@', 'Elevation', 'Basement']) as cursor:
        for row in cursor:
            try:
                row[1] = geometries[row[0]]
                cursor.updateRow(row)
            except:
                notfound.append(tuple((row[0], row[2], row[3])))

        del row, cursor

    print 'Found no id match and could not update geometry for IDs: ', notfound
    return notfound


#####
#####
#####
def geocode_ffe_points_with_taxlots(input_table, feature_class_path):

    input_table_fields = ["Address", "Elevation", "Basement"]
    taxlots = egh_public + r"\ARCMAP_ADMIN.taxlots_pdx"
    address_list = []

    insert_cursor = arcpy.da.InsertCursor(feature_class_path, input_table_fields)

    with arcpy.da.SearchCursor(input_table, input_table_fields) as search_cursor:
        for row in search_cursor:
            insert_cursor.insertRow(row)
            address_list.append(row[0])

        del search_cursor, insert_cursor

    address_list_2 = [str(r) for r in address_list]
    address_tuple = tuple(address_list_2)

    field_list = ["SITEADDR", "@SHAPE"]
    query = "SITECITY in('PORTLAND') AND SITEADDR in %s" % (address_tuple,)

    #arcpy.Delete_management(input_table)

    # Create a layer that has the matching addresses and save it
    arcpy.MakeFeatureLayer_management(taxlots, "temp_layer", query)

    geometries = {key:value for (key,value) in arcpy.da.SearchCursor("temp_layer", ["SITEADDR", 'Shape'])}

    notfound = []

    #Update B with geometries from A where ID:s match
    with arcpy.da.UpdateCursor(feature_class_path, ["Address", 'SHAPE@', 'Elevation', 'Basement']) as cursor:
        for row in cursor:
            try:
                row[1] = geometries[row[0]]
                cursor.updateRow(row)
            except:
                notfound.append(tuple((row[0], row[2], row[3])))

        del row, cursor

    print 'Found no id match and could not update geometry for IDs: ', notfound
    return notfound







def geocode_ffe_points_with_address_locator(not_found_list, feature_class_path):
    # At this point there is a completed feature class that has spatial data for all points that match the master address list and we have a list of addresses that dont match

### create a new table from the unmatched records using the other table as a template
 #TODO: these use file paths that sould be removed

    arcpy.CreateTable_management(r"C:\temp\ffe_scratch\ffe_working.gdb", "unmatched_ffe" )

    arcpy.AddField_management(r"C:\temp\ffe_scratch\FFE_working.gdb\unmatched_ffe", 'Address', "TEXT", "", "", 50)
    arcpy.AddField_management(r"C:\temp\ffe_scratch\FFE_working.gdb\unmatched_ffe", 'Elevation', "FLOAT",)
    arcpy.AddField_management(r"C:\temp\ffe_scratch\FFE_working.gdb\unmatched_ffe", 'Basement', "TEXT", "", "", 5)

    arcpy.AddField_management(r"C:\temp\ffe_scratch\FFE_working.gdb\unmatched_ffe", 'City', "TEXT", "", "", 8)


    if not_found_list:
        cursor = arcpy.da.InsertCursor(r"C:\temp\ffe_scratch\FFE_working.gdb\unmatched_ffe", ['Address', 'Elevation', 'Basement'])

        for row in not_found_list:
            cursor.insertRow(row)

        del row, cursor

        arcpy.CalculateField_management(r"C:\temp\ffe_scratch\FFE_working.gdb\unmatched_ffe", "City", "'Portland'", "PYTHON")

        # run that table through the geocode process to create geometry for the remaining points

        arcpy.GeocodeAddresses_geocoding(r"C:\temp\ffe_scratch\ffe_working.gdb\unmatched_ffe", address_locator, "Address Address", r"C:\temp\ffe_scratch\ffe_working.gdb\geocoded_ffe")



        #create a lookup for the geometries based on their address

        arcpy.MakeFeatureLayer_management(r"C:\temp\ffe_scratch\ffe_working.gdb\geocoded_ffe", "qc")

        geometries2 = {key:value for (key,value) in arcpy.da.SearchCursor("qc", ["ARC_Single_Line_Input", 'Shape'])}

        notfound2 = []

        #Update B with geometries from A where ID:s match
        with arcpy.da.UpdateCursor(feature_class_path, ["Address", 'SHAPE@', 'Elevation', 'Basement']) as cursor:
            for row in cursor:
                try:
                    row[1] = geometries2[row[0]]
                    cursor.updateRow(row)
                except:
                    notfound2.append(tuple((row[0], row[2], row[3])))

            del row, cursor

        print 'Found no id match and could not update geometry for IDs: ', notfound2

        # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
        # The following inputs are layers or table views: "unmatched_ffe"
