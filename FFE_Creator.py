import arcpy
import create_map
import layer_creator

### this section is for user defined variables

input_excel = r"C:\temp\ffe_scratch\surveys\Surveyed_E10345_RoseCity.xls"
excel_sheet = "Sheet1"



output_gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"


ffe_main = output_gdb + "/FFE_points_main"
ffe_taxlots = output_gdb + "/FFE_points_taxlots"

output_mxd_path = r"C:\temp\ffe_scratch\output"
ffe_points = output_gdb + "/FFE_points"
ffe_template_path = r"C:\temp\ffe_scratch\FFE_working.gdb\ffe_template"

#TODO: transistion to in-memory workspace for all temporary files

if not arcpy.Exists(output_gdb):
    arcpy.CreateFileGDB_management(r"C:\temp\ffe_scratch", "FFE_working.gdb")

feature_classes_to_append = []


# Create a table from the input ffe excel spread sheet
new_table = layer_creator.create_ffe_points_layer(input_excel, excel_sheet, output_gdb)

# Create an empty feature class from a template
feature_class_name = layer_creator.create_point_feature_class_with_template("FFE_points_main", output_gdb, ffe_template_path)
additional_fc = layer_creator.create_point_feature_class_with_template("FFE_points_taxlots", output_gdb, ffe_template_path)
#geo_locater_fc = layer_creator.create_point_feature_class_with_template("FFE_points_locator", output_gdb, ffe_template_path)

# Geocode the ffe points using a first pass from master address points and a second pass from the address locator
unmatched_address_list = layer_creator.geocode_ffe_points_with_master_address_points(new_table, feature_class_name)


if len(unmatched_address_list) > 0:

    unmatched_address_table = layer_creator.create_table_from_list(unmatched_address_list, output_gdb, "unmatched_ffe")


    #  ffe points using the taxlot addresses

    unmatched_address_list_2 = layer_creator.geocode_ffe_points_with_taxlots(unmatched_address_table, additional_fc)
    feature_classes_to_append.append(ffe_taxlots)
    if len(unmatched_address_list_2) > 0:
        filtered_list = layer_creator.remove_address_ranges_from_list_of_addresses(unmatched_address_list_2)
        unmatched_address_table_2 = layer_creator.create_table_from_list(filtered_list, output_gdb, "unmatched_ffe_2")


        ###Go over the uncoded points using the adddress locator
        geo_locater_fc_path = output_gdb + "/geocoded_ffe"

        layer_creator.add_text_field_to_feature_class(unmatched_address_table_2, "conditioned_address", 100)


        layer_creator.update_field_with_conditioned_address(unmatched_address_table_2, "Address", "conditioned_address")

        layer_creator.geocode_ffe_points_with_address_locator(unmatched_address_table_2, geo_locater_fc_path)



        feature_classes_to_append.append(geo_locater_fc_path)

    #combine all three geocoded_feature_classes
if len(feature_classes_to_append) > 0:
    layer_creator.append_tables_to_single_featureclass(ffe_main, feature_classes_to_append)

### Create the Map ##
#pass the path only, the name is added in the function
#create_map.create_survey_appender_from_template(output_mxd_path)