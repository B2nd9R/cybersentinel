import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from security.threat_analyzer import ThreatAnalyzer
from security.link_guardian import LinkGuardian

class TestThreatAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ThreatAnalyzer()
        self.analyzer.initialize = AsyncMock()
    
    async def test_analyze_message(self):
        message = MagicMock()
        message.content = "Test message"
        message.author = MagicMock()
        
        result = await self.analyzer.analyze_message(message)
        self.assertIsInstance(result, dict)
        self.assertIn('threat_level', result)
        
    async def test_check_user_behavior(self):
        user = MagicMock()
        guild = MagicMock()
        
        result = await self.analyzer.check_user_behavior(user, guild)
        self.assertIsInstance(result, dict)
        self.assertIn('risk_score', result)

class TestLinkGuardian(unittest.TestCase):
    def setUp(self):
        self.guardian = LinkGuardian('test_api_key')
        self.guardian.initialize = AsyncMock()
    
    async def test_scan_link(self):
        url = "https://example.com"
        result = await self.guardian.scan_link(url)
        self.assertIsInstance(result, dict)
        self.assertIn('is_safe', result)

if __name__ == '__main__':
    unittest.main()