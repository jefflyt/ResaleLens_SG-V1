"""Tests for geospatial utilities."""


from resalelens.utils.geo import calculate_haversine_distance


class TestHaversineDistance:
    """Tests for Haversine distance calculation."""

    def test_same_location_zero_distance(self):
        """Test that distance between same point is zero."""
        dist = calculate_haversine_distance(1.3521, 103.8198, 1.3521, 103.8198)
        assert dist == 0.0

    def test_known_distance_ang_mo_kio_to_bishan(self):
        """Test known distance between Ang Mo Kio MRT and Bishan MRT."""
        # Ang Mo Kio MRT: 1.3700, 103.8494
        # Bishan MRT: 1.3509, 103.8484
        # Calculated distance: ~2.1km
        dist = calculate_haversine_distance(1.3700, 103.8494, 1.3509, 103.8484)

        # Allow 5% tolerance for Haversine approximation
        assert 2000 < dist < 2200, f"Expected ~2100m, got {dist:.0f}m"

    def test_known_distance_orchard_to_marina_bay(self):
        """Test known distance between Orchard MRT and Marina Bay MRT."""
        # Orchard MRT: 1.3048, 103.8318
        # Marina Bay MRT: 1.2764, 103.8542
        # Known distance: ~4.2km
        dist = calculate_haversine_distance(1.3048, 103.8318, 1.2764, 103.8542)

        # Allow 5% tolerance
        assert 4000 < dist < 4400, f"Expected ~4200m, got {dist:.0f}m"

    def test_short_distance_accuracy(self):
        """Test accuracy for short distances (<100m)."""
        # Two points ~50m apart
        dist = calculate_haversine_distance(1.3521, 103.8198, 1.3525, 103.8198)

        # Should be approximately 44-45 meters
        assert 40 < dist < 50, f"Expected ~45m, got {dist:.0f}m"

    def test_symmetry(self):
        """Test that distance(A, B) == distance(B, A)."""
        dist_ab = calculate_haversine_distance(1.3700, 103.8494, 1.3509, 103.8484)
        dist_ba = calculate_haversine_distance(1.3509, 103.8484, 1.3700, 103.8494)

        assert dist_ab == dist_ba

    def test_positive_distance(self):
        """Test that distance is always positive."""
        # Test various point combinations
        test_cases = [
            (1.3521, 103.8198, 1.3700, 103.8494),
            (1.2764, 103.8542, 1.3048, 103.8318),
            (1.4000, 103.9000, 1.3000, 103.8000),
        ]

        for lat1, lng1, lat2, lng2 in test_cases:
            dist = calculate_haversine_distance(lat1, lng1, lat2, lng2)
            assert dist >= 0, f"Distance should be non-negative, got {dist}"

    def test_singapore_bounds(self):
        """Test distances within Singapore bounds."""
        # Singapore roughly: 1.1°N - 1.5°N, 103.6°E - 104.0°E
        # Max distance across Singapore ~50km

        # Southwest corner to northeast corner
        dist = calculate_haversine_distance(1.1, 103.6, 1.5, 104.0)

        # Should be less than 65km (actual diagonal is ~63km)
        assert dist < 65000, f"Distance across Singapore should be <65km, got {dist/1000:.1f}km"
