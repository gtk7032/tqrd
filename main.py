import argparse
import csv
import os
import re
from enum import Flag, auto
from typing import Generator, Tuple

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
        r"(DELETE|UPDATE|INSERT)",
        sentence,
        flags=re.DOTALL | re.IGNORECASE,
    ) or re.search(
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


def query_gen(files: list[str]) -> Generator[Tuple[str, str, QueryType], None, None]:
    for file in files:
        basename = os.path.splitext(os.path.basename(file))[0]
        with open(file, "r", encoding="utf-8") as f:
            queries = f.read().split(";")
            for query in queries:
                if not is_query(query):
                    continue
                query_type = guess_query_type(query)
                if query_type == QueryType.UNKNOWN:
                    continue
                yield basename, query, query_type


def draw_diagram(
    from_tables: list[str], to_table: str, query_type: QueryType, query_file: str
):
    dg.node(
        to_table,
        shape="cylinder",
        color="white" if query_type == QueryType.SELECT else "black",
    )
    dg.node(query_file, shape="note")
    dg.edge(
        tail_name=query_file,
        head_name=to_table,
        color=select_color(query_type),
    )
    for from_table in from_tables:
        dg.node(from_table, shape="cylinder")
        dg.edge(
            tail_name=from_table,
            head_name=query_file,
            color=select_color(query_type),
        )


def read_mapping_file(file: str) -> dict[str, str]:
    map = {}
    try:
        with open(file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in reader:
                map[r[0]] = r[1]
    finally:
        return map


def map_tables(frms: list[str], to: str, map: dict[str, str]) -> tuple[list[str], str]:
    return (
        [frm + "\n" + map.get(frm, "") for frm in frms],
        to + "\n" + map.get(to, ""),
    )


def get_queryfiles(dir: str) -> list[str]:
    queryfiles: list[str] = []
    for current, _, subfiles in os.walk(dir):
        queryfiles.extend(
            os.path.join(current, subfile)
            for subfile in subfiles
            if os.path.splitext(subfile)[1] in [".sh", ".sql"]
        )
    return queryfiles


dg = Digraph()
dg.attr("graph", rankdir="LR")


def main():

    parser = argparse.ArgumentParser(
        description="draw Table and Query Relationship Diagram"
    )
    parser.add_argument("--querydir", required=False, nargs=1, type=str)
    parser.add_argument("--mappings", required=False, nargs=1, type=str)
    parser.add_argument("--relations", required=False, nargs=1, type=str)
    args = parser.parse_args()

    mappings = read_mapping_file(args.mappings[0])

    for query_file, query, query_type in query_gen(get_queryfiles(args.querydir[0])):

        try:
            frms, to = extract_tables(query)
            frms, to = map_tables(frms, to, mappings)
        except:
            continue

        draw_diagram(frms, to, query_type, query_file)

    dg.render("./dgraph", view=True, format="svg")


if __name__ == "__main__":
    main()
