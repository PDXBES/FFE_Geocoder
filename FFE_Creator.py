import arcpy
import create_map
import layer_creator
import xlrd


### this section is for user defined variables
#input_excel = r"C:\temp\ffe_scratch\surveys\Surveyed_E08659_TGA0102C.xls"
input_excel = r"C:\temp\ffe_scratch\surveys\2019-03-29 E10216 Stark HSS-17 MERGE Original Request FFE JMF.xlsx"
excel_sheet = "Sheet1"
input_table = r"C:\temp\ffe_scratch\FFE_working.gdb\FFE_points_main"


def create_ffe_from_excel_with_addresses(excel_workbook, excel_sheet, output_gdb, feature_class_name):
#application variables
    #output_gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"
    output_gdb_in_memory = "in_memory"
    ffe_main = r"C:\temp\ffe_scratch\FFE_working.gdb\FFE_points_main"
    ffe_taxlots = output_gdb_in_memory + r"/FFE_points_taxlots"

    output_mxd_path = r"C:\temp\ffe_scratch\output"
    ffe_points = output_gdb_in_memory + r"\FFE_points"
    ffe_template_path = r"C:\temp\ffe_scratch\FFE_working.gdb\ffe_template"

    output_featureclass_path = output_gdb + "/" + feature_class_name

    #TODO: transistion to in-memory workspace for all temporary files

    #if not arcpy.Exists(output_gdb):
     #   arcpy.CreateFileGDB_management(r"C:\temp\ffe_scratch", "FFE_working.gdb")

    feature_classes_to_append = []

    # Create a table from the input ffe excel spread sheet
    new_table = layer_creator.create_ffe_points_layer(excel_workbook, excel_sheet, output_gdb_in_memory)

    # Create empty feature classes from  template
    feature_class_name = layer_creator.create_point_feature_class_with_template(feature_class_name, r"C:\temp\ffe_scratch\FFE_working.gdb", ffe_template_path)
    additional_fc = layer_creator.create_point_feature_class_with_template("FFE_points_taxlots", output_gdb_in_memory, ffe_template_path)

    # Geocode the ffe points using a first pass from master address points and a second pass from the address locator
    unmatched_address_list = layer_creator.geocode_ffe_points_with_master_address_points(new_table, feature_class_name)

    if len(unmatched_address_list) > 0:

        unmatched_address_table = layer_creator.create_table_from_list(unmatched_address_list, output_gdb_in_memory, "unmatched_ffe")

        #  ffe points using the taxlot addresses

        unmatched_address_list_2 = layer_creator.geocode_ffe_points_with_taxlots(unmatched_address_table, additional_fc)
        feature_classes_to_append.append(ffe_taxlots)
        if len(unmatched_address_list_2) > 0:
            filtered_list = layer_creator.remove_address_ranges_from_list_of_addresses(unmatched_address_list_2)
            unmatched_address_table_2 = layer_creator.create_table_from_list(filtered_list, output_gdb_in_memory, "unmatched_ffe_2")


            ###Go over the uncoded points using the adddress locator
            geo_locater_fc_path = output_gdb_in_memory + "/geocoded_ffe"

            layer_creator.add_text_field_to_feature_class(unmatched_address_table_2, "conditioned_address", 100)


            layer_creator.update_field_with_conditioned_address(unmatched_address_table_2, "Address", "conditioned_address")

            layer_creator.geocode_ffe_points_with_address_locator(unmatched_address_table_2, geo_locater_fc_path)



            feature_classes_to_append.append(geo_locater_fc_path)

        #combine all three geocoded_feature_classes
    if len(feature_classes_to_append) > 0:
        layer_creator.append_tables_to_single_featureclass(output_featureclass_path, feature_classes_to_append)



#here we are running the application:

### Create the Map ##
#pass the path only, the name is added in the function
#create_map.create_survey_appender_from_template(output_mxd_path)

### Create the FFE with addressses
#create_ffe_from_excel_with_addresses(input_excel, excel_sheet)

### Create FFE with X Y
#output_gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"

#ffe_main = output_gdb + "/FFE_points_main"

#ffe = layer_creator.create_ffe_points_layer(r"C:\temp\ffe_scratch\surveys\Surveyed_E08659_TGA0102E.xls", "Sheet2", output_gdb)
#layer_creator.geocode_address_table_with_x_y_values(ffe, ffe_main)

#comprehensive tool

def geocode_ffe(input_excel, excel_sheet, output_featureclass_path, output_gdb, feature_class_name):

    x_y_key_field_list = ["X_COORD", "Y_COORD", "TYPE", "Elevation"]
    address_key_field_list = ["Address", "Elevation", "Basement"]
    restricted_fields = ["SITEADDR"]
    #output_gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"
    output_gdb_in_memory = "in_memory"

    #ffe_main = output_gdb + "/FFE_points_main"

    try:
        excel_fields_list = layer_creator.return_list_of_excel_fields_from_sheet(input_excel, excel_sheet)

        if layer_creator.search_list_of_fields_for_key_words(restricted_fields, excel_fields_list):
            print("Excel file has restricted field names, remove or rename restricted fields")

        elif layer_creator.search_list_of_fields_for_key_words(x_y_key_field_list, excel_fields_list):

            ffe = layer_creator.create_ffe_points_layer(input_excel, excel_sheet, output_gdb_in_memory)
            arcpy.AddField_management(ffe, "Basement", "TEXT", "", "", 10)
            layer_creator.geocode_address_table_with_x_y_values(ffe, output_featureclass_path)
            layer_creator.find_nearest_taxlot_to_x_y_point(output_featureclass_path)

            layer_creator.add_nearest_site_address_to_x_y_points(output_featureclass_path)
            layer_creator.rename_field(output_featureclass_path, "SITEADDR", "Address")
            layer_creator.convert_type_code_to_y_or_no(output_featureclass_path)
            fields_to_keep = [u'OBJECTID', "Address", 'SHAPE@', u'Shape', 'Elevation', 'Basement', 'GeocodingNotes']
            layer_creator.delete_all_fields_except_as_specified_and_geometry(output_featureclass_path, fields_to_keep)

        elif layer_creator.search_list_of_fields_for_key_words(address_key_field_list, excel_fields_list):
            create_ffe_from_excel_with_addresses(input_excel, excel_sheet, output_gdb, feature_class_name)
        else:
            print("Excel file is not in correct format, please check that fields have correct names")
    except xlrd.XLRDError:
        print("Excel sheet is not named 'Sheet1'")



ffe_main = r"C:\temp\ffe_scratch\FFE_working.gdb\FFE_points_main"
gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"
fc_name = r"\FFE_points_main"
geocode_ffe(input_excel, excel_sheet, ffe_main, gdb, fc_name)
#layer_creator.add_nearest_site_address_to_x_y_points(input_table)
#layer_creator.rename_field(input_table, "SITEADDR", "Address")
#fields_to_keep = [u'OBJECTID', "Address", 'SHAPE@', u'Shape', 'Elevation', 'Basement', 'GeocodingNotes']
#layer_creator.delete_all_fields_except_as_specified_and_geometry(input_table, fields_to_keep)