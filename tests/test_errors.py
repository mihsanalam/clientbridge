import unittest

from clientbridge.exceptions import (
    APIError,
    AuthenticationError,
    ClientBridgeError,
    NetworkError,
    RateLimitError,
    ServerError,
)


class ExceptionTests(unittest.TestCase):
    def test_api_errors_share_a_base_class(self):
        for error_class in (
            APIError,
            AuthenticationError,
            RateLimitError,
            ServerError,
        ):
            self.assertTrue(issubclass(error_class, ClientBridgeError))

    def test_network_error_is_a_client_bridge_error(self):
        self.assertTrue(issubclass(NetworkError, ClientBridgeError))
        self.assertFalse(issubclass(NetworkError, APIError))

    def test_specific_errors_are_api_errors(self):
        for error_class in (AuthenticationError, RateLimitError, ServerError):
            self.assertTrue(issubclass(error_class, APIError))

    def test_api_error_keeps_message_and_status_code(self):
        error = APIError("failed", 503)
        self.assertEqual(str(error), "failed")
        self.assertEqual(error.status_code, 503)

    def test_api_error_status_code_defaults_to_none(self):
        self.assertIsNone(APIError("failed").status_code)

    def test_specific_error_keeps_status_code(self):
        error = RateLimitError("slow down", 429)
        self.assertEqual(str(error), "slow down")
        self.assertEqual(error.status_code, 429)


if __name__ == "__main__":
    unittest.main()
