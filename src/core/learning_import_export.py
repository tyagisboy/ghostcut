import os
import json

class LearningImportExport:
    """
    Handles portable JSON database imports and exports.
    Automatically scrubs absolute file paths during export to guarantee user privacy.
    """
    def __init__(self, db_path="learning_db.json", failure_path="failure_db.json"):
        self.db_path = db_path
        self.failure_path = failure_path

    def export_database(self, export_path: str) -> bool:
        """
        Gathers records, scrubs personal file paths, and saves to export_path.
        """
        export_data = {
            "recipes": [],
            "failures": []
        }

        # 1. Gather recipes
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    recipes = json.load(f)
                    for r in recipes:
                        # Scrub absolute path (replace with generic base name)
                        r_copy = dict(r)
                        if "file_path" in r_copy:
                            r_copy["file_path"] = os.path.basename(r_copy["file_path"])
                        export_data["recipes"].append(r_copy)
            except Exception as e:
                print(f"[-] Export recipes fail: {e}")

        # 2. Gather failures
        if os.path.exists(self.failure_path):
            try:
                with open(self.failure_path, "r", encoding="utf-8") as f:
                    export_data["failures"] = json.load(f)
            except Exception as e:
                print(f"[-] Export failures fail: {e}")

        # Write out
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4)
            return True
        except Exception as e:
            print(f"[-] Failed to write export database: {e}")
        return False

    def import_database(self, import_path: str) -> bool:
        """
        Merges imported JSON records into the local databases.
        """
        if not os.path.exists(import_path):
            return False

        try:
            with open(import_path, "r", encoding="utf-8") as f:
                imported = json.load(f)
        except Exception as e:
            print(f"[-] Failed to read import database: {e}")
            return False

        # 1. Merge recipes
        recipes_merged = 0
        if "recipes" in imported:
            local_recipes = []
            if os.path.exists(self.db_path):
                try:
                    with open(self.db_path, "r", encoding="utf-8") as f:
                        local_recipes = json.load(f)
                except Exception:
                    pass
            
            # Find unique additions
            existing_paths = {os.path.basename(r.get("file_path", "")) for r in local_recipes}
            for rec in imported["recipes"]:
                base = os.path.basename(rec.get("file_path", ""))
                if base not in existing_paths:
                    local_recipes.append(rec)
                    recipes_merged += 1

            try:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(local_recipes, f, indent=4)
            except Exception as e:
                print(f"[-] Fail to save merged recipes: {e}")

        # 2. Merge failures
        failures_merged = 0
        if "failures" in imported:
            local_failures = []
            if os.path.exists(self.failure_path):
                try:
                    with open(self.failure_path, "r", encoding="utf-8") as f:
                        local_failures = json.load(f)
                except Exception:
                    pass

            for fail in imported["failures"]:
                if fail not in local_failures:
                    local_failures.append(fail)
                    failures_merged += 1

            try:
                with open(self.failure_path, "w", encoding="utf-8") as f:
                    json.dump(local_failures, f, indent=4)
            except Exception as e:
                print(f"[-] Fail to save merged failures: {e}")

        print(f"[OK] Database imported. Merged {recipes_merged} recipes and {failures_merged} failures.")
        return True
