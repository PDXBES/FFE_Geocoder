import arcpy
import create_map
import layer_creator
import xlrd


### this section is for user defined variables
#input_excel = r"C:\temp\ffe_scratch\surveys\Surveyed_E08659_TGA0102C.xls"
input_excel = r"\\besfile1\ASM_Projects\E10683_GooseHollow\Research\Survey\Excel\Suveyed_E10683_092019.xlsx"
#input_excel = r"C:\temp\ffe_scratch\surveys\Surveyed_E08659_TGA0102A.xls"
excel_sheet = "Sheet1"
#input_table = r"C:\temp\ffe_scratch\FFE_working.gdb\FFE_points_main"

def geocode_ffe(input_excel, excel_sheet, output_featureclass_path, output_gdb, feature_class_name):

    output_featureclass_path = output_gdb + "/" + feature_class_name

    x_y_key_field_list = ["X_COORD", "Y_COORD", "TYPE", "Elevation"]
    address_key_field_list = ["Address", "Elevation", "Basement", "Notes"]
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

    #layer_creator.get_taxlot_and_emgaats_data(input_geocoded_feature_class, output_path)
    joined_layer = layer_creator.join_spatial_joined_feature_class_with_emgaats_building(output_path)
    layer_creator.create_diff_layers(joined_layer)

#ToDo: possible new tool to compare ffe elevations


def name_splitter(path):
    index = path.rfind("\\")
    return path[index + 1:]


if __name__ == "__main__":

    ffe_main = "nonea"
    gdb = r"C:\temp\ffe_scratch\FFE_working.gdb"
    fc_name = r"Stet"

    #geocode_ffe(input_excel, excel_sheet, ffe_main, gdb, fc_name)

    #phase_2(r"C:\temp\ffe_scratch\FFE_working.gdb\Surveyed_E10683_09202019_init", r"C:\temp\ffe_scratch\FFE_working.gdb\Surveyed_E10683_092019_joined")

    print(name_splitter(gdb))

    #test to see if vcs works well 2

    #testing GitHub Desktop Client