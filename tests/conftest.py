from __future__ import annotations

import os

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from claimcheck import config  # noqa: F401  (loads .env)
from claimcheck.data import Catalogue, load_answers, load_facts, load_gold
from claimcheck.db import init_schema


@pytest.fixture(scope="session")
def answers():
    return load_answers()


@pytest.fixture(scope="session")
def answers_by_id(answers):
    return {a.answer_id: a for a in answers}


@pytest.fixture(scope="session")
def catalogue():
    return Catalogue(load_facts())


@pytest.fixture(scope="session")
def gold():
    return load_gold()


@pytest.fixture(scope="session")
def test_db_url():
    """A dedicated, freshly reset PostgreSQL database for API/DB tests."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    dbname = conninfo_to_dict(url)["dbname"]
    admin_url = make_conninfo(url, dbname="postgres")
    try:
        with psycopg.connect(admin_url, autocommit=True, connect_timeout=5) as conn:
            exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)).fetchone()
            if not exists:
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    except psycopg.OperationalError as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS claim_results, answer_results, runs CASCADE")
    init_schema(url)
    return url
