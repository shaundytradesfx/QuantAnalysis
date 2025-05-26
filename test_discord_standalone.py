#!/usr/bin/env python3
"""
Standalone Discord webhook test that bypasses database dependencies.
"""
import os
import requests
from datetime import datetime, timedelta

def test_discord_webhook():
    """Test Discord webhook directly without database dependencies."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL environment variable not set")
        return False
    
    print("🧪 Testing Discord Webhook Integration...")
    print(f"🔗 Webhook URL: {webhook_url[:50]}...")
    
    # Create test message
    week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    while week_start.weekday() != 0:  # Monday is 0
        week_start -= timedelta(days=1)
    
    week_str = week_start.strftime("%B %d, %Y")
    
    message = f"""**📊 Economic Directional Analysis: Week of {week_str}**

**🇺🇸 USD**
1. CPI y/y (Test): Prev=2.10, Forecast=2.30 → 🟢 Bullish
**Overall**: 🟢 Bullish – Discord webhook integration test successful!

**📈 Net Summary:**
• USD: Bullish (Test)

_Generated automatically by EconSentimentBot - Integration Test_"""
    
    # Send message
    payload = {"content": message}
    
    try:
        print("📤 Sending test message...")
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 204:
            print("✅ SUCCESS: Discord message sent successfully!")
            print("🎉 Discord webhook integration is working correctly!")
            return True
        else:
            print(f"❌ FAILED: Discord returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to send Discord message: {e}")
        return False

if __name__ == "__main__":
    success = test_discord_webhook()
    exit(0 if success else 1) 