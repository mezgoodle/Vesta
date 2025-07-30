"""
Performance and load tests for the API.
"""

import time

from fastapi.testclient import TestClient


class TestAPIPerformance:
    """Performance tests for the API."""

    def test_response_time_under_threshold(self, client: TestClient):
        """Test that API responses are under acceptable time threshold."""
        endpoints = [
            "/",
            "/health",
            "/api/v1/",
            "/api/v1/status",
            "/api/v1/items/",
            "/api/v1/users/",
            "/api/v1/auth/me",
        ]

        max_response_time = 1.0  # 1 second threshold

        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < max_response_time, (
                f"Endpoint {endpoint} took {response_time:.2f}s"
            )

    def test_concurrent_requests_handling(self, client: TestClient):
        """Test handling of multiple concurrent requests."""
        import threading

        results = []

        def make_request():
            response = client.get("/api/v1/")
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()

        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)

        # Total time should be reasonable
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds

    def test_large_payload_handling(self, client: TestClient):
        """Test handling of large payloads."""
        # Create a large payload
        large_data = {
            "name": "Large Item",
            "description": "x" * 10000,  # 10KB description
            "metadata": {f"key_{i}": f"value_{i}" for i in range(1000)},
        }

        start_time = time.time()
        response = client.post("/api/v1/items/", json=large_data)
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # Should handle large payload within 2 seconds
