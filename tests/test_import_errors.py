import sqlite3

from sqlalchemy.exc import IntegrityError

from finance_ai.imports.errors import describe_import_error


def test_describe_import_error_for_duplicate_category():
    orig = sqlite3.IntegrityError("UNIQUE constraint failed: categories.name")
    exc = IntegrityError(
        statement="INSERT INTO categories (name, category_type) VALUES (?, ?)",
        params=("Salary", "income"),
        orig=orig,
    )

    message = describe_import_error(exc)

    assert "duplicate data" in message
    assert "category" in message
    assert "categories.name" not in message
    assert "SQL" not in message


def test_describe_import_error_for_unrecognized_table():
    orig = sqlite3.IntegrityError("UNIQUE constraint failed: widgets.sku")
    exc = IntegrityError(statement="INSERT INTO widgets ...", params=("ABC",), orig=orig)

    message = describe_import_error(exc)

    assert "widgets" in message


def test_describe_import_error_for_generic_exception():
    message = describe_import_error(ValueError("Corrupt zip file"))

    assert message == "Corrupt zip file"
