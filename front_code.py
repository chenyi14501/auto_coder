# -*- coding: utf-8 -*-
'''
Author: your name
Date: 2021-03-10 14:39:41
LastEditTime: 2021-04-04 15:44:12
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /deou/Users/mac/Documents/code/python/other/front_code.py
'''

import api_code
import numpy as np
import pandas as pd
from translate import Translator
import csv
import re
import urllib
import json
import jieba
from functools import reduce


def build_index_page_code(table_name, cols, opt_set):
    code = "<!DOCTYPE html>\n"
    code += "<html>\n"
    code += "<head>\n"
    code += "<meta charset=\"UTF-8\">\n"
    code += "<title > Basic DataGrid - jQuery EasyUI Demo</title>\n"
    code += "<link rel=\"stylesheet\" type=\"text/css\" href=\"../../static/css/themes/default/easyui.css\">\n"
    code += "<link rel=\"stylesheet\" type=\"text/css\" href=\"../../static/css/themes/icon.css\">\n"
    code += "<link rel=\"stylesheet\" type=\"text/css\" href=\"../../static/js/demo/demo.css\">\n"
    code += "<script type=\"text/javascript\" src=\"../../static/js/jquery.min.js\"></script>\n"
    code += "<script type=\"text/javascript\" src=\"../../static/js/jquery.easyui.min.js\"></script>\n"
    code += "<script type=\"text/javascript\" src=\"../../static/js/locale/easyui-lang-zh_CN.js\"></script>\n"
    code += "<script type=\"text/javascript\" src=\"../../static/js/cy_common.js\"></script>\n"
    # js code
    code += "        <script type='text/javascript' >\n"
    code += "        var row_add_url = '/api/%s/add';\n" % (table_name)
    code += "        var row_remove_url = '/api/%s/remove';\n" % (table_name)
    code += "        var row_edit_url = '/api/%s/update';\n" % (table_name)
    ids_list = [col['name'] for col in cols]
    code += "        var search_ids = ['"+"','".join(ids_list)+"'];\n"
    code += "        var form_ids = ['"+"','".join(ids_list)+"'];\n\n"

    opt_col_list = [col for col in cols if col["dtype"] == "tinyint"]
    for col in opt_col_list:
        # opts = opt_set[col["name"]]
        if col["name"] in opt_set:
            opts = opt_set[col["name"]]
            opts_code = ""
            for opt in opts:
                opts_code += "\"%s\":\"%s\"," %(opt["val"], opt["name"])
            code += "        var %s_opts = {%s};\n"  %(col['name'],opts_code)
            code += "        function %s_formatter(val,row,index){ return %s_opts[val]} \n\n" %(col["name"], col["name"])

    code += "    </script>\n"

    # html grid code
    code += "    </script>\n"
    code += "       </head>\n"
    code += "<body>\n"

    code += "   <table id=\"datagrid\" class=\"easyui-datagrid\" title=\"列表管理\" style=\"width:1500px;height:800px;margin:0px\" rownumbers=\"true\" pagination=\"true\"\n"
    code += " data-options=\"striped:true,singleSelect:true,collapsible:true,url:'/api/%s/list',method:'get'\" toolbar=\"#tb\" >\n" %(table_name)
    code += "       <thead>\n"
    code += "           <tr>\n"

    # grid columns html code
    for col in cols:
        if col["dtype"] == "tinyint":
            code += "               <th field=\"%s\" formatter=\"%s_formatter\" width=\"120\">%s</th> \n"% (
            col['name'], col['name'], col['comment'])
        else:
            code += "               <th data-options=\"field:'%s',width:120\">%s</th>\n" % (
            col['name'], col['comment'])

    code += "           </tr>\n"
    code += "       </thead>\n"
    code += "   </table>\n"

    # search bar html code
    code += "   <div id=\"tb\">\n"
    count = 0
    for col in cols:
        count += 1
        code += "       <label style=\"width:80px;display: inline-block;margin-top:10px;margin-left:20px;\">%s:</label>\n" % (col["comment"])
        if col["dtype"] == "datetime":
            code += "<input id=\"%s\" type=\"text\" style=\"width:150px;margin-top:10px\" class=\"easyui-datebox\" >\n" %(col["name"])
        elif col["dtype"] == "tinyint":
            opt_list = opt_set[col["name"]]
            code += "       <select id=\"%s\" class=\"easyui-combobox\" style=\"width:150px;margin-top:10px;\">\n" % (col["name"])
            for opt in opt_list:
                code += "           <option value='%s'>%s</option>\n" %(opt["val"], opt["name"])
            code += "       </select>\n"
        else:
            code += "       <input id=\"%s\" style=\"width:150px;margin-top:10px;line-height:26px;border:1px solid #ccc\">\n" % (col["name"])
        if count%5==0:
            code += "           </br>\n"
    code += "   <a href=\"#\" class=\"easyui-linkbutton\" iconCls=\"icon-search\" plain=\"true\" onclick=\"doSearch()\">查询</a></br>\n"
    code += "   <a href=\"#\" class=\"easyui-linkbutton\" iconCls=\"icon-add\" plain=\"true\" onclick=\"add()\">添加</a>\n"
    code += "   <a href=\"#\" class=\"easyui-linkbutton\" iconCls=\"icon-edit\" plain=\"true\" onclick=\"update()\">修改</a>\n"
    code += "   <a href=\"#\" class=\"easyui-linkbutton\" iconCls=\"icon-remove\" plain=\"true\" onclick=\"remove()\">删除</a>\n"
    code += "   </div>\n"
    code += "   </div>\n"

    code += "   <div id=\"dd\" class =\"easyui-dialog\" title =\"My Dialog\" style=\"width:400px;height:500px;\"\n"
    code += "   	data-options =\"iconCls: 'icon-save', resizable: true, modal: true, closed: true\">\n"
    code += " <div style =\"padding: 10px 60px 20px 60px\">\n"
    code += " <form id =\"ff\" method =\"post\">\n"
    code += " <table cellpadding =\"5\">\n"

    # form options html code
    # for col in cols:
    #     code += "			<tr>\n"
    #     code += "				<td>%s:</td>\n" % (col["comment"])
    #     code += "				<td><input class=\"easyui-textbox\" type=\"text\" id=\"form_%s\" data-options=\"required:true\"></input></td>\n" % (
    #         col["comment"])
    #     code += "			</tr>\n"

    for col in cols:
        code += "			<tr>\n"
        code += "				<td>%s:</td>\n" % (col["comment"])
        if col["dtype"] == "datetime":
            code += "				<td><input class=\"easyui-datebox\" type=\"text\" id=\"form_%s\" ></input></td>\n" % (
            col["name"])
        elif col["dtype"] == "tinyint":
            opt_list = opt_set[col["name"]]
            code += "       <td><select id=\"form_%s\" class=\"easyui-combobox\" style=\"width:150px;\">\n" % (col["name"])
            for opt in opt_list:
                code += "           <option value='%s'>%s</option>" %(opt["val"], opt["name"])
            code += "       </select></td>\n"
        else:
            code += "				<td><input class=\"easyui-textbox\" type=\"text\" id=\"form_%s\" ></input></td>\n" % (
            col["name"])
        code += "			</tr>\n"

    # other html code
    code += "   			</table>\n"
    code += "   		</form>\n"

    code += "   		<div style=\"text-align:center;padding:5px\">\n"
    code += "   			<a href=\"javascript:void(0)\" class=\"easyui-linkbutton\" style=\"margin-right:30px\" onclick=\"submit_form()\">保存</a>\n"
    code += "   			<a href=\"javascript:void(0)\" class=\"easyui-linkbutton\" onclick=\"clear_form()\">清空</a>\n"
    code += "   		</div>\n"
    code += "   		</div>\n"
    code += "   </div>\n"
    code += "       </div>\n"
    code += "   </body>\n"
    code += "   </html>\n"

    return code


def get_opt_set(opt_json_file):
    pro_opt_set = json.load(open(opt_json_file, "rb"))
    res_opt_set = {}
    for table_name, obj in pro_opt_set.items():
        table_opt = {}
        for col, opt_text in obj.items():
            opt_split_list = opt_text.replace(" ","").split(",")
            
            opt_list = []
            for opt in opt_split_list:
                val, name = opt.split(":")
                opt_list.append({"val":val, "name":name})
            table_opt[col] = opt_list
        res_opt_set[table_name] = table_opt
    print(res_opt_set)
    return res_opt_set


def build_code_files(map_csv_file, code_file_dir, opt_dict_json_file):
    tables = api_code.get_db_info(map_csv_file)
    opt_set = get_opt_set(opt_dict_json_file)
    for table_name, cols in tables.items():
        code = build_index_page_code(table_name, cols, opt_set[table_name])
        with open("%s/%s_index.html" % (code_file_dir, table_name), 'w+') as fp:
            fp.write(code)
            fp.close()
        print("build %s success !" % (table_name))



app_dir = "/Users/mac/Documents/code/python/other/builder"
def run(map_csv_file, opt_dict_json_file):
    #map_csv_file = app_dir +"/csv/" + map_csv_file
    #opt_dict_json_file = app_dir +"/csv/" + opt_dict_json_file
    html = app_dir + "/html"
    build_code_files(map_csv_file, html, opt_dict_json_file)

def _run(project_dir):
    map_csv_file = app_dir +"/csv/" + map_csv_file
    opt_dict_json_file = app_dir +"/csv/" + opt_dict_json_file
    html = app_dir + "/html"


# run("deou_map.csv", "shu_dict.json")
# tables = api_code.get_db_info("/Users/mac/Documents/code/python/other/builder/csv/deou_map.csv")
# print(tables)

# build_code_files( app_dir+"/csv/deou_map.csv", app_dir + "/html", app_dir+"/csv/shu_dict.json")

# res_opts = get_opt_set(app_dir+"/csv/shu_dict.json")
# print(res_opts)


