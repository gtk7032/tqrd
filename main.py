import re
from typing import Tuple

from sql_metadata import Parser


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
    if is_select_query(pure_query):
        return tables, ""
    elif len(tables) == 0:
        return [], ""
    elif len(tables) == 1:
        return tables[0], tables[0]
    else:
        return tables[1:], tables[0]


def is_select_query(query: str) -> bool:
    result = re.search(
        r"(DELETE|UPDATE|INSERT)", query, flags=re.DOTALL | re.IGNORECASE
    )
    return result is None


def main():
    filess = ["file1.sql"]

    queries = []
    for file in filess:
        with open(file, "r", encoding="utf-8") as f:
            sq = f.read().split(";")
            del sq[-1]  # empty
            queries.extend(sq)

    for query in queries:
        from_tables, to_table = extract_tables(query)
        print(from_tables)
        print(to_table)


if __name__ == "__main__":
    main()
