import pytest

from src.services.db import schema_diagnostics

pytestmark = pytest.mark.unit


class _StubQuery:
    def __init__(self, should_fail=False, error=None):
        self.should_fail = should_fail
        self.error = error or RuntimeError("query failed")

    def select(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.should_fail:
            raise self.error
        return {"ok": True}


class _StubRPC:
    def __init__(self, should_fail=False, error=None):
        self.should_fail = should_fail
        self.error = error or RuntimeError("rpc failed")

    def execute(self):
        if self.should_fail:
            raise self.error
        return {"ok": True}


class _StubDB:
    def __init__(
        self, table_should_fail=False, table_error=None, rpc_should_fail=False, rpc_error=None
    ):
        self.table_should_fail = table_should_fail
        self.table_error = table_error
        self.rpc_should_fail = rpc_should_fail
        self.rpc_error = rpc_error

    def table(self, _name):
        return _StubQuery(self.table_should_fail, self.table_error)

    def rpc(self, _name, _payload):
        return _StubRPC(self.rpc_should_fail, self.rpc_error)


@pytest.mark.anyio
async def test_check_postgrest_schema_profile_ok():
    validator = schema_diagnostics.SchemaValidator(_StubDB())

    result = await validator._check_postgrest_schema_profile()

    assert result["ok"] is True


@pytest.mark.anyio
async def test_check_postgrest_schema_profile_detects_pgrst106():
    validator = schema_diagnostics.SchemaValidator(
        _StubDB(
            table_should_fail=True,
            table_error=RuntimeError("PGRST106 schema must be one of the following"),
        )
    )

    result = await validator._check_postgrest_schema_profile()

    assert result["ok"] is False
    assert result["code"] == "PGRST106"
    assert validator.validation_errors


@pytest.mark.anyio
async def test_check_rpc_search_similar_documents_not_found_error():
    validator = schema_diagnostics.SchemaValidator(
        _StubDB(rpc_should_fail=True, rpc_error=RuntimeError("function not found"))
    )

    result = await validator._check_rpc_search_similar_documents()

    assert result is False
    assert any("search_similar_documents" in err for err in validator.validation_errors)


@pytest.mark.anyio
async def test_check_table_document_chunks_missing():
    validator = schema_diagnostics.SchemaValidator(
        _StubDB(table_should_fail=True, table_error=RuntimeError("table missing"))
    )

    result = await validator._check_table_document_chunks()

    assert result is False


@pytest.mark.anyio
async def test_check_column_embedding_missing_column():
    validator = schema_diagnostics.SchemaValidator(
        _StubDB(table_should_fail=True, table_error=RuntimeError("column embedding does not exist"))
    )

    result = await validator._check_column_embedding()

    assert result["exists"] is False


@pytest.mark.anyio
async def test_validate_all_returns_warning_status_when_no_errors():
    validator = schema_diagnostics.SchemaValidator(_StubDB())

    result = await validator.validate_all()

    assert result["status"] in {"ok", "warning"}
    assert "checks" in result


def test_get_validation_summary_formats_sections():
    summary = schema_diagnostics.get_validation_summary(
        {
            "status": "error",
            "errors": ["bad"],
            "warnings": ["warn"],
            "checks": {},
        }
    )

    assert "Schema Validation: ERROR" in summary
    assert "ERRORS:" in summary
    assert "WARNINGS:" in summary
