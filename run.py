'''
Author: your name
Date: 2021-03-10 20:17:22
LastEditTime: 2021-04-05 00:00:24
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /builder/run.py
'''
import front_code, api_code,  sql_code
import sys, os
import pro.pro_map as pro_map



builder_base_dir = "/Users/mac/Documents/code/python/other/builder/"
builder_csv_dir = builder_base_dir +"csv/"

pro_dtype_dict_csv  = builder_csv_dir + "dtype.csv"

# @click.command()
# @click.option("--dir", default=None, help="source dir")
# @click.option("--pro", default=None, help="source dir")
# @click.option("--all", default=None, help="source dir")
# @click.option("--map", default=None, help="destination dir")
# @click.option("--sql", default=None, help="destination dir")
# @click.option("--api", default=None, help="destination dir")
# @click.option("--page", default=None, help="destination dir")
# def build(_dir, _pro, _all, _map, _sql, _api, _page):
#     out_dir, pro_csv, pro_map_csv = None, None, None
#     if _dir == None:
#         _dir = "./"
#     out_dir = _dir

#     if _all != None:
#         pro_csv = _all
#         _map, sql, api, page = pro_csv, pro_csv, pro_csv, pro_csv

#     if _map != None:
        



    

if __name__ == "__main__":
    # execute only if run as a script
    pro_name = sys.argv[1]

    pro_csv_file = ("%s%s/%s.csv") % (builder_csv_dir,pro_name, pro_name)
    
    pro_map_csv_file = ("%s_map.csv") % (pro_name)
    pro_map_csv_file_path =  ("%s%s/%s") % (builder_csv_dir,pro_name, pro_map_csv_file)

    pro_sql_file = ("%s.sql") % (pro_name)
    pro_dict_json_file = ("%s%s/%s_dict.json") % (builder_csv_dir,pro_name, pro_name)


    pro_api_code_dir = ("%s%s/routes") % (builder_csv_dir,pro_name)
    pro_front_code_dir = ("%s%s/html") % (builder_csv_dir,pro_name)

    model_file_path = ("%s%s/models.py") % (builder_csv_dir,pro_name)
    
    code = sys.argv[2]
    if code == "map":
        pro_map.build_pro_map(pro_csv_file, pro_map_csv_file, pro_dtype_dict_csv)
    
    elif code == "sql":
        sql_str = sql_code.build_sql(pro_map_csv_file_path)
        with open(pro_sql_file, "w") as fp :
            fp.write(sql_str)
            fp.close()
        cmd = "mysql -u $USER -p$PASS um < %s"
        
    

    elif code == "api":
        tables = api_code.get_db_info(pro_map_csv_file_path)
        api_code.build_flask_routes(tables, pro_api_code_dir)
    
    elif code == 'model':
        cmd = "cy_sqlachemycode %s %s" %(pro_name, model_file_path)
        os.system(cmd)

        cmd = "gsed -i -e '5i from .. import db' -e 's/(Base)/(db.Model)/g' %s" %(model_file_path)
        os.system(cmd)

    elif code == "page":
        tables = api_code.get_db_info(pro_map_csv_file_path)
        front_code.build_code_files(pro_map_csv_file_path, pro_front_code_dir, pro_dict_json_file)
    else:
        print("error action command !")
    
    # else code == "api":
    #     api_code.build(pro_csv_map_file, pro_api_dir)
    
    # else code == "page":
    #     front_code.build(pro_csv_map_file, pro_page_dir)
    
        
    