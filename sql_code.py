'''
Author: your name
Date: 2021-03-17 11:09:29
LastEditTime: 2021-04-04 16:06:59
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /builder/sql_code.py
'''
import pandas as pd

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