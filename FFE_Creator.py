import arcpy
import create_map
import layer_creator

### this section is for user defined variables

input_excel = r"C:\temp\ffe_scratch\surveys\2019-03-29 E10216 Stark HSS-17 MERGE Original Request FFE JMF.xlsx"
excel_sheet = "Sheet1"
output_gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"
output_mxd_path = r"C:\temp\ffe_scratch\output"
ffe_points = output_gdb + "/FFE_points"

#using output_gdb now, will transition to in memory

if not arcpy.Exists(output_gdb):
    arcpy.CreateFileGDB_management(r"C:\temp\ffe_scratch", "FFE_working.gdb")


### Create the Map ##
#pass the path only, the name is added in the function
#create_map.create_survey_appender_from_template(output_mxd_path)

### Create the layer from the input ffe excel spread sheet
new_table = layer_creator.create_ffe_points_layer(input_excel, excel_sheet, output_gdb)


feature_class_name = layer_creator.create_point_feature_class_with_template("FFE_points1")

### Geocode the ffe points using a first pass from master address points and a second pass from the address locator
unmatched_addresses = layer_creator.geocode_ffe_points_with_master_address_points(new_table, feature_class_name)


### Geocode the ffe points using the taxlot addresses
#unmatched_addresses = layer_creator.geocode_ffe_points_with_taxlots(new_table)

###Go over the uncoded points using the adddress locator
#layer_creator.geocode_ffe_points_with_address_locator(unmatched_addresses)