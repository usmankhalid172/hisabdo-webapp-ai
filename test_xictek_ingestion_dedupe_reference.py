import unittest

from xictek_ingestion_dedupe_reference import (
    Chunk,
    build_chunk_records,
    canonicalize_url,
    plan_source_sync,
)


class CanonicalUrlTests(unittest.TestCase):
    def test_removes_tracking_and_fragment_and_normalizes_host(self) -> None:
        self.assertEqual(
            canonicalize_url(
                "HTTPS://WWW.XICTEKSYSTEMS.COM/services/?utm_source=mail#top"
            ),
            "https://www.xicteksystems.com/services",
        )

    def test_rejects_out_of_scope_host(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize_url("https://example.org/page")


class ChunkIdentityTests(unittest.TestCase):
    def test_reingestion_produces_same_chunk_id(self) -> None:
        chunks = [Chunk("Services > Web", "Build useful web products.")]
        first = build_chunk_records(
            namespace="xictek-public",
            canonical_url="https://xicteksystems.com/services/web-development",
            chunks=chunks,
        )
        second = build_chunk_records(
            namespace="xictek-public",
            canonical_url="https://www.xicteksystems.com/services/web-development/",
            chunks=chunks,
        )
        self.assertEqual(first[0].chunk_id, second[0].chunk_id)

    def test_suppresses_exact_duplicate_chunks_in_same_section(self) -> None:
        records = build_chunk_records(
            namespace="xictek-public",
            canonical_url="https://www.xicteksystems.com/services",
            chunks=[
                Chunk("Services", "Cloud services help teams."),
                Chunk("Services", "Cloud   services help teams."),
            ],
        )
        self.assertEqual(len(records), 1)

    def test_dry_run_retires_only_after_current_generation_is_known(self) -> None:
        current = build_chunk_records(
            namespace="xictek-public",
            canonical_url="https://www.xicteksystems.com/services",
            chunks=[Chunk("Services", "Updated service details.")],
        )
        plan = plan_source_sync(
            namespace="xictek-public",
            canonical_url="https://www.xicteksystems.com/services",
            chunks=[Chunk("Services", "Updated service details.")],
            existing_active_chunk_ids={current[0].chunk_id, "old-id"},
        )
        self.assertEqual(plan["retire_after_commit"], ["old-id"])
        self.assertEqual(len(plan["upsert"]), 1)


if __name__ == "__main__":
    unittest.main()
