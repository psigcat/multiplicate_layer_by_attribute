# Multiplicate layer by attribute

Create multiple layers from all unique values from a selected field or expression.

## Expressions

Expressions have to be written in Standard SQL, meaning they will work in the Query Builder (SQLite/GeoPackage) and the QGIS Expression Engine without modification.

1. String Manipulation

- First characters: `substr("FIELD", 1, 3)`
- Middle characters: `substr("FIELD", 4, 2)`
- Uppercase: `upper("FIELD")`
- Lowercase: `lower("FIELD")`
- Concatenate: `` `"FIELD1"``
- Replace text: `replace("FIELD", 'old', 'new')`

2. Pattern Matching & Filtering

- Starts with: `"FIELD" LIKE '9%'`
- Ends with: `"FIELD" LIKE '%9'`
- Contains: `"FIELD" LIKE '%9%'`
- One of many: `"FIELD" IN ('A', 'B', 'C')`
- Case-sensitive: `"FIELD" ILIKE '%a%'`

3. Numbers & Logic

- Rounding: `round("FIELD", 2)`
- Absolute Value: `abs("FIELD")`
- Convert to Integer: `cast("FIELD" as integer)`
- Convert to Real: `cast("FIELD" as real)`
- If/Then Logic: `CASE WHEN "A" = 1 THEN 'Yes' ELSE 'No' END`
- Handle NULLs: `coalesce("FIELD", 0)` (Returns 0 if field is NULL)