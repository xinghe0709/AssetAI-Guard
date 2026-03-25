import tempfile
import unittest
import json
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
        uploads_dir = Path(cls._tmp_dir.name) / "ai_json_uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        TestConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path.as_posix()}"
        TestConfig.AI_JSON_UPLOADS_DIR = str(uploads_dir)

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
        health = self.client.get("/api/v1/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json(), {"status": "ok"})

        admin_token = self._login("admin@demo.com", "admin123")
        manager_token = self._login("manager@demo.com", "manager123")
        contractor_token = self._login("contractor@demo.com", "contractor123")

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

        loc_res = self.client.get(
            "/api/v1/locations/",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(loc_res.status_code, 200, loc_res.get_json())
        locations = loc_res.get_json()["data"]
        self.assertGreaterEqual(len(locations), 1)
        location_id = locations[0]["id"]
        location_name = locations[0]["name"]
        fuzzy_location_name = f"  {location_name.lower().replace(' ', '   ')}  "

        create_asset_ok = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "locationName": fuzzy_location_name,
                "name": "Test Asset A",
                "loadCapacities": [
                    {"name": "max point load", "metric": "kN", "maxLoad": 1000, "details": "outrigger"},
                    {"name": "max axle load", "metric": "t", "maxLoad": 80, "details": "vehicle"},
                    {"name": "max uniform distributor load", "metric": "kPa", "maxLoad": 40},
                    {"name": "max displacement size", "metric": "t", "maxLoad": 70000},
                ],
            },
        )
        self.assertEqual(create_asset_ok.status_code, 201, create_asset_ok.get_json())
        created_asset_id = create_asset_ok.get_json()["data"]["id"]
        self.assertEqual(create_asset_ok.get_json()["data"]["name"], "Test Asset A")

        duplicate_asset = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "locationName": fuzzy_location_name,
                "name": "Test Asset A",
                "loadCapacities": [
                    {"name": "max point load", "metric": "kN", "maxLoad": 1000}
                ],
            },
        )
        self.assertEqual(duplicate_asset.status_code, 409, duplicate_asset.get_json())

        list_assets = self.client.get(
            f"/api/v1/assets/?locationId={location_id}&page=1&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(list_assets.status_code, 200, list_assets.get_json())
        items = list_assets.get_json()["data"]["items"]
        self.assertTrue(any(a["name"] == "Test Asset A" for a in items))
        berth5 = next((a for a in items if a["name"] == "Berth 5"), None)
        self.assertIsNotNone(berth5)
        asset_id = berth5["id"]
        self.assertGreaterEqual(len(berth5["loadCapacities"]), 1)

        new_location_name = "Auto Created Test Wharf Zeta"
        create_asset_new_location = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "locationName": new_location_name,
                "name": "Test Asset New Location",
                "loadCapacities": [
                    {"name": "max point load", "metric": "kN", "maxLoad": 150}
                ],
            },
        )
        self.assertEqual(create_asset_new_location.status_code, 201, create_asset_new_location.get_json())

        updated_locations_res = self.client.get(
            "/api/v1/locations/",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(updated_locations_res.status_code, 200, updated_locations_res.get_json())
        updated_locations = updated_locations_res.get_json()["data"]
        created_location = next((loc for loc in updated_locations if loc["name"] == new_location_name), None)
        self.assertIsNotNone(created_location)

        new_location_assets = self.client.get(
            f"/api/v1/assets/?locationId={created_location['id']}&page=1&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(new_location_assets.status_code, 200, new_location_assets.get_json())
        self.assertTrue(
            any(a["name"] == "Test Asset New Location" for a in new_location_assets.get_json()["data"]["items"])
        )

        all_assets = self.client.get(
            "/api/v1/assets/all?page=1&pageSize=50",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(all_assets.status_code, 200, all_assets.get_json())
        all_items = all_assets.get_json()["data"]["items"]
        self.assertTrue(any(a["name"] == "Berth 5" for a in all_items))
        self.assertTrue(any(a["name"] == "Test Asset A" for a in all_items))

        list_caps = self.client.get(
            f"/api/v1/assets/{asset_id}/load-capacities",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        self.assertEqual(list_caps.status_code, 200, list_caps.get_json())
        self.assertEqual(list_caps.get_json()["data"]["asset"]["name"], "Berth 5")
        caps = list_caps.get_json()["data"]["items"]
        self.assertGreaterEqual(len(caps), 1)
        first_cap_id = caps[0]["id"]

        create_cap = self.client.post(
            f"/api/v1/assets/{asset_id}/load-capacities",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"name": "max point load", "metric": "t", "maxLoad": 800, "details": "temp cap"},
        )
        self.assertEqual(create_cap.status_code, 201, create_cap.get_json())
        self.assertEqual(create_cap.get_json()["data"]["asset"]["name"], "Berth 5")
        created_cap = create_cap.get_json()["data"]["capacity"]
        created_cap_id = created_cap["id"]
        self.assertEqual(created_cap["name"], "max point load")

        update_cap = self.client.put(
            f"/api/v1/assets/{asset_id}/load-capacities/{created_cap_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"maxLoad": 850, "details": "updated"},
        )
        self.assertEqual(update_cap.status_code, 200, update_cap.get_json())
        self.assertEqual(update_cap.get_json()["data"]["asset"]["name"], "Berth 5")
        self.assertEqual(update_cap.get_json()["data"]["capacity"]["maxLoad"], 850.0)

        delete_cap = self.client.delete(
            f"/api/v1/assets/{asset_id}/load-capacities/{created_cap_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        self.assertEqual(delete_cap.status_code, 200, delete_cap.get_json())
        self.assertTrue(delete_cap.get_json()["data"]["deleted"])

        forbidden_caps = self.client.get(
            f"/api/v1/assets/{asset_id}/load-capacities",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(forbidden_caps.status_code, 403, forbidden_caps.get_json())

        opt = self.client.get(
            "/api/v1/evaluations/equipment-options",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(opt.status_code, 200, opt.get_json())
        self.assertGreaterEqual(len(opt.get_json()["data"]), 6)

        eval_res = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationId": location_id,
                "assetId": asset_id,
                "equipment": "Crane with outriggers",
                "equipmentModel": "Test crane",
                "loadParameterValue": 500,
                "remark": "Pre-lift check",
            },
        )
        self.assertEqual(eval_res.status_code, 200, eval_res.get_json())
        eval_data = eval_res.get_json()["data"]
        self.assertEqual(eval_data["status"], "Compliant")
        self.assertEqual(eval_data["loadParameterMetric"], "kN")
        self.assertEqual(eval_data["remark"], "Pre-lift check")

        eval_non = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationId": location_id,
                "assetId": asset_id,
                "equipment": "Crane with outriggers",
                "equipmentModel": "Test crane",
                "loadParameterValue": 5000,
                "remark": "Overload case",
            },
        )
        self.assertEqual(eval_non.status_code, 200, eval_non.get_json())
        self.assertEqual(eval_non.get_json()["data"]["status"], "Non-Compliant")

        eval_storage_ok = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationId": location_id,
                "assetId": asset_id,
                "equipment": "Storage Load",
                "loadParameterValue": 35,
                "remark": "Storage compliant",
            },
        )
        self.assertEqual(eval_storage_ok.status_code, 200, eval_storage_ok.get_json())
        self.assertEqual(eval_storage_ok.get_json()["data"]["status"], "Compliant")
        self.assertEqual(eval_storage_ok.get_json()["data"]["loadParameterMetric"], "kPa")

        eval_storage_non = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationId": location_id,
                "assetId": asset_id,
                "equipment": "Storage Load",
                "loadParameterValue": 55,
            },
        )
        self.assertEqual(eval_storage_non.status_code, 200, eval_storage_non.get_json())
        self.assertEqual(eval_storage_non.get_json()["data"]["status"], "Non-Compliant")

        eval_vessel_ok = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationId": location_id,
                "assetId": asset_id,
                "equipment": "Vessel",
                "loadParameterValue": 68000,
            },
        )
        self.assertEqual(eval_vessel_ok.status_code, 200, eval_vessel_ok.get_json())
        self.assertEqual(eval_vessel_ok.get_json()["data"]["status"], "Compliant")
        self.assertEqual(eval_vessel_ok.get_json()["data"]["loadParameterMetric"], "t")

        wrong_location_eval = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationId": location_id + 999,
                "assetId": asset_id,
                "equipment": "Crane with outriggers",
                "loadParameterValue": 100,
            },
        )
        self.assertEqual(wrong_location_eval.status_code, 400, wrong_location_eval.get_json())

        hist = self.client.get(
            "/api/v1/evaluations/history?page=1&pageSize=20",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        self.assertEqual(hist.status_code, 200, hist.get_json())
        hist_items = hist.get_json()["data"]["items"]
        self.assertGreaterEqual(len(hist_items), 1)
        self.assertIn("loadParameterMetric", hist_items[0])
        self.assertIn("matchedCapacityName", hist_items[0])

        contractor_hist = self.client.get(
            "/api/v1/evaluations/history?page=1&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(contractor_hist.status_code, 403, contractor_hist.get_json())

        forbidden_asset = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationName": location_name,
                "name": "Should Fail",
                "loadCapacities": [{"name": "max point load", "metric": "kN", "maxLoad": 1}],
            },
        )
        self.assertEqual(forbidden_asset.status_code, 403, forbidden_asset.get_json())

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

        bad_metric = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "locationName": location_name,
                "name": "Bad Metric Asset",
                "loadCapacities": [{"name": "max point load", "metric": "grams", "maxLoad": 1}],
            },
        )
        self.assertEqual(bad_metric.status_code, 400, bad_metric.get_json())

        bad_capacity_name = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "locationName": location_name,
                "name": "Bad Capacity Name Asset",
                "loadCapacities": [{"name": "custom load", "metric": "kN", "maxLoad": 1}],
            },
        )
        self.assertEqual(bad_capacity_name.status_code, 400, bad_capacity_name.get_json())

        duplicate_cap_in_batch = self.client.post(
            "/api/v1/assets/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "locationName": location_name,
                "name": "Dup Cap Asset",
                "loadCapacities": [
                    {"name": "max point load", "metric": "kN", "maxLoad": 100},
                    {"name": "max point load", "metric": "kN", "maxLoad": 200},
                ],
            },
        )
        self.assertEqual(duplicate_cap_in_batch.status_code, 409, duplicate_cap_in_batch.get_json())
        self.assertEqual(duplicate_cap_in_batch.get_json()["code"], "duplicate_capacity")

        duplicate_cap_single = self.client.post(
            f"/api/v1/assets/{asset_id}/load-capacities",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"name": "max point load", "metric": "kN", "maxLoad": 999},
        )
        self.assertEqual(duplicate_cap_single.status_code, 409, duplicate_cap_single.get_json())
        self.assertEqual(duplicate_cap_single.get_json()["code"], "duplicate_capacity")

        bad_metric_capacity_create = self.client.post(
            f"/api/v1/assets/{created_asset_id}/load-capacities",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={
                "name": "max point load",
                "metric": "kg",
                "maxLoad": 10,
            },
        )
        self.assertEqual(bad_metric_capacity_create.status_code, 400, bad_metric_capacity_create.get_json())

        bad_capacity_update = self.client.put(
            f"/api/v1/assets/{asset_id}/load-capacities/{first_cap_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"name": "custom load"},
        )
        self.assertEqual(bad_capacity_update.status_code, 400, bad_capacity_update.get_json())

        missing_load = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={"locationId": location_id, "assetId": asset_id, "equipment": "Crane with outriggers"},
        )
        self.assertEqual(missing_load.status_code, 400, missing_load.get_json())

        bad_equipment = self.client.post(
            "/api/v1/evaluations/check",
            headers={"Authorization": f"Bearer {contractor_token}"},
            json={
                "locationId": location_id,
                "assetId": asset_id,
                "equipment": "Not a real equipment",
                "loadParameterValue": 100,
            },
        )
        self.assertEqual(bad_equipment.status_code, 400, bad_equipment.get_json())

        no_loc = self.client.get(
            "/api/v1/assets/?page=1&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(no_loc.status_code, 400, no_loc.get_json())

        bad_page = self.client.get(
            f"/api/v1/assets/?locationId={location_id}&page=0&pageSize=20",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        self.assertEqual(bad_page.status_code, 400, bad_page.get_json())

    def test_import_json_uploads(self):
        admin_token = self._login("admin@demo.com", "admin123")
        manager_token = self._login("manager@demo.com", "manager123")
        contractor_token = self._login("contractor@demo.com", "contractor123")

        locations = self.client.get(
            "/api/v1/locations/",
            headers={"Authorization": f"Bearer {contractor_token}"},
        ).get_json()["data"]
        location_name = locations[0]["name"]

        uploads_dir = Path(self.app.config["AI_JSON_UPLOADS_DIR"])
        for file_path in uploads_dir.glob("*.json"):
            file_path.unlink()

        valid_path = uploads_dir / "01_design_criteria_asset_payload_valid.json"
        duplicate_path = uploads_dir / "02_design_criteria_asset_payload_duplicate.json"
        invalid_path = uploads_dir / "03_misc_invalid.json"

        valid_payload = {
            "locationName": location_name,
            "name": "Imported From Uploads A",
            "loadCapacities": [{"name": "max point load", "metric": "kN", "maxLoad": 321}],
        }
        duplicate_payload = {
            "locationName": location_name,
            "name": "Imported From Uploads A",
            "loadCapacities": [{"name": "max point load", "metric": "kN", "maxLoad": 321}],
        }

        valid_path.write_text(json.dumps(valid_payload), encoding="utf-8")
        duplicate_path.write_text(json.dumps(duplicate_payload), encoding="utf-8")
        invalid_path.write_text('{"foo": "bar"}', encoding="utf-8")

        forbidden_import_res = self.client.post(
            "/api/v1/assets/import-json-uploads",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={},
        )
        self.assertEqual(forbidden_import_res.status_code, 403, forbidden_import_res.get_json())

        import_res = self.client.post(
            "/api/v1/assets/import-json-uploads",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )
        self.assertEqual(import_res.status_code, 201, import_res.get_json())
        import_data = import_res.get_json()["data"]
        self.assertEqual(import_data["filesScanned"], 3)
        self.assertEqual(import_data["createdCount"], 1)
        self.assertEqual(import_data["rejectedCount"], 2)
        self.assertTrue(any(item["file"] == valid_path.name for item in import_data["items"]))
        self.assertTrue(any(item["reason"] == "asset_already_exists" for item in import_data["rejected"]))
        self.assertTrue(any(item["reason"] == "invalid_asset_payload" for item in import_data["rejected"]))

if __name__ == "__main__":
    unittest.main()
