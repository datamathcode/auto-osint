"""
Migration script to migrate evidence entries from raw string storage to structured
storage with confidence quantification.

This script migrates existing evidence entries by converting claim strings to
structured claims with confidence metadata.

Usage:
    python -m src.python.migrations.migrate_evidence_to_confidence
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.evidence import Evidence


class EvidenceMigration:
    """Migrate evidence entries from raw strings to structured storage."""
    
    def __init__(self, db_session):
        """
        Initialize migration.
        
        Args:
            db_session: SQLAlchemy session or ORM instance
        """
        self.session = db_session
    
    def migrate_evidence(
        self,
        confidence_module = None,
    ) -> Dict[str, int]:
        """
        Migrate all evidence entries to structured format.
        
        Args:
            confidence_module: Optional confidence quantification module for
                              automated confidence calculation
            
        Returns:
            Dict with migration stats
        """
        print("=" * 60)
        print("EVIDENCE MIGRATION: Raw Strings to Structured Storage")
        print("=" * 60)
        
        # Get all evidence entries
        evidence_list = self.session.query(Evidence).all()
        total_count = len(evidence_list)
        
        if total_count == 0:
            print("No evidence entries found. Nothing to migrate.")
            return {"total": 0, "success": 0, "skipped": 0, "failed": 0}
        
        print(f"\nFound {total_count} evidence entries to migrate.\n")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for idx, evidence in enumerate(evidence_list, 1):
            print(f"[{idx}/{total_count}] Migrating evidence ID {evidence.id}")
            
            try:
                # Check if already structured
                if self._is_structured(evidence):
                    print(f"  ⏭️  Evidence ID {evidence.id} is already structured. Skipping.")
                    skipped_count += 1
                    continue
                
                # If confidence is already set, use it
                if evidence.confidence and evidence.confidence > 0:
                    print(f"  ✓ Using existing confidence: {evidence.confidence}")
                else:
                    # Calculate confidence if module provided
                    if confidence_module:
                        print(f"  📊 Calculating confidence for: {evidence.claim[:50]}...")
                        confidence_score = confidence_module.quantify_confidence(
                            prior_probability=0.5,
                            likelihood=0.7,
                            evidence=evidence.claim
                        )
                        evidence.confidence = confidence_score
                        
                        # Update independence score
                        independence_score = confidence_module.calculate_independence_score(
                            financial_interest=False,
                            organizational_tie=False,
                            personal_relationship=False,
                            promotional_purpose=False
                        )
                        evidence.independence_score = independence_score
                        
                        print(f"  ✓ Confidence calculated: {confidence_score:.2f}")
                    else:
                        print("  ⚠️  No confidence module provided. Defaulting to 0.5")
                        evidence.confidence = 0.5
                        evidence.independence_score = 0.5
                
                # Ensure independence check details exist
                if evidence.independence_check_details is None:
                    evidence.independence_check_details = {
                        "financial_interest": False,
                        "organizational_tie": False,
                        "personal_relationship": False,
                        "promotional_purpose": False,
                        "migration_note": "Migrated from raw string storage",
                        "migrated_at": datetime.utcnow().isoformat()
                    }
                
                # Mark as migrated. Assign a new list: in-place mutation of a
                # JSON column is not tracked by SQLAlchemy, so the append alone
                # would never be persisted.
                custody = list(evidence.chain_of_custody or [])
                custody.append({
                    "action": "migration_to_confidence",
                    "timestamp": datetime.utcnow().isoformat(),
                    "migration_version": "1.0"
                })
                evidence.chain_of_custody = custody
                
                self.session.commit()
                success_count += 1
                print(f"  ✅ Successfully migrated evidence ID {evidence.id}\n")
                
            except Exception as e:
                print(f"  ❌ Failed to migrate evidence ID {evidence.id}: {e}\n")
                self.session.rollback()
                failed_count += 1
        
        # Print summary
        print("=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total entries: {total_count}")
        print(f"✅ Successfully migrated: {success_count}")
        print(f"⏭️  Skipped (already structured): {skipped_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"Success rate: {success_count / total_count * 100:.1f}%")
        print("=" * 60)
        
        return {
            "total": total_count,
            "success": success_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "success_rate": success_count / total_count * 100 if total_count > 0 else 0
        }
    
    def _is_structured(self, evidence: Evidence) -> bool:
        """
        Check if evidence entry has structured storage.
        
        Args:
            evidence: Evidence entry
            
        Returns:
            True if entry is structured, False otherwise
        """
        # Entry is structured if confidence and independence_score are set
        if evidence.confidence is None or evidence.confidence <= 0:
            return False
        
        if evidence.independence_score is None or evidence.independence_score <= 0:
            return False
        
        # Check if independence check details exist
        if evidence.independence_check_details is None:
            return False
        
        return True
    
    def verify_migration(self) -> Dict[str, int]:
        """
        Verify migration by checking evidence entries.
        
        Returns:
            Dict with verification stats
        """
        print("\n" + "=" * 60)
        print("VERIFICATION: Checking Evidence Entries")
        print("=" * 60)
        
        all_evidence = self.session.query(Evidence).all()
        total = len(all_evidence)
        structured = 0
        unstructured = 0
        
        for evidence in all_evidence:
            if self._is_structured(evidence):
                structured += 1
            else:
                unstructured += 1
        
        print(f"\nTotal entries: {total}")
        print(f"✅ Structured: {structured} ({structured / total * 100:.1f}%)")
        print(f"❌ Unstructured: {unstructured} ({unstructured / total * 100:.1f}%)")
        print("=" * 60)
        
        return {
            "total": total,
            "structured": structured,
            "unstructured": unstructured,
            "structured_rate": structured / total * 100 if total > 0 else 0
        }


def transfer_evidence(
    source_url: str,
    target_url: str,
    run_migration: bool = True,
) -> Dict[str, Any]:
    """
    Copy an investigation's evidence from one database to another.

    This is the database-to-database step: rows are read from the source
    engine, copied into the target schema (created if missing), and then
    optionally migrated to structured confidence storage in place.

    Args:
        source_url: SQLAlchemy URL to copy from (e.g. sqlite:///old.db)
        target_url: SQLAlchemy URL to copy to (e.g. postgresql://...)
        run_migration: Run the confidence migration on the target after copy

    Returns:
        Dict with investigation/evidence counts plus migration stats
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from ..database import init_db
    from ..models.investigation import Investigation

    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)
    init_db(target_engine)

    SourceSession = sessionmaker(bind=source_engine, expire_on_commit=False)
    TargetSession = sessionmaker(bind=target_engine, expire_on_commit=False)

    investigations_copied = 0
    evidence_copied = 0

    with SourceSession() as source, TargetSession() as target:
        source_investigations = source.query(Investigation).all()

        id_map: Dict[int, int] = {}
        for row in source_investigations:
            copied = Investigation(
                target_name=row.target_name,
                target_id=row.target_id,
                claim_under_investigation=row.claim_under_investigation,
                status=row.status,
                stages_completed=row.stages_completed,
                total_sources=row.total_sources,
                corroborated_sources=row.corroborated_sources,
                contradictory_sources=row.contradictory_sources,
                net_confidence_score=row.net_confidence_score,
                investigation_notes=row.investigation_notes,
                playbook_update=row.playbook_update,
                created_at=row.created_at,
                completed_at=row.completed_at,
            )
            target.add(copied)
            target.flush()
            id_map[row.id] = copied.id
            investigations_copied += 1

        for row in source.query(Evidence).all():
            target.add(
                Evidence(
                    source=row.source,
                    timestamp=row.timestamp,
                    claim=row.claim,
                    confidence=row.confidence,
                    independence_score=row.independence_score,
                    independence_check_details=row.independence_check_details,
                    corroborating_sources=row.corroborating_sources or [],
                    contradictions=row.contradictions or [],
                    links=row.links or [],
                    chain_of_custody=row.chain_of_custody or [],
                    investigation_id=id_map.get(row.investigation_id, row.investigation_id),
                )
            )
            evidence_copied += 1

        target.commit()

    result: Dict[str, Any] = {
        "investigations_copied": investigations_copied,
        "evidence_copied": evidence_copied,
    }

    if run_migration and evidence_copied:
        with TargetSession() as target:
            migration = EvidenceMigration(target)
            result["migration"] = migration.migrate_evidence()
            result["verification"] = migration.verify_migration()

    return result


def main(argv: Optional[List[str]] = None) -> int:
    """Copy and migrate evidence, or report how to call migrate_evidence()."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="migrate-evidence",
        description="Copy evidence between databases and migrate it to structured storage.",
    )
    parser.add_argument("--source-url", help="Database URL to copy from")
    parser.add_argument("--target-url", help="Database URL to copy to")
    parser.add_argument(
        "--no-migrate",
        action="store_true",
        help="Copy rows only; skip the confidence migration on the target",
    )
    args = parser.parse_args(argv)

    if not args.source_url or not args.target_url:
        parser.print_help()
        print("\nGive --source-url and --target-url to copy and migrate evidence.")
        return 2

    stats = transfer_evidence(
        args.source_url, args.target_url, run_migration=not args.no_migrate
    )
    print(json.dumps(stats, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
