import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.config import Config
from app.extensions import db


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    TOKEN_EXPIRES_SECONDS = 3600


class ApiFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        db_path = Path(cls._tmp_dir.name) / "api_flow_test.db"
        TestConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path.as_posix()}"

        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()

        cli = cls.app.test_cli_runner()
        seed_result = cli.invoke(args=["seed"])
        if seed_result.exit_code != 0:
            raise RuntimeError(f"seed failed: {seed_result.output}")

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self, email: str, password: str) -> str:
        res = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(res.status_code, 200, res.get_json())
        payload = res.get_json()
        self.assertTrue(payload["success"])
        return payload["data"]["token"]

    def test_full_api_flow(self):
        # 1) health
        health = self.client.get("/api/v1/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json(), {"status": "ok"})

        # 2) login by 3 roles
        admin_token = self._login("admin@demo.com", "admin123")
        manager_token = self._login("manager@demo.com", "manager123")
        contractor_token = self._login("contractor@demo.com", "contractor123")

        # 3) admin creates a user
        create_user = self.client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "contractor2@demo.com",
                "password": "contractor456",
                "role": "Contractors",
            },
        )
        self.assertEqual(create_user.status_code, 201, create_user.get_json())
        self.assertTrue(create_user.get_json()["success"])

        # 4) manager creates an asset (English unit only)
        create_asset = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "assetName": "Crane A1",
                "maxLoadCapacity": 10,
                "equipmentType": "Crane",
                "unit": "ton",
                "sourceFile": "manual",
            },
        )
        self.assertEqual(create_asset.status_code, 201, create_asset.get_json())
        asset_payload = create_asset.get_json()["data"]
        asset_id = asset_payload["id"]
        self.assertEqual(asset_payload["unit"], "ton")

        # 5) asset list with contractor token
        list_assets = self.client.get(
            "/api/v1/assets/?page=1&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(list_assets.status_code, 200, list_assets.get_json())
        self.assertTrue(list_assets.get_json()["success"])

        # 6) evaluation check with unit conversion + remark
        eval_res = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "assetId": asset_id,
                "plannedLoad": 9500,
                "evaluationUnit": "kg",
                "remark": "Pre-lift check",
            },
        )
        self.assertEqual(eval_res.status_code, 200, eval_res.get_json())
        eval_data = eval_res.get_json()["data"]
        self.assertIn(eval_data["status"], {"Compliant", "Non-Compliant"})
        self.assertEqual(eval_data["evaluationUnit"], "kg")
        self.assertEqual(eval_data["remark"], "Pre-lift check")

        # 7) evaluation history
        hist = self.client.get(
            "/api/v1/evaluations/history?page=1&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(hist.status_code, 200, hist.get_json())
        items = hist.get_json()["data"]["items"]
        self.assertGreaterEqual(len(items), 1)
        self.assertIn("submittedUnit", items[0])
        self.assertIn("remark", items[0])

        # 8) RBAC: contractor cannot create asset
        forbidden_asset = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={"assetName": "Should Fail", "maxLoadCapacity": 1},
        )
        self.assertEqual(forbidden_asset.status_code, 403, forbidden_asset.get_json())

        # 9) RBAC: contractor cannot create user
        forbidden_user = self.client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "email": "x@demo.com",
                "password": "123456",
                "role": "Contractors",
            },
        )
        self.assertEqual(forbidden_user.status_code, 403, forbidden_user.get_json())

        # 10) validation: invalid asset unit must fail
        invalid_unit = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"assetName": "Bad Unit", "maxLoadCapacity": 1, "unit": "grams"},
        )
        self.assertEqual(invalid_unit.status_code, 400, invalid_unit.get_json())

        # 11) validation: missing evaluationUnit
        missing_eval_unit = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={"assetId": asset_id, "plannedLoad": 100},
        )
        self.assertEqual(missing_eval_unit.status_code, 400, missing_eval_unit.get_json())

        # 12) validation: unsupported evaluation unit
        bad_eval_unit = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={"assetId": asset_id, "plannedLoad": 100, "evaluationUnit": "kN"},
        )
        self.assertEqual(bad_eval_unit.status_code, 400, bad_eval_unit.get_json())

        # 13) validation: invalid pagination
        bad_page = self.client.get(
            "/api/v1/assets/?page=0&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(bad_page.status_code, 400, bad_page.get_json())

        # 14) placeholder endpoint
        bulk_import = self.client.post(
            "/api/v1/assets/bulk-import",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        self.assertEqual(bulk_import.status_code, 501, bulk_import.get_json())


if __name__ == "__main__":
    unittest.main()
