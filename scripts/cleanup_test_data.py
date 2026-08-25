"""Clean up test/mock regulation versions from the database."""

from __future__ import annotations

import sys
from sqlalchemy import create_engine, text
from app.core.config import get_settings


def preview_and_cleanup(dry_run: bool = True) -> None:
    engine = create_engine(get_settings().database_url)
    
    with engine.begin() as conn:
        # Find versions starting with test- or itest-
        versions = conn.execute(
            text(
                """
                SELECT rv.id, rv.version, r.title, COUNT(c.id) as clause_count
                FROM regulation_versions rv
                JOIN regulations r ON rv.regulation_id = r.id
                LEFT JOIN clauses c ON c.version_id = rv.id
                WHERE rv.version LIKE 'test-%' OR rv.version LIKE 'itest-%'
                GROUP BY rv.id, rv.version, r.title;
                """
            )
        ).mappings().all()

        if not versions:
            print("No test/mock regulation versions found to clean up.")
            return

        print(f"Found {len(versions)} test/mock regulation version(s):")
        total_clauses = 0
        for v in versions:
            print(f" - Version ID: {v['id']} | Label: {v['version']} | Regulation: {v['title']} | Clauses: {v['clause_count']}")
            total_clauses += v['clause_count']

        if dry_run:
            print(f"\n[DRY RUN] Would delete {len(versions)} versions and {total_clauses} clauses.")
            print("To execute the deletion, run this script with the '--execute' flag.")
            return

        print(f"\nDeleting {len(versions)} versions and {total_clauses} clauses...")
        
        # Delete clauses, versions, regulations, and regulators
        # First, delete clauses associated with these versions
        conn.execute(
            text(
                """
                DELETE FROM clauses
                WHERE version_id IN (
                    SELECT id FROM regulation_versions
                    WHERE version LIKE 'test-%' OR version LIKE 'itest-%'
                );
                """
            )
        )
        
        # Delete regulation versions
        conn.execute(
            text(
                """
                DELETE FROM regulation_versions
                WHERE version LIKE 'test-%' OR version LIKE 'itest-%';
                """
            )
        )

        # Delete regulations that have no versions left
        conn.execute(
            text(
                """
                DELETE FROM regulations
                WHERE id NOT IN (SELECT DISTINCT regulation_id FROM regulation_versions);
                """
            )
        )

        # Delete regulators that have no regulations left (excluding seeded ones if they have regulations)
        conn.execute(
            text(
                """
                DELETE FROM regulators
                WHERE code NOT IN (SELECT DISTINCT regulator_code FROM regulations);
                """
            )
        )

        print("Cleanup completed successfully.")


if __name__ == "__main__":
    execute_flag = "--execute" in sys.argv
    preview_and_cleanup(dry_run=not execute_flag)
