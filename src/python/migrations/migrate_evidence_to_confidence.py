"""
Migration script to migrate evidence entries from raw string storage to structured
storage with confidence quantification.

This script migrates existing evidence entries by converting claim strings to
structured claims with confidence metadata.

Usage:
    python src/python/migrations/migrate_evidence_to_confidence.py
"""

import sys
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '..')

from models.evidence import Evidence


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
            return {"total": 0, "success": 0, "failed": 0}
        
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
                if evidence.confidence > 0:
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
                        print(f"  ⚠️  No confidence module provided. Defaulting to 0.5")
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
                
                # Mark as migrated
                evidence.chain_of_custody.append({
                    "action": "migration_to_confidence",
                    "timestamp": datetime.utcnow().isoformat(),
                    "migration_version": "1.0"
                })
                
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


def main():
    """Main migration entry point."""
    print("\n⚠️  This migration script requires a SQLAlchemy session to be provided.")
    print("    It should be run as part of the application setup, not as a standalone script.")
    print()
    
    # Example usage (requires actual database connection):
    # from src.python.main import app
    # with app.app_context():
    #     from sqlalchemy.orm import sessionmaker
    #     Session = sessionmaker(bind=app.db)
    #     session = Session()
    #     
    #     migration = EvidenceMigration(session)
    #     stats = migration.migrate_evidence()
    #     stats = migration.verify_migration()
    
    sys.exit(0)


if __name__ == "__main__":
    main()
