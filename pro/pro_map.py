'''
Author: your name
Date: 2021-03-17 11:12:46
LastEditTime: 2021-04-04 14:41:13
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /builder/util/pro_map_util.py
'''
import pandas as pd
# from ..pro import trans.youdao_trans as youdao_trans
# from ..pro import trans.word  as word
# import trans.youdao_trans as youdao_trans
# import trans.word  as word

from translate import Translator
import csv
import re, urllib,json
import jieba
from functools import reduce 


def word(s, c):
    return s.replace(c, " ").title().replace(" ","")



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

def fetch_pro_map(csv_file_path):
    df = pd.read_csv(csv_file_path)
    tables = {}
    for i, t in df[df.type == "table"].iterrows():
        cols = []
        cols.append({"name":"id", "dtype":"int", "comment":"ID"})
        for j, col in df[(df.type=="col")  & (df.table==t["comment"])].iterrows():
            cols.append({"name":col["en"], "dtype":col["dtype"], "comment": col["comment"]})
        tables[t["en"]] = cols
    return tables



def build_pro_map(pro_src_csv_file, pro_map_csv_file, dtype_cvs_file):
    table = []
    with open(pro_src_csv_file, 'r') as f:
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
    
    df.to_csv(pro_map_csv_file, index=False)
    
    print("build success !")
    print("project map infomation has  saved to %s" %(pro_map_csv_file))


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
        
        sql_str += "    `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'created time',\n"
        sql_str += "    `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'updated time',\n" 
        sql_str += "    PRIMARY KEY (`id`) \n"
        sql_str += ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='%s' ;\n\n" % (t["table"])
    
    print(sql_str)
