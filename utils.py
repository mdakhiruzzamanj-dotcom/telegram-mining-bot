import random
from datetime import datetime

def generate_mining_stats():
    """Generate realistic mining statistics"""
    cpm = random.uniform(3.0, 10.0)
    hashrate = random.randint(500, 2000)
    efficiency = random.uniform(0.8, 1.2)
    
    return {
        'cpm': round(cpm, 2),
        'hashrate': hashrate,
        'efficiency': round(efficiency, 2),
        'timestamp': datetime.utcnow().strftime('%H:%M:%S')
    }

def generate_ad_stats():
    """Generate realistic ad statistics"""
    return {
        'cpm': round(random.uniform(3.0, 8.0), 2),
        'fill_rate': random.randint(92, 98),
        'viewability': random.randint(88, 95),
        'quality_score': random.randint(8, 10)
    }

def calculate_mining_earnings(mining_power, duration_minutes):
    """Calculate earnings based on mining power and duration"""
    base_earnings = 0.1 * duration_minutes
    return round(base_earnings * mining_power, 6)

def calculate_ad_earnings(ad_type):
    """Calculate earnings based on ad type"""
    ad_rates = {
        'banner': random.uniform(0.001, 0.005),
        'video': random.uniform(0.005, 0.015),
        'interstitial': random.uniform(0.003, 0.008)
    }
    return round(ad_rates.get(ad_type, 0.002), 6)

def format_balance(balance):
    """Format balance with proper formatting"""
    if balance >= 1:
        return f"${balance:.6f}"
    else:
        return f"${balance:.8f}"

def create_mining_animation():
    """Create mining animation frames"""
    frames = [
        "⛏️ Mining... █░░░░░░░░░",
        "⛏️ Mining... ██░░░░░░░░",
        "⛏️ Mining... ███░░░░░░░",
        "⛏️ Mining... ████░░░░░░",
        "⛏️ Mining... █████░░░░░",
        "⛏️ Mining... ██████░░░░",
        "⛏️ Mining... ███████░░░",
        "⛏️ Mining... ████████░░",
        "⛏️ Mining... █████████░",
        "⛏️ Mining... ██████████"
    ]
    return random.choice(frames)
