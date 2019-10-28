import arcpy
import re

egh_public = r"\\oberon\grp117\DAshney\Scripts\connections\egh_public on gisdb1.rose.portland.local.sde"

#master_address = output_gdb + r"\master_address"
#master_address = egh_public + r"\ARCMAP_ADMIN.Master_Address_Points_pdx"


## Creates an empty feature class based on a template and converts the excel input to a table
## Returns the table path
        ## this could be split into 2 functions
def create_ffe_points_layer(input_excel, excel_sheet, output_gdb):
    output_table = output_gdb + r"\new_ffe"

    arcpy.ExcelToTable_conversion(Input_Excel_File= input_excel, Output_Table=output_table, Sheet=excel_sheet)

    arcpy.AddField_management(output_table, "Filtered_Address", "TEXT", "", "",50)

    return output_gdb + "/new_ffe"


#need to be able to add the filtered addresses to the excel table

def create_point_feature_class_with_template(name, output_gdb_path, template_path):
    sr = arcpy.SpatialReference("NAD 1983 HARN StatePlane Oregon North FIPS 3601 (Intl Feet)")
    arcpy.CreateFeatureclass_management(output_gdb_path, name, "POINT", template_path, "DISABLED", "DISABLED", sr)
    return output_gdb_path + "/" + name


def append_tables_to_single_featureclass(main, additional):
    arcpy.Append_management(additional, main, "NO_TEST")

##Takes the table that does not have geometry, and creates a featureclass from it
def geocode_ffe_points_with_master_address_points(input_table, feature_class_path):
    input_table_fields = ["Address", "Elevation", "Basement"]
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
    arcpy.MakeFeatureLayer_management(master_address, "temp_layer", query)

    geometries = {key:value for (key,value) in arcpy.da.SearchCursor("temp_layer", ["ADDRESS_FULL", 'Shape'])}

    notfound = []

    #Update B with geometries from A where ID:s match
    with arcpy.da.UpdateCursor(feature_class_path, ["Address", 'SHAPE@', 'Elevation', 'Basement', 'GeocodingNotes']) as cursor:
        for row in cursor:
            try:
                row[1] = geometries[row[0]]
                row[4] = "Master Address"
                cursor.updateRow(row)
            except:
                notfound.append(tuple((row[0], row[2], row[3])))
                cursor.deleteRow()

        del row, cursor

    print 'Found no id match and could not update geometry for IDs: ', notfound

    return notfound


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
    arcpy.MakeFeatureLayer_management(taxlots, "temp_layer_2", query)
    geometries = {key:value for (key,value) in arcpy.da.SearchCursor("temp_layer_2", ["SITEADDR", 'Shape'])}
    notfound = []
    #Update B with geometries from A where ID:s match
    with arcpy.da.UpdateCursor(feature_class_path, ["Address", 'SHAPE@', 'Elevation', 'Basement', 'GeocodingNotes']) as cursor:
        for row in cursor:
            try:
                row[1] = geometries[row[0]]
                row[4] = "Taxlot"
                cursor.updateRow(row)
            except:
                notfound.append(tuple((row[0], row[2], row[3])))
                cursor.deleteRow()

        del row, cursor

    print 'Found no id match and could not update geometry for IDs: ', notfound
    return notfound

def geocode_ffe_points_with_address_locator(not_found_path, feature_class_path):
    address_locator = egh_public + r"\ARCMAP_ADMIN.Streets_Geocoding_pdx_no_zone"
    arcpy.CalculateField_management(not_found_path, "City", "'Portland'", "PYTHON")
    address_fields_city = "conditioned_address Address; City City"

    arcpy.AlterField_management(not_found_path, "Address", "original_address")
    arcpy.AlterField_management(not_found_path, "conditioned_address", "Address")

    arcpy.GeocodeAddresses_geocoding(not_found_path, address_locator, "", feature_class_path)

    arcpy.AlterField_management(feature_class_path, "Address", "conditioned_address")
    arcpy.AlterField_management(feature_class_path, "original_address", "Address")


    add_text_field_to_feature_class(feature_class_path,'GeocodingNotes', 15)

    with arcpy.da.UpdateCursor(feature_class_path, ['GeocodingNotes', 'Status']) as cursor:
        for row in cursor:
            if row[1] =='U':
                row[0] = "UNMATCHED"
            else:
                row[0] = "Address Locater"
            cursor.updateRow(row)


    drop_fields = ["Status", "Score", "Match_addr", "Pct_along", "Side", "Ref_ID", "X", "Y", "Addr_type", "ARC_Street", "ARC_City", "ARC_ZIP"]

    if arcpy.TestSchemaLock(feature_class_path):
        arcpy.DeleteField_management(feature_class_path, drop_fields)
    else:
        print("ArcPy will not unlock the geocoded ffe")


def create_table_from_list(not_found_list, output_gdb_path, table_name):
    full_table_path = output_gdb_path + "/" + table_name
    arcpy.CreateTable_management(output_gdb_path, table_name)
    arcpy.AddField_management(full_table_path, 'Address', "TEXT", "", "", 50)
    arcpy.AddField_management(full_table_path, 'Elevation', "FLOAT", )
    arcpy.AddField_management(full_table_path, 'Basement', "TEXT", "", "", 5)
    arcpy.AddField_management(full_table_path, 'City', "TEXT", "", "", 8)
    cursor = arcpy.da.InsertCursor(full_table_path, ['Address', 'Elevation', 'Basement'])
    for row in not_found_list:
        cursor.insertRow(row)
    del row, cursor
    return full_table_path

def remove_address_ranges_from_list_of_addresses(list):
    new_list = []
    regex_1 = re.compile(r'(?:-\w+)+') # this gets the hyphen without spaces
    regex_2 = re.compile(r'(?:-+\s\w+)+') # this gets the hyphen that includes spaces

    for i in list:
        if re.search(r'(?:-\w+)+', i[0]):
            replacement_address = regex_1.sub("", i[0])
            new_tuple = (replacement_address, i[1], i[2])
            new_list.append(new_tuple)
        elif re.search(r'(?:-+\s\w+)+', i[0]):
            replacement_address = regex_2.sub("", i[0])
            new_tuple = (replacement_address, i[1], i[2])
            new_list.append(new_tuple)
        else:
            new_tuple = (i[0], i[1], i[2])
            new_list.append(new_tuple)


    return new_list

def filter_address_with_regex(address):
    regex_1 = re.compile(r'(?:-\w+)+') # this gets the hyphen without spaces
    regex_2 = re.compile(r'(?:-+\s\w+)+') # this gets the hyphen that includes spaces
    regex_3 = re.compile(r'(?:\s(\d+)\b)') #this gets the case where we have 2 numbers with no hyphen

    if re.search(r'(?:-\w+)+', address):
        replacement_address = regex_1.sub("", address)
        return replacement_address
    elif re.search(r'(?:-+\s\w+)+', address):
        replacement_address = regex_2.sub("", address)
        return replacement_address
    elif re.search(r'(?:\s(\d+)\b)', address):
        replacement_address = regex_3.sub("", address)
        return replacement_address
    else:
        return address

def add_text_field_to_feature_class(feature_class, field_name, text_length):

    arcpy.AddField_management(feature_class, field_name,"TEXT", "", "", text_length)

def update_field_with_conditioned_address(feature_class, source_field_name, update_field_name):
    with arcpy.da.UpdateCursor(feature_class, [source_field_name, update_field_name]) as cursor:
        for row in cursor:
            row[1] = filter_address_with_regex(row[0])
            cursor.updateRow(row)