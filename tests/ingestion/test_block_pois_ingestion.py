"""Tests for block_pois ingestion."""

import unittest
from unittest.mock import MagicMock, patch

from resalelens.ingestion.block_pois import calculate_haversine_distance, ingest_block_pois


class TestBlockPOSIngestion(unittest.TestCase):

    def test_calculate_haversine_distance(self):
        # Known distance: Singapore (1.3521, 103.8198) to JB (1.4927, 103.7414)
        # Approx 17-18km
        lat1, lon1 = 1.3521, 103.8198
        lat2, lon2 = 1.4927, 103.7414

        dist = calculate_haversine_distance(lat1, lon1, lat2, lon2)
        self.assertTrue(15000 < dist < 20000, f"Distance {dist} seems off for SG-JB")

        # Zero distance
        self.assertEqual(calculate_haversine_distance(1.0, 1.0, 1.0, 1.0), 0.0)

    @patch("resalelens.ingestion.block_pois.log_ingestion_run")
    @patch("resalelens.ingestion.block_pois.BlockPOIRepository")
    def test_ingest_block_pois(self, mock_repo_cls, mock_log_ctx):
        # Setup mocks
        mock_session = MagicMock()
        mock_repo = mock_repo_cls.return_value
        mock_repo.upsert_distances.return_value = 1

        # Mock Context Manager
        mock_run = MagicMock()
        mock_log_ctx.return_value.__enter__.return_value = mock_run

        # Mock Data
        # Block at 0,0
        mock_block = MagicMock()
        mock_block.id = 1
        mock_block.latitude = 0.0
        mock_block.longitude = 0.0

        # POI at 0,0.01 (approx 1.1km away at equator)
        mock_poi_near = MagicMock()
        mock_poi_near.id = 101
        mock_poi_near.latitude = 0.0
        mock_poi_near.longitude = 0.01  # ~1.11km
        mock_poi_near.name = "Near POI"

        # POI at 10,10 (far away)
        mock_poi_far = MagicMock()
        mock_poi_far.id = 102
        mock_poi_far.latitude = 10.0
        mock_poi_far.longitude = 10.0
        mock_poi_far.name = "Far POI"

        # Configure session.execute results
        # First call is for POIs, Second is for Blocks, subsequent for queries inside loop?
        # Actually the code does session.execute(select(POI...)) and then session.execute(select(Block...))

        # We need to mock the return values of execute().all()
        # It's a bit tricky with multiple calls. Let's use side_effect.

        def execute_side_effect(query):
            # Inspect query string representation to decide what to return
            q_str = str(query)
            if "FROM pois" in q_str:
                return [mock_poi_near, mock_poi_far]
            if "FROM blocks" in q_str:
                return [mock_block]
            return []

        # Simpler approach: verify the code calls execute twice and mock returns
        # The code iterates the result of .all()

        # Mock the result objects that have .all()
        mock_result_pois = MagicMock()
        mock_result_pois.all.return_value = [mock_poi_near, mock_poi_far]

        mock_result_blocks = MagicMock()
        mock_result_blocks.all.return_value = [mock_block]

        mock_session.execute.side_effect = [mock_result_pois, mock_result_blocks]

        # Run ingestion with 2km limit
        summary = ingest_block_pois(mock_session, max_distance_m=2000.0)

        # Verification
        self.assertEqual(summary["blocks_processed"], 1)
        # Should simulate distance calculation for near POI
        # Far POI might be skipped by bounding box or distance check

        # Check that upsert was called
        mock_repo.upsert_distances.assert_called_once()
        call_args = mock_repo.upsert_distances.call_args
        block_id_arg = call_args[0][0]
        distances_arg = call_args[0][1]

        self.assertEqual(block_id_arg, 1)
        self.assertEqual(len(distances_arg), 1)
        self.assertEqual(distances_arg[0]["poi_id"], 101)
        # 0.01 deg lon at equator is approx 1113.2 meters
        self.assertTrue(1000 < distances_arg[0]["distance_m"] < 1200)

if __name__ == "__main__":
    unittest.main()
