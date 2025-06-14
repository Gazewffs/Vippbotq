
"""
Mock verification service that simulates real verification
This is for testing purposes when the real service is not available
"""

import logging
import time
import random

logger = logging.getLogger(__name__)

class MockVerificationService:
    def __init__(self):
        # List of "valid" user IDs for testing
        self.valid_user_ids = {
            "12345678", "87654321", "11111111", "22222222", 
            "99999999", "55555555", "77777777", "33333333"
        }
        logger.info("Mock verification service initialized")

    def verify_quotex_user(self, quotex_user_id: str) -> bool:
        """
        Mock verification that simulates checking with QuotexPartnerBot
        Returns True for predefined valid IDs, False otherwise
        """
        logger.info(f"Mock verifying user ID: {quotex_user_id}")
        
        # Simulate network delay
        time.sleep(2)
        
        # Check if user ID is in our "valid" list
        is_valid = quotex_user_id in self.valid_user_ids
        
        if is_valid:
            logger.info(f"Mock verification successful for user ID: {quotex_user_id}")
        else:
            logger.info(f"Mock verification failed for user ID: {quotex_user_id}")
        
        return is_valid

    def test_connection(self) -> bool:
        """Test connection to mock verification service"""
        logger.info("Testing mock verification connection")
        time.sleep(1)  # Simulate connection test
        logger.info("Mock connection test successful")
        return True
