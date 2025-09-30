import logging
import asyncio
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import os

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = "7837389709:AAEue6M60TRpL7F1adZwsFhkrPx6awll6K4"
ADMIN_ID = 123456789  # আপনার Telegram ID

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('mining_bot.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0,
                total_earned REAL DEFAULT 0.0,
                mining_power REAL DEFAULT 1.0,
                referrals INTEGER DEFAULT 0,
                referral_bonus REAL DEFAULT 0.0,
                is_mining BOOLEAN DEFAULT FALSE,
                last_mining TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Referrals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ Database tables created successfully")
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            return {
                'id': user[0],
                'user_id': user[1],
                'username': user[2],
                'first_name': user[3],
                'balance': user[4],
                'total_earned': user[5],
                'mining_power': user[6],
                'referrals': user[7],
                'referral_bonus': user[8],
                'is_mining': user[9],
                'last_mining': user[10],
                'created_at': user[11]
            }
        return None
    
    def create_user(self, user_id, username, first_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name) 
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET balance = balance + ?, total_earned = total_earned + ? 
            WHERE user_id = ?
        ''', (amount, amount, user_id))
        self.conn.commit()
    
    def add_referral(self, referrer_id, referred_id):
        cursor = self.conn.cursor()
        
        # Add referral record
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id) 
            VALUES (?, ?)
        ''', (referrer_id, referred_id))
        
        # Update referrer stats
        cursor.execute('''
            UPDATE users 
            SET referrals = referrals + 1, 
                referral_bonus = referral_bonus + 0.5,
                balance = balance + 0.5
            WHERE user_id = ?
        ''', (referrer_id,))
        
        self.conn.commit()

# Initialize database
db = Database()

# Utility functions
def format_balance(balance):
    if balance >= 1:
        return f"${balance:.6f}"
    else:
        return f"${balance:.8f}"

def calculate_mining_earnings(mining_power, duration_minutes):
    base_earnings = 0.1 * duration_minutes
    return round(base_earnings * mining_power, 6)

def create_mining_animation():
    frames = [
        "⛏️ Mining... █░░░░░░░░░",
        "⛏️ Mining... ██░░░░░░░░",
        "⛏️ Mining... ███░░░░░░░",
        "⛏️ Mining... ████░░░░░░",
        "⛏️ Mining... █████░░░░░"
    ]
    return random.choice(frames)

class MiningBot:
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # Check if user exists
        db_user = db.get_user(user.id)
        
        if not db_user:
            # Create new user
            db.create_user(user.id, user.username, user.first_name or "User")
            db_user = db.get_user(user.id)
            
            # Check for referral
            referral_code = context.args[0] if context.args else None
            if referral_code:
                try:
                    referrer_id = int(referral_code)
                    if referrer_id != user.id:
                        db.add_referral(referrer_id, user.id)
                except:
                    pass
        
        welcome_text = f"""
🏆 **Welcome to CryptoMiner Pro Bot!** 🏆

📊 **Your Stats:**
├ Balance: {format_balance(db_user['balance'])}
├ Total Earned: {format_balance(db_user['total_earned'])}
├ Mining Power: {db_user['mining_power']}x
└ Referrals: {db_user['referrals']} users

🎁 **Referral Link:**
`https://t.me/{(await context.bot.get_me()).username}?start={user.id}`

Click **Start Mining** to begin!
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Balance", callback_data="balance"),
             InlineKeyboardButton("👥 Referrals", callback_data="referrals")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        data = query.data
        
        db_user = db.get_user(user.id)
        
        if data == "start_mining":
            await self.start_mining(query, db_user)
        elif data == "balance":
            await self.show_balance(query, db_user)
        elif data == "referrals":
            await self.show_referrals(query, db_user)
        elif data == "stats":
            await self.show_stats(query, db_user)
    
    async def start_mining(self, query, db_user):
        mining_text = """
🚀 **Starting Mining Session...**
⛏️ Mining in progress...
        """
        
        message = await query.edit_message_text(mining_text, parse_mode='Markdown')
        
        # Simulate mining with ads
        total_earnings = 0
        
        for i in range(3):
            await asyncio.sleep(2)
            
            # Show ad
            ad_text = f"""
📺 **Advertisement ({i+1}/3)**
Watching ad for 5 seconds...
            """
            await message.edit_text(ad_text)
            await asyncio.sleep(5)
            
            # Ad earnings
            ad_earnings = random.uniform(0.001, 0.005)
            total_earnings += ad_earnings
            
            # Mining progress
            progress_text = f"""
🎯 **Mining Session Active**

{create_mining_animation()}

💰 Earnings so far: ${total_earnings:.6f}
⏳ Next ad in: {3-i} cycles
            """
            await message.edit_text(progress_text)
            await asyncio.sleep(5)
        
        # Mining earnings
        mining_earnings = calculate_mining_earnings(db_user['mining_power'], 1)
        total_earnings += mining_earnings
        
        # Update balance
        db.update_balance(db_user['user_id'], total_earnings)
        
        completion_text = f"""
✅ **Mining Session Complete!**

💰 **Total Earnings:** ${total_earnings:.8f}
📈 **New Balance:** {format_balance(db_user['balance'] + total_earnings)}

Click below to mine again!
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Mine Again", callback_data="start_mining")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.edit_text(completion_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_balance(self, query, db_user):
        balance_text = f"""
💰 **Your Balance & Statistics**

💵 **Available Balance:** {format_balance(db_user['balance'])}
🏦 **Total Earned:** {format_balance(db_user['total_earned'])}
⚡ **Mining Power:** {db_user['mining_power']}x
👥 **Referrals:** {db_user['referrals']} users

Keep mining to earn more!
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_referrals(self, query, db_user):
        referral_text = f"""
👥 **Referral Program**

🎁 **Earn 50% of your referrals' earnings!**

📊 **Your Stats:**
├ Total Referrals: {db_user['referrals']}
├ Referral Earnings: ${db_user['referral_bonus']:.6f}

🔗 **Your Referral Link:**
`https://t.me/{(await query.bot.get_me()).username}?start={db_user['user_id']}`

Share this link to earn more!
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Balance", callback_data="balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(referral_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_stats(self, query, db_user):
        stats_text = f"""
📊 **Live Statistics**

💎 **Your Performance:**
├ Mining Power: {db_user['mining_power']}x
├ Total Sessions: {int(db_user['total_earned'] / 0.1) if db_user['total_earned'] > 0 else 0}
└ Uptime: 99.9%

🏭 **Mining Equipment:**
├ ASIC Miners: Online
├ Cloud Nodes: Active
└ System: Stable
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Balance", callback_data="balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    try:
        bot = MiningBot()
        
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CallbackQueryHandler(bot.button_handler))
        
        print("🤖 Bot is starting...")
        print("🚀 Bot is running on Render!")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == '__main__':
    main()
