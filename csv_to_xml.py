import argparse
import csv
from xml.etree.ElementTree import Element, SubElement, ElementTree

GRADE_8_COLUMN_ORDER = [
    ("Problem Number", "ProblemNumber"),
    ("Directions", "Directions"),
    ("Problem", "Problem"),
    ("Solution", "Solution"),
    ("Alternate Solution", "AlternateSolution"),
    ("Common Core Category", "CommonCoreCategory"),
]

def csv_to_xml(
    csv_path: str,
    xml_path: str,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> None:
    """
    Convert the CSV to XML with the SAME columns:
      Problem Number, Directions, Problem, Solution, Alternate Solution, Common Core Category

    - No transformations or parsing of math text.
    - No fraction reduction.
    - Preserves text verbatim.
    - Emits empty elements if cells are missing.
    """
    root = Element("problems")

    with open(csv_path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        headers = reader.fieldnames or []
        required = [c[0] for c in GRADE_8_COLUMN_ORDER]
        missing = [h for h in required if h not in headers]
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {missing}. "
                f"Found columns: {headers}"
            )

        for idx, row in enumerate(reader, start=1):
            prob_el = SubElement(root, "problem", {"id": str(idx)})
            for csv_name, xml_tag in GRADE_8_COLUMN_ORDER:
                # Pull the cell as-is; preserve exactly
                value = row.get(csv_name, "")
                # Ensure it's a string
                if value is None:
                    value = ""
                # Create the element and set text verbatim (no trimming)
                el = SubElement(prob_el, xml_tag)
                el.text = value

    _indent_xml(root)
    ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)

def _indent_xml(elem, level=0):
    """Pretty-print the XML with indentation (no content changes)."""
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

def main():
    ap = argparse.ArgumentParser(
        description="CSV → XML (pass-through) for 8th grade math problems with fixed columns."
    )
    ap.add_argument("--in", dest="csv_in", required=True, help="Input CSV path.")
    ap.add_argument("--out", dest="xml_out", required=True, help="Output XML path.")
    ap.add_argument("--delimiter", default=",", help="CSV delimiter (default ',').")
    ap.add_argument("--encoding", default="utf-8", help="CSV encoding (default 'utf-8').")
    args = ap.parse_args()

    csv_to_xml(
        csv_path=args.csv_in,
        xml_path=args.xml_out,
        delimiter=args.delimiter,
        encoding=args.encoding,
    )

if __name__ == "__main__":
    main()
