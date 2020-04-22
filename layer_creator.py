import arcpy
import re
import xlrd
import join_field
import time

egh_public = r"\\oberon\grp117\DAshney\Scripts\connections\egh_public on gisdb1.rose.portland.local.sde"



# Creates an empty feature class based on a template and converts the excel input to a table
# Returns the table path

def create_ffe_points_layer(input_excel, excel_sheet, output_gdb):
    output_table = output_gdb + r"\new_ffe"
    arcpy.ExcelToTable_conversion(Input_Excel_File= input_excel, Output_Table=output_table, Sheet=excel_sheet)
    return output_gdb + "/new_ffe"

def create_feature_class_template():
    sr = arcpy.SpatialReference("NAD 1983 HARN StatePlane Oregon North FIPS 3601 (Intl Feet)")
    #temp = arcpy.CreateFeatureclass_management(r"C:\temp\ffe_scratch\FFE_working.gdb", "template", "POINT","", "DISABLED", "DISABLED", sr)

    temp = arcpy.CreateFeatureclass_management("in_memory", "template", "POINT","", "DISABLED", "DISABLED", sr)
    #need to start with having this field named improperly so it does not mess with later joins
    #arcpy.AddField_management(temp, "SITEADDR", "TEXT", "", "", 75)

    arcpy.AddField_management(temp, "RNO", "TEXT", "", "", 20)
    #arcpy.AddField_management(temp, "SURVEYFFE", "DOUBLE")
    arcpy.AddField_management(temp, "NOBSMT", "SHORT")
    arcpy.AddField_management(temp, "SURVEYDATE", "DATE")
    arcpy.AddField_management(temp, "NOTES", "TEXT", "", "", 200)
    arcpy.AddField_management(temp, "AREA_ID", "LONG")
    arcpy.AddField_management(temp, "AREA_NAME", "TEXT", "", "", 255)
    arcpy.AddField_management(temp, "ADDATE", "DATE")

    #Create some temporary fields so we can start testing this our with minimal changes
    arcpy.AddField_management(temp, "Address", "TEXT", "", "", 50)
    arcpy.AddField_management(temp, "Elevation", "FLOAT")
    arcpy.AddField_management(temp, "Basement", "TEXT", "", "", 10)
    arcpy.AddField_management(temp, "GeocodingNotes", "TEXT", "", "", 15)

    return temp


def create_point_feature_class_with_template(name, output_gdb_path, template_path):
    sr = arcpy.SpatialReference("NAD 1983 HARN StatePlane Oregon North FIPS 3601 (Intl Feet)")
    arcpy.CreateFeatureclass_management(output_gdb_path, name, "POINT", template_path, "DISABLED", "DISABLED", sr)
    return output_gdb_path + "/" + name


def append_tables_to_single_featureclass(main, additional):
    arcpy.Append_management(additional, main, "NO_TEST")


# Takes the table that does not have geometry, and creates a featureclass from it
def geocode_ffe_points_with_master_address_points(input_table, feature_class_path):
    input_table_fields = ["Address", "Elevation", "Basement", "Notes"]
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

    #field_list = ["ADDRESS_FULL", "@SHAPE"]
    query = "COUNTY NOT IN( 'COLUMBIA' , 'MARION' , 'WASHINGTON' ) AND ADDRESS_FULL in %s" % (address_tuple,)

    # Create a layer that has the matching addresses and save it
    arcpy.MakeFeatureLayer_management(master_address, "temp_layer", query)

    geometries = {key:value for (key,value) in arcpy.da.SearchCursor("temp_layer", ["ADDRESS_FULL", 'Shape'])}

    notfound = []

    # Update B with geometries from A where ID:s match
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

    #print 'Found no id match and could not update geometry for IDs: ', notfound

    return notfound


def geocode_ffe_points_with_taxlots(input_table, feature_class_path):
    input_table_fields = ["Address", "Elevation", "Basement", "Notes"]
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

    query = "SITECITY in('PORTLAND') AND SITEADDR in %s" % (address_tuple,)

    # Create a layer that has the matching addresses and save it
    arcpy.MakeFeatureLayer_management(taxlots, "temp_layer_2", query)
    geometries = {key:value for (key,value) in arcpy.da.SearchCursor("temp_layer_2", ["SITEADDR", 'Shape'])}
    notfound = []

    # Update B with geometries from A where ID:s match
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

    #print 'Found no id match and could not update geometry for IDs: ', notfound
    return notfound

def geocode_ffe_points_with_address_locator(not_found_path, feature_class_path):
    address_locator = egh_public + r"\ARCMAP_ADMIN.Streets_Geocoding_pdx_no_zone"
    arcpy.CalculateField_management(not_found_path, "City", "'Portland'", "PYTHON")
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
        pass
        #print("ArcPy will not unlock the geocoded ffe")


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
    print(new_list)
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

def geocode_address_table_with_x_y_values(input_table, feature_class_path):
    sr = arcpy.SpatialReference("NAD 1983 HARN StatePlane Oregon North FIPS 3601 (Intl Feet)")
    temp_layer = arcpy.MakeXYEventLayer_management(input_table,"X_COORD", "Y_COORD", "Temp_XY_Layer", sr)
    filtered_layer = filter_x_y_table_for_ffe(temp_layer)

    arcpy.CopyFeatures_management(filtered_layer, feature_class_path)


def filter_x_y_table_for_ffe(x_y_layer):
    query = "TYPE in ('FFE', 'FFEB')"
    ffe_query_layer = arcpy.MakeFeatureLayer_management(x_y_layer, "ffe_layer", query)
    return ffe_query_layer

def find_nearest_taxlot_to_x_y_point(feature_class_path):

    taxlots = egh_public + r"\ARCMAP_ADMIN.taxlots_pdx"
    arcpy.Near_analysis(feature_class_path, taxlots, "", "LOCATION")

def add_nearest_site_address_to_x_y_points(feature_class_path):
    taxlots = egh_public + r"\ARCMAP_ADMIN.taxlots_pdx"
    join_field.join(feature_class_path, "NEAR_FID", taxlots, "OBJECTID", "SITEADDR")


def rename_field(input_table, old_field_name, new_field_name):
    arcpy.AlterField_management(input_table, old_field_name, new_field_name)

def return_list_of_excel_fields_from_sheet(excel_workbook, excel_sheet):
    wb = xlrd.open_workbook(excel_workbook)
    sheet = wb.sheet_by_name(excel_sheet)
    wb.release_resources()
    field_list = []

    for i in range(sheet.ncols):
        field_list.append(sheet.cell_value(0, i))

    return field_list

def return_list_of_fields_from_table(input_table):
    field_list = []
    fields = arcpy.ListFields(input_table)

    for field in fields:
        field_list.append(field.name)
    return field_list

def delete_all_fields_except_as_specified_and_geometry(input_table, fields_to_keep):
    all_fields = return_list_of_fields_from_table(input_table)
    fields_to_delete = [x for x in all_fields if x not in fields_to_keep]

    if arcpy.TestSchemaLock(input_table):
        arcpy.DeleteField_management(input_table, fields_to_delete)
    else:
        pass
        #print("ArcPy will not unlock the table")


def search_list_of_fields_for_keyword(field_list, keyword):
    if keyword in field_list:
        return True
    return False


def search_list_of_fields_for_key_words(keyword_list, field_list):
    return all(elem in field_list for elem in keyword_list)

def convert_type_code_to_y_or_no(input_table):
    with arcpy.da.UpdateCursor(input_table, ["TYPE", "Basement"]) as cursor:
        for row in cursor:
            if row[0].upper() == "FFEB":
                row[1] = "Y"
            elif row[0].upper() == "FFE":
                row[1] = "N"
            else:
                pass
            cursor.updateRow(row)

def create_ffe_from_excel_with_addresses(excel_workbook, excel_sheet, output_gdb, feature_class_name):

    output_gdb_in_memory = "in_memory"
    ffe_taxlots = output_gdb_in_memory + r"/FFE_points_taxlots"

    ffe_template_path = r"C:\temp\ffe_scratch\FFE_working.gdb\ffe_template"

    output_featureclass_path = output_gdb + "\\" + feature_class_name

    feature_classes_to_append = []

    # if excel_sheet is None or excel_sheet == "":
    #     excel_sheet = get_sheet_names(excel_workbook)

    # Create a table from the input ffe excel spread sheet
    new_table = create_ffe_points_layer(excel_workbook, excel_sheet, output_gdb_in_memory)

    # Create empty feature classes from  template

    newTemplate = create_feature_class_template()
    feature_class_name = create_point_feature_class_with_template(feature_class_name, output_gdb, newTemplate)

    additional_fc = create_point_feature_class_with_template("FFE_points_taxlots", output_gdb_in_memory, newTemplate)


    # Geocode the ffe points using a first pass from master address points and a second pass from the address locator
    unmatched_address_list = geocode_ffe_points_with_master_address_points(new_table, feature_class_name)

    if len(unmatched_address_list) > 0:

        unmatched_address_table = create_table_from_list(unmatched_address_list, output_gdb_in_memory, "unmatched_ffe")

        #  ffe points using the taxlot addresses

        unmatched_address_list_2 = geocode_ffe_points_with_taxlots(unmatched_address_table, additional_fc)

        feature_classes_to_append.append(ffe_taxlots)
        if len(unmatched_address_list_2) > 0:
            filtered_list = remove_address_ranges_from_list_of_addresses(unmatched_address_list_2)
            print(filtered_list)
            unmatched_address_table_2 = create_table_from_list(filtered_list, output_gdb_in_memory, "unmatched_ffe_2")


            ###Go over the uncoded points using the adddress locator
            geo_locater_fc_path = output_gdb_in_memory + "/geocoded_ffe"

            add_text_field_to_feature_class(unmatched_address_table_2, "conditioned_address", 100)

            update_field_with_conditioned_address(unmatched_address_table_2, "Address", "conditioned_address")

            geocode_ffe_points_with_address_locator(unmatched_address_table_2, geo_locater_fc_path)

            feature_classes_to_append.append(geo_locater_fc_path)

        #combine all three geocoded_feature_classes
    if len(feature_classes_to_append) > 0:
        append_tables_to_single_featureclass(output_featureclass_path, feature_classes_to_append)

    calculate_fields(output_featureclass_path)

def get_sheet_names(in_excel):
    """ Returns a list of sheet names for the selected excel file.
          This function is used in the script tool's Validation
    """
    f = open(r"C:\Users\bfreeman\Desktop\test.txt", "a")
    f.write(" get sheets ")
    f.close()
    try:
        workbook = xlrd.open_workbook(in_excel)
        f = open(r"C:\Users\bfreeman\Desktop\test.txt", "a")
        f.write(" try ")
        f.close()
        return [sheet.name for sheet in workbook.sheets()]
    except:

        return ["two", "three"]

def calculate_fields(feature_class_path):
    bsmt_expression = "def basement(bool):\n   if bool.upper() == 'Y':\n      return 0\n   elif bool.upper() == 'N':\n      return 1\n   else:\n      return -1"
    arcpy.CalculateField_management(feature_class_path, "NOBSMT", "basement( !Basement!)", "PYTHON_9.3", bsmt_expression)
    #notes_expression = "def basement(bool):\n   if bool.upper() == 'Y':\n      return 'Has Basement = YES'\n   elif bool.upper() == 'N':\n      return 'Has Basement = NO'\n   else:\n      return -1"
    #arcpy.CalculateField_management(feature_class_path, "NOTES", "basement( !Basement!)", "PYTHON_9.3", notes_expression)
    arcpy.AlterField_management(feature_class_path, "Address", "SITEADDR")
    arcpy.AlterField_management(feature_class_path, "Elevation", "SURVEYFFE")
    arcpy.DeleteField_management(feature_class_path, "Basement")



def create_ffe_from_X_Y(input_excel, excel_sheet, output_featureclass_path, output_gdb, feature_class_name):
    output_featureclass_path = output_gdb + "/" + feature_class_name
    output_gdb_in_memory = "in_memory"
    ffe = create_ffe_points_layer(input_excel, excel_sheet, output_gdb_in_memory)
    arcpy.AddField_management(ffe, "Basement", "TEXT", "", "", 10)


    geocode_address_table_with_x_y_values(ffe, output_featureclass_path)
    find_nearest_taxlot_to_x_y_point(output_featureclass_path)

    add_nearest_site_address_to_x_y_points(output_featureclass_path)
    rename_field(output_featureclass_path, "SITEADDR", "Address")
    convert_type_code_to_y_or_no(output_featureclass_path)
    fields_to_keep = [u'OBJECTID', "Address", 'SHAPE@', u'Shape', 'Elevation', 'Basement', 'Notes']
    delete_all_fields_except_as_specified_and_geometry(output_featureclass_path, fields_to_keep)

    arcpy.AddField_management(output_featureclass_path, "Basement", "TEXT", "", "", 10)
    #arcpy.AddField_management(output_featureclass_path, "SITEADDR", "TEXT", "", "", 75)

    arcpy.AddField_management(output_featureclass_path, "RNO", "TEXT", "", "", 20)
    #arcpy.AddField_management(output_featureclass_path, "SURVEYFFE", "DOUBLE")
    arcpy.AddField_management(output_featureclass_path, "NOBSMT", "SHORT")
    arcpy.AddField_management(output_featureclass_path, "SURVEYDATE", "DATE")
    #arcpy.AddField_management(output_featureclass_path, "NOTES", "TEXT", "", "", 200)
    arcpy.AddField_management(output_featureclass_path, "AREA_ID", "LONG")
    arcpy.AddField_management(output_featureclass_path, "AREA_NAME", "TEXT", "", "", 255)
    arcpy.AddField_management(output_featureclass_path, "ADDATE", "DATE")



    calculate_fields(output_featureclass_path)



#Phase 2
def spatial_join_in_memory(target_feature_class, join_feature_class, output_name):
    in_memory_name = "in_memory/" + output_name
    return arcpy.SpatialJoin_analysis(target_feature_class, join_feature_class, in_memory_name)


def transfer_data_to_fields(joined_feature_class, target_field, transfer_field):
    expression = "!" + transfer_field + "!"
    arcpy.CalculateField_management(joined_feature_class, target_field, expression, "PYTHON_9.3")



def get_taxlot_and_emgaats_data(input_feature_class, output_path):

    taxlot_path = egh_public + r"\EGH_PUBLIC.ARCMAP_ADMIN.taxlots_pdx"
    emgaats_buildings_path = r"\\besfile1\GRP117\BFreeman\Connections\EMGAATS BESDBPROD1.sde\EMGAATS.GIS.Network\EMGAATS.GIS.Areas"

    fields_to_keep = return_list_of_fields_from_table(input_feature_class)

    joined_taxlots = spatial_join_in_memory(input_feature_class, taxlot_path, "joined_taxlots")
    transfer_data_to_fields(joined_taxlots, "RNO", "RNO_1")

    joined_buildings = spatial_join_in_memory(joined_taxlots, emgaats_buildings_path, "joined_buildings")
    transfer_data_to_fields(joined_buildings, "Area_ID", "area_id_1")
    transfer_data_to_fields(joined_buildings, "Area_NAME", "area_name_1")


    delete_all_fields_except_as_specified_and_geometry(joined_buildings, fields_to_keep)

    arcpy.CopyFeatures_management(joined_buildings, output_path)

#Todo: function to
def name_splitter(path):
    index = path.rfind("\\")
    return path[index + 1:]

def create_diff_layers(input_featureclass, output_path, name):
    expression_diff_1 = '("SURVEYFFE"- "first_floor_elev_ft" ) > 3'
    expression_diff_2 = '("SURVEYFFE"- "first_floor_elev_ft" ) < -3'

    diff_1 = arcpy.MakeFeatureLayer_management(input_featureclass, "diff_1", expression_diff_1)

    diff_2 = arcpy.MakeFeatureLayer_management(input_featureclass, "diff_2", expression_diff_2)



    fc_diff_1 = arcpy.CopyFeatures_management(diff_1, r"C:\temp\ffe_scratch\FFE_working.gdb\Surveyed_E10683_09202019_diff_1")
    fc_diff_2 = arcpy.CopyFeatures_management(diff_2, r"C:\temp\ffe_scratch\FFE_working.gdb\Surveyed_E10683_09202019_diff_2")

    add_text_field_to_feature_class(fc_diff_1, "Resurvey", 10)
    add_text_field_to_feature_class(fc_diff_2, "Resurvey", 10)

def join_spatial_joined_feature_class_with_emgaats_building(input_featureclass):
    emgaats_buildings_path = r"\\besfile1\GRP117\BFreeman\Connections\EMGAATS BESDBPROD1.sde\EMGAATS.GIS.Network\EMGAATS.GIS.Areas"
    temp_layer = arcpy.MakeFeatureLayer_management(input_featureclass, "temp_layer")
    return arcpy.AddJoin_management(temp_layer,"AREA_ID", emgaats_buildings_path, "area_id")