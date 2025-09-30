import logging
import asyncio
import random
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = "7837389709:AAEue6M60TRpL7F1adZwsFhkrPx6awll6K4"
ADMIN_ID = 123456789  # আপনার Telegram ID দিন

class SimpleDatabase:
    def __init__(self):
        self.db_path = "mining_bot.db"
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0,
                total_earned REAL DEFAULT 0.0,
                mining_power REAL DEFAULT 1.0,
                referrals INTEGER DEFAULT 0,
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
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
    
    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'balance': user[3],
                'total_earned': user[4],
                'mining_power': user[5],
                'referrals': user[6],
                'created_at': user[7]
            }
        return None
    
    def create_user(self, user_id, username, first_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
                (user_id, username, first_name)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            conn.close()
            return False
    
    def update_balance(self, user_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET balance = balance + ?, total_earned = total_earned + ? WHERE user_id = ?',
            (amount, amount, user_id)
        )
        conn.commit()
        conn.close()
    
    def add_referral(self, referrer_id, referred_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add referral record
        cursor.execute(
            'INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)',
            (referrer_id, referred_id)
        )
        
        # Update referrer stats and add bonus
        cursor.execute(
            'UPDATE users SET referrals = referrals + 1, balance = balance + 0.5 WHERE user_id = ?',
            (referrer_id,)
        )
        
        conn.commit()
        conn.close()

# Initialize database
db = SimpleDatabase()

# Utility functions
def format_balance(balance):
    """Format balance for display"""
    if balance == 0:
        return "$0.00000000"
    elif balance < 0.0001:
        return f"${balance:.8f}"
    else:
        return f"${balance:.6f}"

def calculate_earnings():
    """Calculate random earnings between $0.001 and $0.01"""
    return round(random.uniform(0.001, 0.01), 6)

def get_mining_animation():
    """Get random mining animation"""
    animations = [
        "⛏️ Mining... █░░░░░░░░░ 10%",
        "⛏️ Mining... ██░░░░░░░░ 20%", 
        "⛏️ Mining... ███░░░░░░░ 30%",
        "⛏️ Mining... ████░░░░░░ 40%",
        "⛏️ Mining... █████░░░░░ 50%",
        "⛏️ Mining... ██████░░░░ 60%",
        "⛏️ Mining... ███████░░░ 70%",
        "⛏️ Mining... ████████░░ 80%",
        "⛏️ Mining... █████████░ 90%",
        "⛏️ Mining... ██████████ 100%"
    ]
    return random.choice(animations)

class MiningBot:
    def __init__(self):
        self.db = db
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        # Get or create user
        db_user = self.db.get_user(user_id)
        if not db_user:
            self.db.create_user(user_id, user.username, user.first_name or "User")
            db_user = self.db.get_user(user_id)
            
            # Check for referral
            if context.args:
                try:
                    referrer_id = int(context.args[0])
                    if referrer_id != user_id:
                        self.db.add_referral(referrer_id, user_id)
                        await update.message.reply_text("🎉 You received $0.50 referral bonus!")
                except:
                    pass
        
        # Welcome message
        welcome_text = f"""
🏆 **Welcome to CryptoMiner Pro!** 🏆

✨ *Start earning cryptocurrency today!*

📊 **Your Stats:**
├ 💰 Balance: {format_balance(db_user['balance'])}
├ ⚡ Mining Power: {db_user['mining_power']}x
├ 👥 Referrals: {db_user['referrals']}
└ 📈 Total Earned: {format_balance(db_user['total_earned'])}

🔗 **Your Referral Link:**
`https://t.me/{(await context.bot.get_me()).username}?start={user_id}`

*Invite friends and earn 50% of their earnings!*
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 My Balance", callback_data="show_balance"),
             InlineKeyboardButton("👥 Referrals", callback_data="show_referrals")],
            [InlineKeyboardButton("📊 Statistics", callback_data="show_stats"),
             InlineKeyboardButton("💳 Withdraw", callback_data="show_withdraw")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        data = query.data
        
        db_user = self.db.get_user(user.id)
        if not db_user:
            await query.edit_message_text("❌ User not found. Please /start again.")
            return
        
        if data == "start_mining":
            await self.start_mining(query, db_user)
        elif data == "show_balance":
            await self.show_balance(query, db_user)
        elif data == "show_referrals":
            await self.show_referrals(query, db_user)
        elif data == "show_stats":
            await self.show_stats(query, db_user)
        elif data == "show_withdraw":
            await self.show_withdraw(query, db_user)
        elif data == "main_menu":
            await self.show_main_menu(query, db_user)
    
    async def start_mining(self, query, db_user):
        """Start a mining session"""
        user_id = db_user['user_id']
        
        # Step 1: Initializing
        init_text = """
🚀 **Starting Mining Session...**

⚡ Initializing mining rigs...
🔧 Optimizing performance...
🌐 Connecting to network...
        """
        message = await query.edit_message_text(init_text, parse_mode='Markdown')
        await asyncio.sleep(2)
        
        total_earned = 0
        
        # Step 2: Mining with ads
        for i in range(3):
            # Show mining progress
            mining_text = f"""
🎯 **Mining Session** ({i+1}/3)

{get_mining_animation()}

⏰ Processing transactions...
💰 Calculating rewards...
            """
            await message.edit_text(mining_text)
            await asyncio.sleep(3)
            
            # Show ad
            ad_text = f"""
📺 **Advertisement** ({i+1}/3)

🎬 Playing video ad...
⏱️ Please wait 3 seconds...

*Thank you for supporting our network!*
            """
            await message.edit_text(ad_text)
            await asyncio.sleep(3)
            
            # Calculate earnings
            earnings = calculate_earnings()
            total_earned += earnings
            
            # Update balance
            self.db.update_balance(user_id, earnings)
            
            # Show earnings
            earnings_text = f"""
✅ **Ad Completed!**

💰 Earned: ${earnings:.6f}
📈 Session Total: ${total_earned:.6f}

🎯 Continuing to mine...
            """
            await message.edit_text(earnings_text)
            await asyncio.sleep(2)
        
        # Final results
        final_text = f"""
🎊 **Mining Session Complete!**

✅ **3 Ads Watched**
✅ **Mining Successful**
✅ **Rewards Distributed**

💰 **Total Earned:** ${total_earned:.6f}
📈 **New Balance:** {format_balance(db_user['balance'] + total_earned)}

⚡ Ready for another session?
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Mine Again", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Check Balance", callback_data="show_balance")],
            [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.edit_text(final_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_balance(self, query, db_user):
        """Show user balance"""
        balance_text = f"""
💰 **Your Balance & Stats**

💵 Available: {format_balance(db_user['balance'])}
📈 Total Earned: {format_balance(db_user['total_earned'])}
⚡ Mining Power: {db_user['mining_power']}x
👥 Referrals: {db_user['referrals']}

💎 **Earning Potential:**
├ Mining: $0.01 - $0.03 per session
├ Ads: $0.003 - $0.03 per session  
└ Referrals: 50% commission

🚀 Keep mining to increase your earnings!
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("👥 Referrals", callback_data="show_referrals")],
            [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_referrals(self, query, db_user):
        """Show referral information"""
        bot_username = (await query.bot.get_me()).username
        referral_text = f"""
👥 **Referral Program**

🎁 **Earn 50% Commission!**

For every friend you invite:
✅ You get $0.50 instant bonus
✅ Earn 50% of their mining rewards
✅ Earn 50% of their ad earnings
✅ Lifetime passive income!

📊 **Your Referral Stats:**
├ Total Referrals: {db_user['referrals']}
├ Referral Earnings: ${db_user['balance'] * 0.1:.6f}
└ Potential Monthly: ${db_user['referrals'] * 5:.2f}

🔗 **Your Personal Link:**
`https://t.me/{bot_username}?start={db_user['user_id']}`

📣 **Share this message:**
"Join CryptoMiner Pro and earn free cryptocurrency! Use my link for bonus rewards! 🚀"
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Balance", callback_data="show_balance")],
            [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(referral_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_stats(self, query, db_user):
        """Show statistics"""
        stats_text = f"""
📊 **Live Statistics**

🎯 **Network Status:**
├ 🟢 Mining: Active
├ 🟢 Ads: Running
├ 🟢 Payments: Available
└ 🟢 Referrals: Enabled

💎 **Your Performance:**
├ Mining Power: {db_user['mining_power']}x
├ Total Sessions: {int(db_user['total_earned'] / 0.01)}
├ Success Rate: 99.9%
└ Uptime: 100%

🏭 **System Info:**
├ Version: CryptoMiner Pro v2.1
├ Server: Render Cloud
├ Database: SQLite
└ Status: 🟢 Optimal
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Balance", callback_data="show_balance")],
            [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_withdraw(self, query, db_user):
        """Show withdrawal information"""
        if db_user['balance'] < 1.0:
            withdraw_text = f"""
💳 **Withdrawal Information**

❌ **Minimum: $1.00**

💰 Your Balance: {format_balance(db_user['balance'])}

💎 You need: ${1.0 - db_user['balance']:.6f} more

🚀 **Ways to Earn Faster:**
├ Complete more mining sessions
├ Watch all ads completely  
├ Invite friends (50% commission)
└ Be active daily

⚡ Keep mining to reach the minimum!
            """
        else:
            withdraw_text = f"""
💳 **Withdrawal Request**

✅ **Eligible for Withdrawal!**

💰 Available: {format_balance(db_user['balance'])}

📝 **Payment Method:**
├ Binance UID Transfer
├ Manual Processing
├ 24-48 Hour Processing
└ No Fees

🎯 **Accepted Currencies:**
├ BTTC (BitTorrent Chain)
├ BONK (Solana)
└ PEPE (Ethereum)

**Contact @admin to withdraw**
            """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Balance", callback_data="show_balance")],
            [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(withdraw_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_main_menu(self, query, db_user):
        """Show main menu"""
        menu_text = f"""
🏆 **CryptoMiner Pro Dashboard**

📊 Quick Stats:
├ Balance: {format_balance(db_user['balance'])}
├ Power: {db_user['mining_power']}x
├ Referrals: {db_user['referrals']}
└ Total: {format_balance(db_user['total_earned'])}

Choose an option below:
        """
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("💰 Balance", callback_data="show_balance"),
             InlineKeyboardButton("👥 Referrals", callback_data="show_referrals")],
            [InlineKeyboardButton("📊 Stats", callback_data="show_stats"),
             InlineKeyboardButton("💳 Withdraw", callback_data="show_withdraw")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    """Start the bot"""
    try:
        print("🚀 Starting CryptoMiner Pro Bot...")
        print(f"🤖 Token: {BOT_TOKEN}")
        
        # Initialize bot
        bot = MiningBot()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CallbackQueryHandler(bot.handle_callback))
        
        print("✅ Bot initialized successfully")
        print("📡 Starting polling...")
        
        # Start polling
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("Please check your BOT_TOKEN and try again.")

if __name__ == '__main__':
    main()
