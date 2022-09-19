type = ['1','2','3']
length = len(type)
"1" in type
filters = ""

if "1" in type:
    if filters == "":
        filters += "type_id = 1"
    else:
        filters += ",type_id = 1"
if "2" in type:
    if filters == "":
        filters += "type_id = 2"
    else:
        filters += ",type_id = 2"
if "3" in type:
    if filters == "":
        filters += "type_id = 3"
    else:
        filters += ",type_id = 3"
if "4" in type:
    if filters == "":
        filters += "type_id = 4"
    else:
        filters += ",type_id = 4"    
if "5" in type:
    if filters == "":
        filters += "type_id = 5"
    else:
        filters += ",type_id = 5"

print(filters)          
