# ABOUTME: Security tests for common/database.py residuals in issue #80.
# ABOUTME: Covers upsert SQL parameterisation, credential redaction and query-log hygiene.

import pandas as pd
import pytest

try:
    from assetutilities.common.database import Database
except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
    pytest.skip(
        f"assetutilities.common optional dependency missing: {exc}",
        allow_module_level=True,
    )

# Synthetic, non-secret. Only ever used to prove it never reaches stdout.
FAKE_PASSWORD = "n0t-a-real-password-2f9c"


def make_db():
    return Database(
        {
            "server_type": "postgresql",
            "server": "db.example.internal",
            "database": "analytics",
            "schema": "public",
            "user": "svc_reader",
            "password": FAKE_PASSWORD,
            "port": 5432,
        }
    )


class TestUpsertStatementIsParameterised:
    """build_upsert_statement must bind values, never interpolate them."""

    def _build(self, df, cfg=None):
        cfg = cfg or {"table_name": "stocks.analysis", "primary_key": "ticker"}
        return make_db().build_upsert_statement(df, cfg)

    def test_statement_text_is_exactly_the_expected_parameterised_upsert(self):
        df = pd.DataFrame([{"ticker": "ACME", "company": "Acme Corp"}])
        sql, _params = self._build(df)
        assert sql == (
            "INSERT INTO stocks.analysis (ticker, company) "
            "VALUES (:v_0, :v_1) "
            "ON CONFLICT (ticker) DO UPDATE SET company = excluded.company"
        )

    def test_apostrophe_value_is_carried_in_the_bound_parameters(self):
        df = pd.DataFrame([{"ticker": "OBR", "company": "O'Brien & Sons"}])
        _sql, params = self._build(df)
        assert params["v_1"] == "O'Brien & Sons"

    def test_apostrophe_value_never_appears_in_the_statement_text(self):
        df = pd.DataFrame([{"ticker": "OBR", "company": "O'Brien & Sons"}])
        sql, _params = self._build(df)
        assert "O'Brien" not in sql

    def test_injection_payload_never_appears_in_the_statement_text(self):
        payload = "x'); DROP TABLE stocks.analysis; --"
        df = pd.DataFrame([{"ticker": "EVIL", "company": payload}])
        sql, _params = self._build(df)
        assert "DROP TABLE" not in sql

    def test_numeric_value_is_bound_unchanged_instead_of_raising_typeerror(self):
        df = pd.DataFrame([{"ticker": "ACME", "shares": 4200}])
        _sql, params = self._build(
            df, {"table_name": "stocks.analysis", "primary_key": "ticker"}
        )
        assert params["v_1"] == 4200

    def test_none_value_is_bound_as_none(self):
        df = pd.DataFrame([{"ticker": "ACME", "company": None}])
        _sql, params = self._build(df)
        assert params["v_1"] is None


class TestUpsertIdentifiersAreValidated:
    """Table/column names cannot be bound, so they must be validated instead."""

    def test_table_name_carrying_a_statement_terminator_is_rejected(self):
        df = pd.DataFrame([{"ticker": "ACME", "company": "Acme"}])
        with pytest.raises(ValueError):
            make_db().build_upsert_statement(
                df,
                {
                    "table_name": "stocks.analysis; DROP TABLE stocks.keys",
                    "primary_key": "ticker",
                },
            )

    def test_column_name_carrying_a_statement_terminator_is_rejected(self):
        df = pd.DataFrame([{"ticker": "ACME", "company); DROP TABLE t; --": "x"}])
        with pytest.raises(ValueError):
            make_db().build_upsert_statement(
                df, {"table_name": "stocks.analysis", "primary_key": "ticker"}
            )

    def test_primary_key_absent_from_the_dataframe_is_rejected(self):
        df = pd.DataFrame([{"ticker": "ACME", "company": "Acme"}])
        with pytest.raises(ValueError):
            make_db().build_upsert_statement(
                df, {"table_name": "stocks.analysis", "primary_key": "isin"}
            )

    def test_schema_qualified_table_name_is_accepted(self):
        # Schema-qualified names must stay accepted: a validator that rejected
        # the dot would break the documented usage shape. The equivalent
        # function in a sibling repo is invoked with 'stocks.analysis'. That is
        # a separate copy, not a caller of this one -- this module currently has
        # no importer in the workspace -- so it is evidence about the intended
        # config shape, not proof of a live call path.
        df = pd.DataFrame([{"ticker": "ACME", "company": "Acme"}])
        sql, _params = make_db().build_upsert_statement(
            df, {"table_name": "stocks.analysis", "primary_key": "ticker"}
        )
        assert sql.startswith("INSERT INTO stocks.analysis (")


class TestUpsertRoundTripsThroughARealEngine:
    """Legitimate input must still reach the database and land correctly."""

    @pytest.fixture
    def sqlite_db(self):
        from sqlalchemy import create_engine, text

        db = make_db()
        db.engine = create_engine("sqlite://")
        with db.engine.begin() as conn:
            conn.execute(
                text("CREATE TABLE analysis (ticker TEXT PRIMARY KEY, company TEXT)")
            )
        return db

    def _fetch(self, db, ticker):
        from sqlalchemy import text

        with db.engine.begin() as conn:
            return conn.execute(
                text("SELECT company FROM analysis WHERE ticker = :t"),
                {"t": ticker},
            ).scalar()

    def test_apostrophe_value_round_trips_intact(self, sqlite_db):
        df = pd.DataFrame([{"ticker": "OBR", "company": "O'Brien & Sons"}])
        sqlite_db.save_1_row_df_to_postgresql_db_using_primary_key(
            df, {"table_name": "analysis", "primary_key": "ticker"}
        )
        assert self._fetch(sqlite_db, "OBR") == "O'Brien & Sons"

    def test_injection_payload_is_stored_as_data_not_executed(self, sqlite_db):
        payload = "x'); DROP TABLE analysis; --"
        df = pd.DataFrame([{"ticker": "EVIL", "company": payload}])
        sqlite_db.save_1_row_df_to_postgresql_db_using_primary_key(
            df, {"table_name": "analysis", "primary_key": "ticker"}
        )
        assert self._fetch(sqlite_db, "EVIL") == payload

    def test_second_write_for_the_same_primary_key_updates_in_place(self, sqlite_db):
        cfg = {"table_name": "analysis", "primary_key": "ticker"}
        sqlite_db.save_1_row_df_to_postgresql_db_using_primary_key(
            pd.DataFrame([{"ticker": "ACME", "company": "Acme Corp"}]), cfg
        )
        sqlite_db.save_1_row_df_to_postgresql_db_using_primary_key(
            pd.DataFrame([{"ticker": "ACME", "company": "Acme Holdings"}]), cfg
        )
        assert self._fetch(sqlite_db, "ACME") == "Acme Holdings"

    def test_empty_dataframe_is_a_no_op_and_leaves_the_table_untouched(self, sqlite_db):
        from sqlalchemy import text

        sqlite_db.save_1_row_df_to_postgresql_db_using_primary_key(
            pd.DataFrame(columns=["ticker", "company"]),
            {"table_name": "analysis", "primary_key": "ticker"},
        )
        with sqlite_db.engine.begin() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM analysis")).scalar()
        assert count == 0


class TestCredentialsAreNotLeaked:
    def test_connection_failure_output_does_not_contain_the_password(
        self, monkeypatch, capsys
    ):
        db = make_db()

        def boom():
            # Mirrors a real driver error, which embeds the DSN.
            raise RuntimeError(
                f"could not connect: postgresql://svc_reader:{FAKE_PASSWORD}@db.example.internal:5432/analytics"
            )

        monkeypatch.setattr(db, "enable_connection_and_cursor", boom)
        db.set_up_db_connection({"password": FAKE_PASSWORD})
        assert FAKE_PASSWORD not in capsys.readouterr().out

    def test_connection_failure_emits_the_redacted_environment_line(
        self, monkeypatch, capsys
    ):
        db = make_db()

        def boom():
            raise RuntimeError("could not connect")

        monkeypatch.setattr(db, "enable_connection_and_cursor", boom)
        db.set_up_db_connection({"password": FAKE_PASSWORD})
        assert (
            "No connection for environment: server=db.example.internal, "
            "database=analytics, user=svc_reader (credentials redacted)"
            in capsys.readouterr().out
        )

    def test_connection_failure_still_reports_false_to_the_caller(self, monkeypatch):
        db = make_db()

        def boom():
            raise RuntimeError("could not connect")

        monkeypatch.setattr(db, "enable_connection_and_cursor", boom)
        assert db.set_up_db_connection({"password": FAKE_PASSWORD}) is False


class TestQueryLoggingDoesNotEchoValues:
    def test_executenodataquery_does_not_print_the_interpolated_statement(self, capsys):
        db = make_db()  # no engine attribute -> the execute path fails immediately
        db.executeNoDataQuery(
            "INSERT INTO analysis (ticker) VALUES ('SENTINEL-PAYROLL-VALUE')"
        )
        assert "SENTINEL-PAYROLL-VALUE" not in capsys.readouterr().out


class TestFormatTableStatisticsRaisesInsteadOfExiting:
    def test_missing_x_and_y_keys_raise_valueerror(self):
        with pytest.raises(ValueError):
            make_db().format_table_statistics_df(pd.DataFrame(), {"statistic": "mean"})

    def test_missing_x_and_y_keys_carry_the_original_message(self):
        with pytest.raises(ValueError) as excinfo:
            make_db().format_table_statistics_df(pd.DataFrame(), {"statistic": "mean"})
        assert str(excinfo.value) == (
            "Data not defined for formatting table statistics: "
            "data_set_cfg must contain both 'x' and 'y'"
        )

    def test_missing_x_and_y_keys_do_not_raise_systemexit(self):
        # SystemExit is a BaseException, so it would slip past the ValueError
        # check above; assert its absence explicitly.
        try:
            make_db().format_table_statistics_df(pd.DataFrame(), {"statistic": "mean"})
        except SystemExit:  # pragma: no cover - the defect being fixed
            raised_systemexit = True
        except ValueError:
            raised_systemexit = False
        assert raised_systemexit is False

    def test_present_x_and_y_keys_still_produce_a_dataframe(self):
        temp_df = pd.DataFrame(
            [
                {
                    "ColumnName": "pressure",
                    "ColumnDataType": "float",
                    "StartTime": "2026-01-01T00:00:00",
                    "mean": "1.5",
                }
            ]
        )
        result = make_db().format_table_statistics_df(
            temp_df, {"x": [], "y": ["pressure"], "statistic": "mean"}
        )
        assert result["pressure"].to_list() == [1.5]
