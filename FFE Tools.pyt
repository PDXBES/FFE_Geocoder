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
            excel_fields_list = layer_creator.return_list_of_excel_fields_from_sheet(input_excel, excel_sheet)

            if layer_creator.search_list_of_fields_for_key_words(restricted_fields, excel_fields_list):
                print("Excel file has restricted field names, remove or rename restricted fields")
            # Excel FIle is based on X/Y coords, no need to geocode
            elif layer_creator.search_list_of_fields_for_key_words(x_y_key_field_list, excel_fields_list):

                layer_creator.create_ffe_from_X_Y(input_excel, excel_sheet, output_featureclass_path, output_gdb,
                                                  feature_class_name)

            elif layer_creator.search_list_of_fields_for_key_words(address_key_field_list, excel_fields_list):
                layer_creator.create_ffe_from_excel_with_addresses(input_excel, excel_sheet, output_gdb,
                                                                   feature_class_name)
            else:
                print("Excel file is not in correct format, please check that fields have correct names")
        except xlrd.XLRDError:
            print("Excel sheet is not named 'Sheet1'")


