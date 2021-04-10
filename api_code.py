# -*- coding: utf-8 -*-
'''
Author: your name
Date: 2021-02-10 18:57:28
LastEditTime: 2021-04-04 16:08:55
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /other/hello.py
'''
import numpy as np
import pandas as pd
from translate import Translator
import csv
import re, urllib,json
import jieba
from functools import reduce
pd.set_option('display.width', 2000)
pd.set_option('display.max_columns', None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',100)



word = lambda s, c :s.replace(c, " ").title().replace(" ","")
def youdao_trans(content):
    # 翻译地址
    request_url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule'
    # data参数
    data = {'i': content,
            'from': 'AUTO',
            'to': 'AUTO',
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'salt': '15944508027607',
            'sign': '598c09b218f668874be4524f19e0be37',
            'ts': '1594450802760',
            'bv': '02a6ad4308a3443b3732d855273259bf',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_REALTlME',
            }
    # headers参数
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    # 将data规范化
    data = urllib.parse.urlencode(data)
    # 转为字节型
    data = bytes(data, 'utf-8')
    # 创建请求
    request = urllib.request.Request(request_url, data, headers=headers)
    # 发送请求并获取相应
    response = urllib.request.urlopen(request)
    # 返回内容,得到一个json字符串
    try:
        html = response.read().decode('utf-8')
        # 将json字符串转为字典
        html = json.loads(html)
        #print('翻译结果：', html['translateResult'][0][0]['tgt'])
        return html['translateResult'][0][0]['tgt']
    except:
        return ""
    # html = response.read().decode('utf-8')
    # # 将json字符串转为字典
    # html = json.loads(html)
    # print(html)
    # #print('翻译结果：', html['translateResult'][0][0]['tgt'])
    # return html['translateResult'][0][0]['tgt']

def handle_from_csv(cvs_file, map_csv_file, dtype_cvs_file):
    table = []
    with open(cvs_file, 'r') as f:
        rows = csv.reader(f)
        for row in rows:
            table.append([row[0].replace("表",""), "table", "str", row[0], row[0], row[0], "-","",""])
            for e in [r for r in row[1:] if r != ""]:
                    table.append([e, "col", "str", e, e, row[0], "-","",""])
    
    df= pd.DataFrame(table, columns=["name", "type", "dtype", "comment", "sub_words", "table", "rel_table","en", "reled_cols"])  
    df["sub_words"] = df["name"].map(lambda s :",".join(jieba.lcut(s,cut_all=True)))
    
    def rel_table(row):
        res = [t for t in df[df.type=="table"]["table"] if str(t).replace("表","") in row["sub_words"] and t != row["table"]]
        if len(res) > 0: return res[0]
        return ""
    df["rel_table"] = df.apply(rel_table , axis=1)

    def reled_cols(row):
        res = [t for t in df[df.type=="table"]["table"] if str(t).replace("表","") in row["sub_words"] and t != row["table"]]
        if len(res) > 0: return res[0]
        return ""
    trans = lambda s : youdao_trans(s).lower().replace(" ","_").replace("-", "_")
    trans_fix = lambda s : reduce(lambda x,y : x.replace(y,""), [trans(s),"the_","_of",".","_to"])
    def trans_table(row):
        en_name = trans_fix(row["name"])
        if row["type"] == "col" and row["rel_table"].strip() != "":
            rel_table_en =  trans_fix(row["rel_table"].replace("表","").strip())
            if rel_table_en not in en_name:
                en_name = rel_table_en + "_" + en_name
        return en_name
    df["en"] = df.apply(trans_table, axis=1)

    dtype_map = {}
    with open(dtype_cvs_file, 'r') as f:
        rows = csv.reader(f)
        for row in rows:
            dtype_map[row[0]] = row[1:]

    def set_dtype(row):
        res = [ key for key, val in dtype_map.items() if len([v for v in val if v in row["name"] and v != ""]) > 0]
        if len(res) > 0 : return res[0]
        return "varchar(32)"
    df["dtype"] = df.apply(set_dtype, axis=1)
    
    df.to_csv(map_csv_file, index=False)
    print(df)

    sql_str = ""
    for i, t in df[df.type == "table"].iterrows():
        print("-->"+t["name"])
        sql_str += "\ndrop table if exists `%s`;\n" %(t["en"])
        sql_str += "CREATE TABLE `%s` (\n" %(t["en"]) 
        sql_str += "    `id` int NOT NULL AUTO_INCREMENT COMMENT 'primary key',\n"
        
        for j, col in df[(df.type=="col")  & (df.table==t["comment"])].iterrows():
            sql_str += "    `%s` %s COMMENT '%s',\n" %(col["en"], col["dtype"], col["comment"])
        sql_str += "    `deleted` tinyint DEFAULT 0 COMMENT '是否已删',\n"
        sql_str += "    `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'created time',\n"
        sql_str += "    `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'updated time',\n" 
        sql_str += "    PRIMARY KEY (`id`) \n"
        sql_str += ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='%s'\n\n" % (t["table"])
    
    print(sql_str)

def build_sql(df_csv_file):
    df = pd.read_csv(df_csv_file)

    sql_str = ""
    for i, t in df[df.type == "table"].iterrows():
        print("-->"+t["name"])
        sql_str += "\ndrop table if exists `%s`;\n" %(t["en"])
        sql_str += "CREATE TABLE `%s` (\n" %(t["en"]) 
        sql_str += "    `id` int NOT NULL AUTO_INCREMENT COMMENT 'primary key',\n"
        
        for j, col in df[(df.type=="col")  & (df.table==t["comment"])].iterrows():
            sql_str += "    `%s` %s COMMENT '%s',\n" %(col["en"], col["dtype"], col["comment"])
        sql_str += "    `deleted` tinyint DEFAULT 0 COMMENT 'delete',\n"
        sql_str += "    `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'created time',\n"
        sql_str += "    `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'updated time',\n" 
        sql_str += "    PRIMARY KEY (`id`) \n"
        sql_str += ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='%s' ;\n\n" % (t["table"])
    
    print(sql_str)

def get_db_info(csv_file_path):
    df = pd.read_csv(csv_file_path)
    tables = {}
    for i, t in df[df.type == "table"].iterrows():
        cols = []
        cols.append({"name":"id", "dtype":"int", "comment":"ID"})
        for j, col in df[(df.type=="col")  & (df.table==t["comment"])].iterrows():
            cols.append({"name":col["en"], "dtype":col["dtype"], "comment": col["comment"]})
        tables[t["en"]] = cols
    return tables


def build_obj_set_value_code(table_name, cols):
    code = ""    

    for col in cols:
        if col['name'] == 'id':
            continue
        if col['dtype'] in  ["int", "tinyint"]:
            code +="    %s = request.json.get('%s', None)\n" %(col['name'], col['name'])
            code +="    if %s != None:\n" %(col['name'])
        else:
            code +="    %s = request.json.get('%s', None)\n" %(col['name'], col['name'])
            code +="    if %s != None and %s.strip()!='':\n" %(col['name'], col['name'])
        code +="        %s.%s = %s\n\n" %(table_name, col['name'], col['name'])
    return code


def build_check_obj_exist_code(table_name, cols):
    code = ""
    code +="    id = request.json.get('id', None)\n"
    code +="    if id == None:\n"
    code +="        return jsonify({'error':1, 'msg':'ID无效', 'data':''})\n\n"

    code +="    %s = %s.query.get(int(id))\n" %(table_name, word(table_name, '_'))
    code +="    if %s == None:\n" %(table_name)
    code +="        return jsonify({'error':1, 'msg':'ID 不存在', 'data':''})\n\n"
    return code

def build_flask_api_list(table_name, cols):
    code = "@base.route('/api/%s/list', methods=['GET'])\n" %(table_name)
    code += "def api_%s_list():\n" %(table_name)
    code += "    page = request.args.get('page', 1, type=int)\n"\
            "    rows = request.args.get('rows', 10, type=int)\n\n"

    # list for the args, note: datetime type has end_time, start_time
    code_cols = []
    for col in cols:
        code_col = {'name':col['name'],'_name':col['name'], 'dtype':col["dtype"], '_dtype':'str', '_cmp':'=='}
        if col["dtype"] in ["int", "tinyint"]:
            code_col['_dtype'] = "int"
            code_cols.append(code_col)
        elif col["dtype"] in ["datetime"]:
            code_col = {'name':col['name'],'_name':col['name'], 'dtype':col["dtype"], '_dtype':'str', '_cmp':'=='}
            code_cols.append(code_col)
            start_code_col = {'name':col['name'],'_name':'start_'+col['name'], 'dtype':col["dtype"], '_dtype':'str', '_cmp':'>='}
            code_cols.append(start_code_col)
            end_code_col = {'name':col['name'],'_name':'end_'+col['name'], 'dtype':col["dtype"], '_dtype':'str', '_cmp':'<='}
            code_cols.append(end_code_col)
        else:
            code_cols.append(code_col)
    print(code_cols)
    # code for get the args with default data
    for code_col in code_cols:
        code += "    %s = request.args.get('%s', None, type=%s)\n" %(code_col["_name"], code_col["_name"], code_col["_dtype"])
    
    # code for the sqlachmy filter , column option compare
    table_orm_name = table_name.replace("_", " ").title().replace(" ","")
    code += "\n\n"
    code += "    filters = [%s.deleted == 0]\n\n" %(table_orm_name)
    
    for code_col in code_cols:
        if code_col['_dtype'] == 'str':
            code += "    if %s != None and %s != \'\':\n" %(code_col["_name"], code_col['_name'])
        elif code_col['dtype'] == 'tinyint':
            code += "    if %s != None and %s != 0:\n" %(code_col["_name"], code_col["_name"])
        else:
            code += "    if %s != None:\n" %(code_col["_name"])
        code += "        filters.append(%s.%s %s %s)\n\n" %(table_orm_name, code_col["name"], code_col['_cmp'], code_col["_name"])
    
    code += "\n    total = %s.query.filter(*filters).count()\n" %(table_orm_name)
    code += "    pagination = %s.query.filter(*filters).paginate(page, rows, False)\n" %(table_orm_name)
    code +="    rows = [ %s for %s in pagination.items]\n" %(table_name, table_name)
    code += "    return jsonify({'total':total, 'rows':util_models.to_json(rows)})"
    return code

def build_flask_api_add(table_name, cols):
    code = "@base.route('/api/%s/add', methods=['POST'])\n" %(table_name)
    code += "def api_%s_add():\n" %(table_name)

    code += "    %s = %s()\n" %(table_name, word(table_name, "_"))
    code += build_obj_set_value_code(table_name, cols)
    code += "\n    db.session.add(%s)\n" %(table_name)
    code += "    db.session.commit()\n"
    code += "    return jsonify({'error':0, 'msg':'update success', 'data':''})\n\n"
    return code


def build_flask_api_update(table_name, cols):
    code = "@base.route('/api/%s/update', methods=['POST'])\n" %(table_name)
    code += "def api_%s_update():\n" %(table_name)

    code += build_check_obj_exist_code(table_name, cols)
    code += build_obj_set_value_code(table_name, cols)
    
    code +="\n    db.session.add(%s)\n" %(table_name)
    code += "    db.session.commit()\n"
    code +="    return jsonify({'error':0, 'msg':'update success', 'data':''})\n\n"
    return code

def build_flask_api_del(table_name, cols):
    code = "@base.route('/api/%s/remove', methods=['POST'])\n" %(table_name)
    code += "def api_%s_del():\n" %(table_name)

    code += build_check_obj_exist_code(table_name, cols)
    code +="\n    %s.deleted = 1\n" %(table_name)
    
    code +="\n    db.session.add(%s)\n" %(table_name)
    code +="    return jsonify({'error':0, 'msg':'update success', 'data':''})\n\n"
    return code

def build_flask_api_info(table_name, cols):
    code = "@base.route('/api/%s/info', methods=['GET'])\n" %(table_name)
    code += "def api_%s_info():\n" %(table_name)
    code += build_check_obj_exist_code(table_name, cols)
    code +="    return jsonify({'error':0, 'msg':'', 'data':%s.to_json()})\n\n" %(table_name)
    return code

def build_flask_routes(tables, code_file_dir):
    apis = [buidl_flask_page_code,
            build_flask_api_list,
            build_flask_api_add,
            build_flask_api_update,
            build_flask_api_info,
            build_flask_api_del]
    
    for table_name, cols in tables.items():
        code = "from ..base import base\n"
        code += "from flask import render_template, jsonify, request\n"
        code += "from ..models import %s\n" %(word(table_name, "_"))
        code += "from ..util import  models as util_models\n\n"
        code += "from .. import  db\n\n"
        
        with open("%s/%s.py"%( code_file_dir, table_name), 'w+') as fp:
            for api in apis:
                code += "\n\n" + api(table_name, cols)
            fp.write(code)
            fp.close()

def buidl_flask_page_code(table_name, cols):
    pages = ["index", "add"]
    code = ""
    for page in pages:
        code += "@base.route('/%s/%s', methods=['GET'])\n" %(table_name, page)
        code += "def %s_%s():\n" %(table_name, page)
        code += "    return render_template('%s/%s.html')\n\n\n" %(table_name, page)

    pages = ["update", "info"]
    for page in pages:
        code += "@base.route('/%s/%s', methods=['GET'])\n" %(table_name, page)
        code += "def %s_%s():\n" %(table_name, page)
        code += build_check_obj_exist_code(table_name, cols)
        code += "    return render_template('%s/%s.html', obj=%s)\n\n\n" %(table_name, page, table_name)
    return code

# handle_from_csv('/Users/mac/Documents/code/python/other/deou.csv', "/Users/mac/Desktop/dtype.csv")
# build_sql("deou_map.csv")


# +
# # tables = get_db_info('deou_map.csv')
# # build_flask_route(tables, "route")

# handle_from_csv("~/Desktop/shu.cvs", "~/Desktop/dtype.cvs")
# -

#handle_from_csv("/Users/mac/Desktop/mg.csv", "/Users/mac/Desktop/mg_map.csv","/Users/mac/Documents/code/python/other/builder/csv/dtype.csv")
