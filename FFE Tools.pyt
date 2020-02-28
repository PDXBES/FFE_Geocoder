import arcpy
import layer_creator
import xlrd

class Toolbox(object):
    def __init__(self):
        self.label = "FFE Tools.pyt"
        self.alias = "ffe"

        # List of tool classes associated with this toolbox
        self.tools = [GeocodeFFE]


class GeocodeFFE(object):
    def __init__(self):
        self.label = "Geocode FFE"
        self.description = "Tool to create geocoded Finished Floor Elevation (FFE) points from Excel Workbooks"


    def getParameterInfo(self):
        # Define parameter definitions

        # Input Excel Workbook parameter
        in_excel_workbook = arcpy.Parameter(
            displayName="Input Excel Workbook",
            name="in_excel",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")

        in_excel_workbook.filter.list = ['xls', 'xlsx']

        # Input Excel Worksheet parameter
        in_excel_worksheet = arcpy.Parameter(
            displayName="Work Sheet",
            name="work_sheet",
            datatype="String",
            parameterType="Optional",
            direction="Input")
        #default_list = ["Sheet1"]
        #in_excel_worksheet.filter.list = default_list

        # Output GDB path parameter
        out_gdb_path = arcpy.Parameter(
            displayName="Output Features",
            name="out_gdb_path",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        # Output featureclass name parameter
        out_featureclass_name = arcpy.Parameter(
            displayName="Featureclass Name",
            name="featureclass_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        out_featureclass_name.value = "Geocoded_FFE"



        parameters = [in_excel_workbook, in_excel_worksheet, out_gdb_path, out_featureclass_name]

        return parameters

    def isLicensed(self):  # optional
        return True

    # def updateParameters(self, parameters):  # optional
    #
    #     return


    def updateMessages(self, parameters):  # optional
        return



    def execute(self, parameters, messages):

        f = open(r"C:\Users\bfreeman\Desktop\test.txt", "a")
        f.write(" execute ")
        f.close()
        input_excel = parameters[0].valueAsText
        excel_sheet = parameters[1].valueAsText
        output_gdb = parameters[2].valueAsText
        feature_class_name = parameters[3].valueAsText

        output_featureclass_path = output_gdb + "/" + feature_class_name

        x_y_key_field_list = ["X_COORD", "Y_COORD", "TYPE", "Elevation"]
        address_key_field_list = ["Address", "Elevation", "Basement"]
        restricted_fields = ["SITEADDR"]
        output_gdb_in_memory = "in_memory"

        twe = layer_creator.get_sheet_names(parameters[0])
        f = open(r"C:\Users\bfreeman\Desktop\test.txt", "a")
        f.write("derp " + twe)
        f.close()
        # if parameters[1] is None:
        #     excel_sheet = layer_creator.get_sheet_names(parameters[0])[0]
        #     f = open(r"C:\Users\bfreeman\Desktop\test.txt", "a")
        #     f.write("derp " + excel_sheet)
        #     f.close()
        try:
            # f = open(r"C:\Users\bfreeman\Desktop\test.txt", "a")
            # f.write(" try execute ")
            # f.close()
            excel_fields_list = layer_creator.return_list_of_excel_fields_from_sheet(input_excel, excel_sheet)

            if layer_creator.search_list_of_fields_for_key_words(restricted_fields, excel_fields_list):
                arcpy.AddMessage("Excel file has restricted field names, remove or rename restricted fields")

            elif layer_creator.search_list_of_fields_for_key_words(x_y_key_field_list, excel_fields_list):

                ffe = layer_creator.create_ffe_points_layer(input_excel, excel_sheet, output_gdb_in_memory)
                arcpy.AddField_management(ffe, "Basement", "TEXT", "", "", 10)
                layer_creator.geocode_address_table_with_x_y_values(ffe, output_featureclass_path)
                layer_creator.find_nearest_taxlot_to_x_y_point(output_featureclass_path)

                layer_creator.add_nearest_site_address_to_x_y_points(output_featureclass_path)
                layer_creator.rename_field(output_featureclass_path, "SITEADDR", "Address")
                layer_creator.convert_type_code_to_y_or_no(output_featureclass_path)
                fields_to_keep = [u'OBJECTID', "Address", 'SHAPE@', u'Shape', 'Elevation', 'Basement', 'GeocodingNotes']
                layer_creator.delete_all_fields_except_as_specified_and_geometry(output_featureclass_path,
                                                                                 fields_to_keep)

            elif layer_creator.search_list_of_fields_for_key_words(address_key_field_list, excel_fields_list):
                layer_creator.create_ffe_from_excel_with_addresses(input_excel, excel_sheet, output_gdb,
                                                                   feature_class_name)
            else:
                arcpy.AddMessage("Excel file is not in correct format, please check that fields have correct names")
        except xlrd.XLRDError:
            arcpy.AddMessage("Excel sheet is not named 'Sheet1'")


