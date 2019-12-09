import arcpy
import sys
#
# in_table = arcpy.GetParameterAsText(0)
# in_join_field = arcpy.GetParameterAsText(1)
# join_table = arcpy.GetParameterAsText(2)
# out_join_field = arcpy.GetParameterAsText(3)
# join_fields = arcpy.GetParameterAsText(4)



# Define generator for join data
def joindataGen(joinTable,fieldList,sortField):
    with arcpy.da.SearchCursor(joinTable,fieldList,sql_clause=['DISTINCT',
                                                               'ORDER BY '+sortField]) as cursor:
        for row in cursor:
            yield row

# Function for progress reporting
def percentile(n,pct):
    return int(float(n)*float(pct)/100.0)

# Add join fields
def join(in_table, in_join_field, join_table, out_join_field, join_fields):

    fList = [f for f in arcpy.ListFields(join_table) if f.name in join_fields.split(';')]

    for i in range(len(fList)):
        name = fList[i].name
        type = fList[i].type
        if type in ['Integer','OID']:
            arcpy.AddField_management(in_table, name, field_type='LONG')
        elif type == 'String':
            arcpy.AddField_management(in_table, name, field_type='TEXT', field_length=fList[i].length)
        elif type == 'Double':
            arcpy.AddField_management(in_table, name, field_type='DOUBLE')
        elif type == 'Date':
            arcpy.AddField_management(in_table, name, field_type='DATE')
        else:

            print('\nUnknown field type: {0} for field: {1}'.format(type,name))

    # Write values to join fields

    # Create generator for values
    fieldList = [out_join_field] + join_fields.split(';')
    joinDataGen = joindataGen(join_table, fieldList, out_join_field)
    version = sys.version_info[0]
    if version == 2:
        joinTuple = joinDataGen.next()
    else:
        joinTuple = next(joinDataGen)
    #
    fieldList = [in_join_field] + join_fields.split(';')
    count = int(arcpy.GetCount_management(in_table).getOutput(0))
    breaks = [percentile(count,b) for b in range(10,100,10)]
    j = 0
    with arcpy.da.UpdateCursor(in_table, fieldList, sql_clause=(None, 'ORDER BY ' + in_join_field)) as cursor:
        for row in cursor:
            j += 1

            row = list(row)
            key = row[0]
            try:
                while joinTuple[0] < key:
                    if version == 2:
                        joinTuple = joinDataGen.next()
                    else:
                        joinTuple = next(joinDataGen)
                if key == joinTuple[0]:
                    for i in range(len(joinTuple))[1:]:
                        row[i] = joinTuple[i]
                    row = tuple(row)
                    cursor.updateRow(row)
            except StopIteration:

                break

