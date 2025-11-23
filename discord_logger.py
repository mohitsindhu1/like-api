import os
import requests
import json
from datetime import datetime
from typing import Optional, Dict, List


class DiscordWebhookLogger:
    """Discord webhook logger for sending formatted logs to Discord"""
    
    def __init__(self):
        self.webhook_url = None
        self.enabled = False
        
        # Disable in serverless/Vercel environment
        if os.environ.get('DISABLE_DISCORD_LOGGER') == '1' or os.environ.get('VERCEL') == '1':
            self.enabled = False
            return
        
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                discord_config = config.get('discord', {})
                self.webhook_url = discord_config.get('webhook_url')
                self.enabled = discord_config.get('enabled', False) and bool(self.webhook_url)
        except Exception as e:
            print(f"⚠️ Could not load Discord config: {e}")
        
        if not self.enabled:
            print("⚠️ Discord webhook not configured")
        else:
            print("✅ Discord webhook logger enabled")
    
    def send_embed(self, title: str, description: str, color: int = 0xFFFFFF, 
                   fields: Optional[List[Dict]] = None, footer: Optional[str] = None):
        """Send an embed message to Discord"""
        if not self.enabled:
            return
        
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": footer or "Free Fire Token Generator"
                }
            }
            
            if fields:
                embed["fields"] = fields
            
            payload = {
                "embeds": [embed],
                "username": "Token Generator Bot"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code not in [200, 204]:
                print(f"⚠️ Discord webhook error: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Failed to send Discord webhook: {e}")
    
    def log_scheduler_start(self, next_run: str):
        """Log when scheduler starts"""
        self.send_embed(
            title="🚀 Token Generator Started",
            description="Automatic token generation scheduler has been started successfully",
            color=0x00FF00,  # Green
            fields=[
                {
                    "name": "Next Scheduled Run",
                    "value": f"```{next_run}```",
                    "inline": False
                },
                {
                    "name": "Generation Interval",
                    "value": "Every 6 hours per region",
                    "inline": True
                },
                {
                    "name": "Status",
                    "value": "✅ Active",
                    "inline": True
                }
            ]
        )
    
    def log_token_generation_start(self, regions: List[str]):
        """Log when token generation starts"""
        regions_str = ", ".join(regions)
        self.send_embed(
            title="🔄 Token Generation Started",
            description=f"Starting automatic token generation for regions: **{regions_str}**",
            color=0x3498DB,  # Blue
            fields=[
                {
                    "name": "Regions",
                    "value": f"```{regions_str}```",
                    "inline": False
                }
            ]
        )
    
    def log_token_generation_complete(self, generated: Dict[str, int], skipped: List[str]):
        """Log when token generation completes"""
        total = sum(generated.values())
        
        fields = []
        
        if generated:
            gen_text = "\n".join([f"{region}: {count} tokens" for region, count in generated.items()])
            fields.append({
                "name": "✅ Generated",
                "value": f"```{gen_text}```",
                "inline": False
            })
        
        if skipped:
            skip_text = ", ".join(skipped)
            fields.append({
                "name": "⏭️ Skipped",
                "value": f"```{skip_text}```",
                "inline": False
            })
        
        fields.append({
            "name": "Total Tokens Generated",
            "value": f"**{total}**",
            "inline": True
        })
        
        self.send_embed(
            title="🎉 Token Generation Complete",
            description="Token generation cycle completed successfully",
            color=0x2ECC71,  # Green
            fields=fields
        )
    
    def log_region_generation(self, region: str, count: int, duration: float):
        """Log individual region generation"""
        self.send_embed(
            title=f"✅ {region} Tokens Generated",
            description=f"Successfully generated tokens for region **{region}**",
            color=0xFFFFFF,  # White
            fields=[
                {
                    "name": "Region",
                    "value": f"```{region}```",
                    "inline": True
                },
                {
                    "name": "Tokens Generated",
                    "value": f"**{count}**",
                    "inline": True
                },
                {
                    "name": "Duration",
                    "value": f"{duration:.2f} seconds",
                    "inline": True
                }
            ]
        )
    
    def log_error(self, error_type: str, error_msg: str, region: Optional[str] = None):
        """Log errors"""
        description = f"**Error Type:** {error_type}\n**Message:** {error_msg}"
        
        fields = []
        if region:
            fields.append({
                "name": "Region",
                "value": f"```{region}```",
                "inline": True
            })
        
        self.send_embed(
            title="❌ Token Generation Error",
            description=description,
            color=0xFF0000,  # Red
            fields=fields
        )
    
    def log_scheduler_heartbeat(self, next_run: str, hours_running: float):
        """Log scheduler heartbeat (every 30 minutes)"""
        self.send_embed(
            title="💓 Scheduler Heartbeat",
            description="Token generator scheduler is active and running",
            color=0xFFFFFF,  # White
            fields=[
                {
                    "name": "Status",
                    "value": "✅ Running",
                    "inline": True
                },
                {
                    "name": "Next Run",
                    "value": f"```{next_run}```",
                    "inline": False
                },
                {
                    "name": "Uptime",
                    "value": f"{hours_running:.1f} hours",
                    "inline": True
                }
            ]
        )
    
    def log_region_skip(self, region: str, hours_since: float, hours_until: float):
        """Log when a region is skipped"""
        self.send_embed(
            title=f"⏭️ {region} Skipped",
            description=f"Region **{region}** tokens are still valid, skipping generation",
            color=0xF39C12,  # Orange
            fields=[
                {
                    "name": "Hours Since Last Generation",
                    "value": f"{hours_since:.2f}h",
                    "inline": True
                },
                {
                    "name": "Next Generation In",
                    "value": f"{hours_until:.2f}h",
                    "inline": True
                }
            ]
        )


discord_logger = DiscordWebhookLogger()
