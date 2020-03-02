import arcpy
import create_map
import layer_creator
import xlrd


### this section is for user defined variables
#input_excel = r"C:\temp\ffe_scratch\surveys\Surveyed_E08659_TGA0102C.xls"
input_excel = r"\\besfile1\ASM_Projects\E10489_RichmondGrnSt\Survey\Xls\Surveyed_E10489_01112020.xlsx"
#input_excel = r"C:\temp\ffe_scratch\surveys\Surveyed_E08659_TGA0102A.xls"
excel_sheet = "Formatted"
#input_table = r"C:\temp\ffe_scratch\FFE_working.gdb\FFE_points_main"

def geocode_ffe(input_excel, excel_sheet, output_featureclass_path, output_gdb, feature_class_name):

    output_featureclass_path = output_gdb + "/" + feature_class_name

    x_y_key_field_list = ["X_COORD", "Y_COORD", "TYPE", "Elevation"]
    address_key_field_list = ["Address", "Elevation", "Basement"]
    restricted_fields = ["SITEADDR"]
    output_gdb_in_memory = "in_memory"

    try:
        excel_fields_list = layer_creator.return_list_of_excel_fields_from_sheet(input_excel, excel_sheet)

        if layer_creator.search_list_of_fields_for_key_words(restricted_fields, excel_fields_list):
            print("Excel file has restricted field names, remove or rename restricted fields")
        # Excel FIle is based on X/Y coords, no need to geocode
        elif layer_creator.search_list_of_fields_for_key_words(x_y_key_field_list, excel_fields_list):

            layer_creator.create_ffe_from_X_Y(input_excel, excel_sheet, output_featureclass_path, output_gdb, feature_class_name)

        elif layer_creator.search_list_of_fields_for_key_words(address_key_field_list, excel_fields_list):
            layer_creator.create_ffe_from_excel_with_addresses(input_excel, excel_sheet, output_gdb, feature_class_name)
        else:
            print("Excel file is not in correct format, please check that fields have correct names")
    except xlrd.XLRDError:
        print("Excel sheet is not named 'Sheet1'")




#ToDo: keep the original address even though geocoding is attempting to use a modified address



def phase_2(input_geocoded_feature_class, output_path):

    layer_creator.get_taxlot_and_emgaats_data(input_geocoded_feature_class, output_path)

#ToDo: possible new tool to compare ffe elevations

if __name__ == "__main__":

    ffe_main = "nonea"
    gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"
    fc_name = r"Surveyed_E10489_01112020"

   # geocode_ffe(input_excel, excel_sheet, ffe_main, gdb, fc_name)

    phase_2(r"C:\temp\ffe_scratch\FFE_working.gdb\Surveyed_E10489_01112020", r"C:\temp\ffe_scratch\FFE_working.gdb\Surveyed_E10489_01112020_joined")