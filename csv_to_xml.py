#!/usr/bin/env python3
import argparse
import csv
from typing import List, Tuple
from xml.etree.ElementTree import Element, SubElement, ElementTree

def parse_mapping(arg: str) -> List[Tuple[str, str]]:
    # Parse '--columns "CSV:XML,CSV:XML"' into [(CSV, XML), ...].
    if not arg:
        return []
    out: List[Tuple[str, str]] = []
    for pair in arg.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if ":" not in pair:
            raise ValueError(f"Invalid mapping item '{pair}'. Use 'CSVName:XMLTag'.")
        csv_name, xml_tag = pair.split(":", 1)
        if not csv_name or not xml_tag:
            raise ValueError(f"Invalid mapping item '{pair}'.")
        out.append((csv_name, xml_tag))
    return out

def _indent_xml(elem, level=0):
    # Pretty-print XML by inserting indentation/newlines (no content changes).
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def csv_to_xml(
    csv_path: str,
    xml_path: str,
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
    columns: List[Tuple[str, str]] = None,  # optional explicit mapping: [(CSV header, XML tag), ...]
    id_col: str = None,                      # optional CSV column to use as the row id
    root_tag: str = "rows",                  # root element name
    row_tag: str = "row",                    # row element name
    short_empty_elements: bool = False,      # render empty tags as <Tag/> if True
) -> None:
    # Convert a CSV to XML without altering cell text.
    root = Element(root_tag)  # create root element

    # Open CSV with requested delimiter/encoding
    with open(csv_path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames or []

        # If no custom mapping: map every CSV header to an XML tag with spaces removed
        mapping = columns if columns else [(h, h.replace(" ", "")) for h in headers]

        # Ensure required columns for the chosen mapping exist
        required = [csv_name for csv_name, _ in mapping]
        missing = [h for h in required if h not in headers]
        if missing:
            raise ValueError(f"CSV is missing required columns: {missing}. Found: {headers}")

        # Iterate rows and emit XML
        for idx, row in enumerate(reader, start=1):
            row_id = (row.get(id_col, "") if id_col else "") or str(idx)  # prefer id_col else index
            row_el = SubElement(root, row_tag, {"id": row_id})

            for csv_name, xml_tag in mapping:
                val = row.get(csv_name, "")
                if val is None:
                    val = ""                  # always emit element, even when empty
                el = SubElement(row_el, xml_tag)
                el.text = val                 # preserve text verbatim

    _indent_xml(root)  # pretty-print
    ElementTree(root).write(
        xml_path,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=short_empty_elements,
    )

def main():
    # CLI flags kept minimal; defaults are generic and work for similar CSVs
    ap = argparse.ArgumentParser(description="CSV → XML (pass-through). No transformation of text.")
    ap.add_argument("--in", dest="csv_in", required=True, help="Input CSV path.")
    ap.add_argument("--out", dest="xml_out", required=True, help="Output XML path.")
    ap.add_argument("--delimiter", default=",", help="CSV delimiter (default ',').")
    ap.add_argument("--encoding", default="utf-8", help="CSV encoding (default 'utf-8').")
    ap.add_argument("--columns", default="", help="Custom mapping 'CSV:XML,CSV:XML' (optional).")
    ap.add_argument("--id-col", default=None, help="CSV column to use for row id (optional).")
    ap.add_argument("--root-tag", default="rows", help="Root XML element name (default 'rows').")
    ap.add_argument("--row-tag", default="row", help="Row XML element name (default 'row').")
    ap.add_argument("--short-empty-elements", action="store_true", help="Render empty tags as <Tag/>.")
    args = ap.parse_args()

    mapping = parse_mapping(args.columns) if args.columns else None

    csv_to_xml(
        csv_path=args.csv_in,
        xml_path=args.xml_out,
        delimiter=args.delimiter,
        encoding=args.encoding,
        columns=mapping,
        id_col=args.id_col,
        root_tag=args.root_tag,
        row_tag=args.row_tag,
        short_empty_elements=args.short_empty_elements,
    )

if __name__ == "__main__":
    main()
