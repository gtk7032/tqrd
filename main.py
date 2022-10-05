from __future__ import annotations

import csv
import os
import re
from enum import Flag, auto
from typing import Generator, Tuple

from graphviz import Digraph
from sql_metadata import Parser


class QueryType(Flag):
    SELECT = (auto(), "SELECT")
    DELETE = (auto(), "DELETE")
    UPDATE = (auto(), "UPDATE")
    INSERT = (auto(), "INSERT")
    UNKNOWN = (auto(), "UNKNOWN")

    def __init__(self, id, val: str):
        self.id = id
        self.val = val

    @classmethod
    def members_as_list(cls) -> list[QueryType]:
        return [*cls.__members__.values()]

    @classmethod
    def get_by_val(cls, val: str) -> QueryType:
        for m in cls.members_as_list():
            if m.val == val:
                return m
        return QueryType.UNKNOWN


class TableExtractionError(Exception):
    pass


def is_query(sentence: str) -> bool:
    return bool(
        re.search(
            "(DELETE|UPDATE|INSERT)",
            sentence,
            flags=re.DOTALL | re.IGNORECASE,
        )
        or re.search(
            "SELECT.*FROM",
            sentence,
            flags=re.DOTALL | re.IGNORECASE,
        )
    )


def remove_impurities(impure_query: str) -> str:
    result = re.search(
        "(WITH|SELECT|DELETE|UPDATE|INSERT).*.$",
        impure_query,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return result.group(0) if result is not None else ""


def extract_tables(query: str) -> Tuple[list[str], str]:
    pure_query = remove_impurities(query)
    try:
        tables = Parser(pure_query).tables
    except:
        raise TableExtractionError("TableExtractionError")
    if guess_query_type(pure_query) == QueryType.SELECT:
        return tables, ""
    elif len(tables) == 0:
        return [], ""
    elif len(tables) == 1:
        return tables[0], tables[0]
    else:
        return tables[1:], tables[0]


def guess_query_type(query: str) -> QueryType:
    if re.search("DELETE", query, flags=re.DOTALL | re.IGNORECASE):
        return QueryType.DELETE
    elif re.search("UPDATE", query, flags=re.DOTALL | re.IGNORECASE):
        return QueryType.UPDATE
    elif re.search("INSERT", query, flags=re.DOTALL | re.IGNORECASE):
        return QueryType.INSERT
    elif re.search("SELECT", query, flags=re.DOTALL | re.IGNORECASE):
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
    elif query_type == QueryType.SELECT:
        return "#e7298a"
    else:
        return "#ffffff"


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


def read_mapping(file: str) -> dict[str, str]:
    map = {}
    try:
        with open(file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in reader:
                map[r[0].upper()] = r[1]
    finally:
        return map


def map_tables(frms: list[str], to: str, map: dict[str, str]) -> tuple[list[str], str]:
    return (
        [frm + "\n" + map.get(frm.upper(), "") for frm in frms],
        to + "\n" + map.get(to.upper(), ""),
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


def read_relations(
    path: str,
) -> Generator[Tuple[list[str], str, str, QueryType], None, None]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            yield r[0].split(":"), r[1], r[2], QueryType.get_by_val(r[3].upper())


dg = Digraph()
dg.attr("graph", rankdir="LR")


def main():

    mappings = read_mapping(os.path.join("resources", "mappings.csv"))

    for query_file, query, query_type in query_gen(
        get_queryfiles(os.path.join("resources", "queries"))
    ):
        try:
            frms, to = extract_tables(query)
        except TableExtractionError:
            continue
        frms, to = map_tables(frms, to, mappings)
        draw_diagram(frms, to, query_type, query_file)

    for frms, to, query, type in read_relations(
        os.path.join("resources", "relations.csv")
    ):
        frms, to = map_tables(frms, to, mappings)
        draw_diagram(frms, to, type, query)

    dg.render("./dgraph", view=False, format="svg", cleanup=True)


if __name__ == "__main__":
    main()
