import re

from sql_metadata import Parser


def remove_impurities(impure_query):
    result = re.search(
        r"(WITH|DELETE|UPDATE|INSERT).*.$", impure_query, flags=re.DOTALL
    )
    return result.group(0) if result is not None else None


def extract_tables(query):
    pure_query = remove_impurities(query)
    return Parser(pure_query).tables if pure_query is not None else None


def main():
    filess = ["file1.sql"]

    queries = []
    for file in filess:
        with open(file, "r", encoding="utf-8") as f:
            queries.extend(f.read().split(";"))

    for query in queries:
        tables = extract_tables(query)
        if tables is None:
            continue
        print(tables)


if __name__ == "__main__":
    main()
