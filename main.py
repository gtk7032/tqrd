import argparse
import csv
import os
import re
from enum import Flag, auto
from logging import exception
from typing import List, Tuple

from graphviz import Digraph
from sql_metadata import Parser


class QueryType(Flag):
    SELECT = auto()
    DELETE = auto()
    UPDATE = auto()
    INSERT = auto()
    UNKNOWN = auto()


def is_query(sentence: str) -> bool:
    return re.search(
        r"(WITH|DELETE|UPDATE|INSERT)",
        sentence,
        flags=re.DOTALL | re.IGNORECASE,
    ) is not None and re.search(
        r"SELECT.*FROM",
        sentence,
        flags=re.DOTALL | re.IGNORECASE,
    )


def remove_impurities(impure_query: str) -> str:
    result = re.search(
        r"(WITH|SELECT|DELETE|UPDATE|INSERT).*.$",
        impure_query,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return result.group(0) if result is not None else ""


def extract_tables(query: str) -> Tuple[List[str], str]:
    pure_query = remove_impurities(query)
    tables = Parser(pure_query).tables
    print(tables)
    if guess_query_type(pure_query) == QueryType.SELECT:
        return tables, ""
    elif len(tables) == 0:
        return [], ""
    elif len(tables) == 1:
        return tables[0], tables[0]
    else:
        return tables[1:], tables[0]


def guess_query_type(query: str) -> QueryType:
    if re.search(r"DELETE", query, flags=re.DOTALL | re.IGNORECASE) is not None:
        return QueryType.DELETE
    elif re.search(r"UPDATE", query, flags=re.DOTALL | re.IGNORECASE) is not None:
        return QueryType.UPDATE
    elif re.search(r"INSERT", query, flags=re.DOTALL | re.IGNORECASE) is not None:
        return QueryType.INSERT
    elif re.search(r"SELECT", query, flags=re.DOTALL | re.IGNORECASE) is not None:
        return QueryType.SELECT
    else:
        return QueryType.UNKNOWN


def select_color(query_type: QueryType) -> str:
    if query_type == QueryType.DELETE:
        return "#1b9e77"
    elif query_type == QueryType.UPDATE:
        return "#d95f02"
    elif query_type == QueryType.INSERT:
        return "#e6ab02"
    else:
        return "#e7298a"


# def add_graph(path: str, dg: Digraph):

#     with open(path, "r", encoding="utf-8") as f:
#         rows = csv.reader(f)
#         for row in rows:
#             from_table = row[0]
#             to_table = row[1]
#             arrow_name = row[2]
#             query_type = row[3]


def main():

    parser = argparse.ArgumentParser(description="an example program")
    parser.add_argument("--files", required=True, nargs="*", type=str)
    parser.add_argument("--add", required=False, nargs=1, type=str)
    parser.add_argument("--mappings", required=False, nargs=1, type=str)
    args = parser.parse_args()
    dg = Digraph()
    dg.attr("graph", rankdir="LR")

    for sqlfile in args.files:
        procedure = os.path.splitext(os.path.basename(sqlfile))[0]
        with open(sqlfile, "r", encoding="utf-8") as f:
            queries = f.read().split(";")
            for query in queries:
                if not is_query(query):
                    continue
                query_type = guess_query_type(query)
                if query_type == QueryType.UNKNOWN:
                    continue
                try:
                    from_tables, to_table = extract_tables(query)
                except:
                    continue
                dg.node(
                    to_table,
                    shape="cylinder",
                    color="white" if query_type == QueryType.SELECT else "black",
                )
                dg.node(procedure, shape="note")
                dg.edge(
                    tail_name=procedure,
                    head_name=to_table,
                    color=select_color(query_type),
                )
                for from_table in from_tables:
                    dg.node(from_table, shape="cylinder")
                    dg.edge(
                        tail_name=from_table,
                        head_name=procedure,
                        color=select_color(query_type),
                    )

    dg.render("./dgraph", view=True, format="svg")


if __name__ == "__main__":
    main()
