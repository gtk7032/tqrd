import os
import re
import sys
from enum import Flag, auto
from typing import Tuple

from graphviz import Digraph
from sql_metadata import Parser


class QueryType(Flag):
    SELECT = auto()
    DELETE = auto()
    UPDATE = auto()
    INSERT = auto()


def remove_impurities(impure_query: str) -> str:
    result = re.search(
        r"(WITH|SELECT|DELETE|UPDATE|INSERT).*.$",
        impure_query,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return result.group(0) if result is not None else ""


def extract_tables(query: str) -> Tuple[list[str], str]:
    pure_query = remove_impurities(query)
    tables = Parser(pure_query).tables
    if guess_query_type(pure_query) == QueryType.SELECT:
        return tables, ""
    elif len(tables) == 0:
        return [], ""
    elif len(tables) == 1:
        return tables[0], tables[0]
    else:
        return tables[1:], tables[0]


def guess_query_type(query: str) -> QueryType:
    if re.search(r"(DELETE)", query, flags=re.DOTALL | re.IGNORECASE) is not None:
        return QueryType.DELETE
    elif re.search(r"(UPDATE)", query, flags=re.DOTALL | re.IGNORECASE) is not None:
        return QueryType.UPDATE
    elif re.search(r"(INSERT)", query, flags=re.DOTALL | re.IGNORECASE) is not None:
        return QueryType.INSERT
    else:
        return QueryType.SELECT


def select_color(query_type: QueryType) -> str:
    if query_type == QueryType.DELETE:
        return "#1b9e77"
    elif query_type == QueryType.UPDATE:
        return "#d95f02"
    elif query_type == QueryType.INSERT:
        return "#e6ab02"
    else:
        return "#e7298a"


def main():
    # files = ["file1.sql"]
    sqlfiles = sys.argv[1:]
    dg = Digraph()
    dg.attr("graph", rankdir="LR")

    for sqlfile in sqlfiles:
        fnm = os.path.splitext(os.path.basename(sqlfile))[0]
        with open(sqlfile, "r", encoding="utf-8") as f:
            queries = f.read().split(";")
            del queries[-1]  # empty

            for query in queries:
                query_type = guess_query_type(query)
                from_tables, to_table = extract_tables(query)
                dg.node(to_table)

                for from_table in from_tables:
                    dg.node(from_table)
                    dg.edge(
                        tail_name=from_table,
                        head_name=to_table,
                        label=fnm,
                        color=select_color(query_type),
                    )

    dg.render("./dgraph", view=True, format="svg")


if __name__ == "__main__":
    main()
