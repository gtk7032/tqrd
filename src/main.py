from __future__ import annotations

import csv
import os
import re
import sys
from typing import Generator, Tuple

from graphviz import Digraph
from sql_metadata import Parser, QueryType


class QueryParseError(Exception):
    pass


def contains_query(string: str) -> bool:
    return bool(
        re.search(
            "(SELECT|DELETE|UPDATE|INSERT)",
            string,
            flags=re.DOTALL | re.IGNORECASE,
        )
    )


def remove_impurities(impure_query: str) -> str:
    result = re.search(
        "(WITH|SELECT|DELETE|UPDATE|INSERT).*.$",
        impure_query,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return result.group(0) if result else ""


def crassify_tables(tables: list[str], query_type: QueryType) -> Tuple[list[str], str]:
    if query_type == QueryType.SELECT:
        return tables, ""
    elif len(tables) == 1:
        return [tables[0]], tables[0]
    else:
        return tables[1:], tables[0]


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


def query_gen(files: list[str]) -> Generator[Tuple[str, str], None, None]:
    for file in files:
        basename = os.path.splitext(os.path.basename(file))[0]
        with open(file, "r", encoding="utf-8") as f:
            strings = f.read().split(";")
            for string in strings:
                if not contains_query(string):
                    continue
                pure_query = remove_impurities(string)
                yield basename, pure_query


def parse_query(query: str) -> Tuple[QueryType, list[str]]:
    parser = Parser(query)
    try:
        query_type = parser.query_type
        tables = parser.tables
    except ValueError:
        raise QueryParseError("QueryParseError")
    return query_type, tables


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
    map: dict[str, str] = {}
    if not file:
        return map
    with open(file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            map[r["table"].upper()] = r["label"]
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
            if os.path.splitext(subfile)[1]
        )
    return queryfiles


def read_relations(
    path: str,
) -> Generator[Tuple[list[str], str, str, QueryType], None, None]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            yield r["from"].split(":"), r["to"], r["query"], QueryType(
                r["type"].upper()
            )


def write_unparsable(unparsable: list[dict[str, str]]):
    with open(
        os.path.join("output", "unparsable_queries.csv"), "w", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        for up in unparsable:
            writer.writerow([up["file"], up["query"].replace("\n", "")])


def should_ignore(
    query_type: QueryType, tables: list[str], display_types: list[QueryType]
) -> bool:
    return bool(
        (query_type == QueryType.SELECT and not len(tables))
        or query_type not in display_types
    )


def parse_display_types(display_types: str) -> list[QueryType]:

    if not display_types:
        return [QueryType.SELECT, QueryType.UPDATE, QueryType.INSERT, QueryType.DELETE]

    dtp: list[QueryType] = []
    for type in list(display_types):
        if type in ["i", "I"]:
            dtp.append(QueryType.INSERT)
        elif type in ["d", "D"]:
            dtp.append(QueryType.DELETE)
        elif type in ["u", "U"]:
            dtp.append(QueryType.UPDATE)
        elif type in ["s", "S"]:
            dtp.append(QueryType.SELECT)
    return dtp


dg = Digraph()
dg.attr("graph", rankdir="LR")

if __name__ == "__main__":

    args = sys.argv
    disptypes = parse_display_types(args[1] if len(args) == 2 else "")

    unparsable: list[dict[str, str]] = []
    mappings = read_mapping(os.path.join("resources", "mappings.csv"))

    for query_file, query in query_gen(
        get_queryfiles(os.path.join("resources", "queries"))
    ):
        try:
            query_type, tables = parse_query(query)
        except QueryParseError:
            unparsable.append({"file": query_file, "query": query})
            continue

        if should_ignore(query_type, tables, disptypes):
            continue

        frms, to = crassify_tables(tables, query_type)
        frms, to = map_tables(frms, to, mappings)
        draw_diagram(frms, to, query_type, query_file)

    write_unparsable(unparsable)

    for frms, to, query, query_type in read_relations(
        os.path.join("resources", "relations.csv")
    ):
        if should_ignore(query_type, frms + [to], disptypes):
            continue
        frms, to = map_tables(frms, to, mappings)
        draw_diagram(frms, to, query_type, query)

    dg.render(os.path.join("output", "diagram"), view=False, format="svg", cleanup=True)
