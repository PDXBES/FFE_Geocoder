import arcpy

# enter where output should go
#output_mxd_path = r"C:\temp\ffe_scratch\output\Survey_Appender.mxd"

#mxd_template_path = r"C:\temp\ffe_scratch\Survey_Appender.mxd"

#ffe_map = arcpy.mapping.MapDocument(mxd_template_path)

#ffe_map.saveACopy(output_mxd_path)

def create_survey_appender_from_template(output_mxd_path):
    mxd_path = output_mxd_path +r"\Survey_Appender.mxd"

    mxd_template_path = r"C:\temp\ffe_scratch\Survey_Appender.mxd"

    ffe_map = arcpy.mapping.MapDocument(mxd_template_path)

    ffe_map.saveACopy(mxd_path)