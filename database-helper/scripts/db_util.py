# !/usr/bin/python3

# -*- coding: utf-8 -*-

"""
@author: GuYouda
@date:   2026/01/07
@desc:
"""
import argparse
import logging
import logging.handlers
import os
import traceback

import pymysql

# 输出到控制台
console_log_handler = logging.StreamHandler()
console_log_handler.setLevel("INFO")
log_formatter = logging.Formatter(
    "[%(process)d] [%(thread)d] [%(levelname)-8s] [%(asctime)s] [%(filename)s %(funcName)s line:%(lineno)d]  %(message)s")
console_log_handler.setFormatter(log_formatter)

_logger = logging.getLogger()
_logger.addHandler(console_log_handler)
_logger.setLevel("INFO")


def __execute(sql: str):
    """
    执行数据库SQL语句
    :param sql: str SQL语句
    :return:
    """
    if not os.getenv("DB_HELPER_HOST"):
        raise ValueError("DB_HELPER_HOST is empty")
    if not os.getenv("DB_HELPER_PORT"):
        raise ValueError("DB_HELPER_PORT is empty")
    if not os.getenv("DB_HELPER_USER"):
        raise ValueError("DB_HELPER_USER is empty")
    if not os.getenv("DB_HELPER_PASSWORD"):
        raise ValueError("DB_HELPER_PASSWORD is empty")
    if not os.getenv("DB_HELPER_DB"):
        raise ValueError("DB_HELPER_DB is empty")

    conn = pymysql.connect(
        host=os.getenv("DB_HELPER_HOST"),
        port=int(os.getenv("DB_HELPER_PORT")),
        user=os.getenv("DB_HELPER_USER"),
        passwd=os.getenv("DB_HELPER_PASSWORD"),
        db=os.getenv("DB_HELPER_DB"),
        charset=os.getenv("DB_CHARSET", "utf8"),
    )
    cursor = conn.cursor()
    try:
        logging.info("SQL executed: %s", sql)
        effect_row = cursor.execute(sql)
        result = cursor.fetchall()
    except Exception as e:
        logging.error("SQL ERROR: %s  sql[%s]", e, sql)
        logging.error(traceback.format_exc())
        result = None
        effect_row = -1
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return effect_row, result


def get_all_tables():
    result = __execute(
        "SELECT TABLE_NAME,TABLE_COMMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA !='information_schema'")
    tables = []
    for item in result[1]:
        tables.append({"TABLE_NAME": item[0], "TABLE_COMMENT": item[1]})
    return tables


def get_all_columns(table):
    result = __execute(
        "SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT FROM information_schema.COLUMNS WHERE TABLE_NAME='{}'".format(
            table))
    columns = []
    for item in result[1]:
        columns.append({"COLUMN_NAME": item[0], "COLUMN_TYPE": item[1], "COLUMN_COMMENT": item[2]})
    return columns


def get_all_indexes(table):
    result = __execute("SHOW INDEXES FROM {}".format(table))
    indexes = []
    for item in result[1]:
        indexes.append({"KEY_NAME": item[2], "INDEX_TYPE": item[3], "COLUMN_NAME": item[4]})
    return indexes


def get_table_structure(table):
    result = __execute("SHOW CREATE TABLE {}".format(table))
    if result[0] == 1 and len(result[1]) > 0:
        return result[1][0][1]
    return None


def get_table_count(table):
    result = __execute("SELECT COUNT(*) FROM {}".format(table))
    if result[0] == 1 and len(result[1]) > 0:
        return result[1][0][0]
    return None


def execute_sql(sql):
    # 仅允许SELECT
    if not str(sql).lower().startswith("select"):
        raise ValueError("Only support SELECT statement.")
    result = __execute(sql)
    return result


def get_sql_count(sql):
    sql = str(sql).lower()
    # 将 select 和 from 中间的所有内容替换为 count(*)
    # 找到from的位置 将前面的内容替换为 select count(*)
    idx = sql.index("from")
    sql = "select count(*) " + sql[idx:]

    result = __execute(sql)
    if result[0] == 1 and len(result[1]) > 0:
        return result[1][0][0]
    return None


def _test():
    """
    测试
    """
    print(get_all_tables())
    print(get_all_columns("task"))
    print(get_all_indexes("task"))
    print(get_table_structure("task"))
    print(get_table_count("task"))
    print(execute_sql("select * from task where id > 65530 AND id < 65535"))
    print(get_sql_count("select id  from task where id > 6553 AND id < 65535"))


if __name__ == '__main__':
    # 解析命令参数，并调起对应方法执行
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, help='Action to perform')
    parser.add_argument('--table', type=str, help='Table name')
    parser.add_argument('--query', type=str, help='Query string')
    args = parser.parse_args()
    action = args.action
    if action == "get_all_tables":
        print(get_all_tables())
    elif action == "get_all_columns":
        print(get_all_columns(args.table))
    elif action == "get_table_count":
        print(get_table_count(args.table))
    elif action == "get_table_structure":
        print(get_table_structure(args.table))
    elif action == "execute_sql":
        print(execute_sql(args.query))
    elif action == "get_sql_count":
        print(get_sql_count(args.query))
    else:
        print('暂不支持该指令')

