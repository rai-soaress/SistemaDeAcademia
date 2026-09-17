import os
import subprocess
import sys
import unittest


class DeployConfigTests(unittest.TestCase):
    def run_config(self, code, **settings):
        env = os.environ.copy()
        for key in ("DATABASE_URL", "SECRET_KEY", "APP_ENV", "RENDER", "VERCEL", "INSTANCE_PATH"):
            env.pop(key, None)
        env.update(PYTHON_DOTENV_DISABLED="1", **settings)
        return subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)

    def test_local_sqlite(self):
        result = self.run_config("from config import Config; assert Config.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///'); assert Config.AUTO_INIT_DB")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_production_requires_postgres_and_secret(self):
        for settings in ({}, {"DATABASE_URL": "sqlite:///local.db"}, {"DATABASE_URL": "postgres://user:pass@localhost/db"}):
            result = self.run_config("import config", APP_ENV="production", **settings)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RuntimeError", result.stderr)

    def test_postgres_urls_and_serverless_pool(self):
        for prefix in ("postgres://", "postgresql://", "postgresql+psycopg://"):
            result = self.run_config(
                "from config import Config; from sqlalchemy.pool import NullPool; "
                "assert Config.SQLALCHEMY_DATABASE_URI == 'postgresql+psycopg://user:pass@localhost/db?sslmode=require'; "
                "assert Config.SQLALCHEMY_ENGINE_OPTIONS['poolclass'] is NullPool; "
                "assert not Config.AUTO_INIT_DB; assert Config.SESSION_COOKIE_SECURE",
                VERCEL="1", SECRET_KEY="test-only-secret", DATABASE_URL=prefix + "user:pass@localhost/db?sslmode=require",
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_is_repeatable_and_preserves_records(self):
        result = self.run_config(
            "from config import Config; Config.SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'; Config.AUTO_INIT_DB=False; "
            "from app import app; from extensions import db; from sqlalchemy import inspect; "
            "from models.usuario import Usuario; runner=app.test_cli_runner(); "
            "assert runner.invoke(args=['init-db']).exit_code == 0; "
            "ctx=app.app_context(); ctx.push(); "
            "assert set(inspect(db.engine).get_table_names()) == set(db.metadata.tables); "
            "db.session.add(Usuario(nome='Teste',email='teste@example.com',senha='hash-teste')); db.session.commit(); "
            "assert runner.invoke(args=['init-db']).exit_code == 0; "
            "assert Usuario.query.count() == 1; "
            "assert app.test_client().get('/login').status_code == 200; ctx.pop()"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_production_import_does_not_connect_or_change_schema(self):
        result = self.run_config(
            "from app import app; from extensions import db; from sqlalchemy.schema import CreateTable; "
            "ctx=app.app_context(); ctx.push(); assert db.engine.dialect.name == 'postgresql'; "
            "assert db.engine.dialect.driver == 'psycopg'; "
            "[str(CreateTable(table).compile(dialect=db.engine.dialect)) for table in db.metadata.sorted_tables]; "
            "assert app.test_client().get('/login').status_code == 200; ctx.pop()",
            VERCEL="1", SECRET_KEY="test-only-secret",
            DATABASE_URL="postgres://user:pass@127.0.0.1:1/test?sslmode=require",
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
