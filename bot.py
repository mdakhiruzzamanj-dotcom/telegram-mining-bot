import logging
import asyncio
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from sqlalchemy.orm import Session

import config
from database import init_db, get_db, User, Referral, Payment
from utils import generate_mining_stats, calculate_mining_earnings, format_balance, create_mining_animation, calculate_ad_earnings, generate_ad_stats

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MonetagSDK:
    def __init__(self):
        self.zone_id = '9945520'
        self.sdk_url = '//libtl.com/sdk.js'
    
    async def simulate_ad_view(self, user_id, ad_type='banner'):
        """Simulate ad viewing and track earnings"""
        try:
            # Simulate different ad types and earnings
            ad_earnings = {
                'banner': random.uniform(0.001, 0.005),
                'video': random.uniform(0.005, 0.015),
                'interstitial': random.uniform(0.003, 0.008)
            }
            
            earnings = ad_earnings.get(ad_type, 0.002)
            
            # Simulate ad loading and viewing
            await asyncio.sleep(3)
            
            return {
                'success': True,
                'earnings': earnings,
                'ad_type': ad_type,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Ad simulation error: {e}")
            return {
                'success': False,
                'earnings': 0.0,
                'ad_type': ad_type,
                'timestamp': datetime.utcnow()
            }

class MiningBot:
    def __init__(self):
        self.config = config.Config()
        self.monetag = MonetagSDK()
        # Initialize database
        init_db()
        logger.info("🤖 MiningBot initialized successfully")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = update.effective_user
            db = get_db()
            
            try:
                # Check if user exists
                db_user = db.query(User).filter(User.user_id == user.id).first()
                
                if not db_user:
                    # Check for referral
                    referral_code = context.args[0] if context.args else None
                    db_user = User(
                        user_id=user.id,
                        username=user.username,
                        first_name=user.first_name or "User"
                    )
                    db.add(db_user)
                    db.commit()
                    
                    if referral_code:
                        try:
                            referrer_id = int(referral_code)
                            referrer = db.query(User).filter(User.user_id == referrer_id).first()
                            if referrer and referrer.id != db_user.id:
                                # Add referral bonus
                                referrer.referrals += 1
                                referrer.referral_bonus += 0.5
                                referrer.balance += 0.5
                                
                                referral = Referral(
                                    referrer_id=referrer_id,
                                    referred_id=user.id
                                )
                                db.add(referral)
                                db.commit()
                                logger.info(f"Referral added: {referrer_id} -> {user.id}")
                        except (ValueError, Exception) as e:
                            logger.warning(f"Referral error: {e}")
                            pass
                
                welcome_text = f"""
🏆 **Welcome to CryptoMiner Pro Bot!** 🏆

💎 *Advanced Cloud Mining Platform*
⚡ *High-Performance Mining Rigs*
🎯 *Professional Grade Equipment*
📺 *Monetag Ads Integration*

📊 **Your Stats:**
├ Balance: {format_balance(db_user.balance)}
├ Total Earned: {format_balance(db_user.total_earned)}
├ Mining Power: {db_user.mining_power}x
└ Referrals: {db_user.referrals} users

🎁 **Referral Program:**
Invite friends and earn 50% of their mining rewards!
Your referral link: 
`https://t.me/{(await context.bot.get_me()).username}?start={user.id}`

💰 **Earn from Ads:** Watch ads to boost your mining earnings!

Click **Start Mining** to begin your journey!
                """
                
                keyboard = [
                    [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
                    [InlineKeyboardButton("💰 Balance", callback_data="balance"),
                     InlineKeyboardButton("👥 Referrals", callback_data="referrals")],
                    [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"),
                     InlineKeyboardButton("📊 Statistics", callback_data="stats")],
                    [InlineKeyboardButton("🛠️ Boost Power", callback_data="boost"),
                     InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
                
            except Exception as e:
                await update.message.reply_text("❌ Database error. Please try again.")
                logger.error(f"Database error in start: {e}")
            finally:
                db.close()
                
        except Exception as e:
            await update.message.reply_text("❌ Bot error. Please try /start again.")
            logger.error(f"Start command error: {e}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        data = query.data
        
        try:
            db = get_db()
            db_user = db.query(User).filter(User.user_id == user.id).first()
            
            if not db_user:
                await query.edit_message_text("❌ User not found. Please use /start again.")
                db.close()
                return
            
            if data == "start_mining":
                await self.start_mining(query, db_user, db)
            elif data == "balance":
                await self.show_balance(query, db_user)
            elif data == "referrals":
                await self.show_referrals(query, db_user)
            elif data == "withdraw":
                await self.show_withdraw(query, db_user)
            elif data == "stats":
                await self.show_stats(query, db_user)
            elif data == "boost":
                await self.show_boost(query, db_user)
            elif data == "watch_ads":
                await self.watch_ads(query, db_user, db)
            elif data == "main_menu":
                await self.main_menu(query, db_user)
            else:
                await self.main_menu(query, db_user)
                
        except Exception as e:
            await query.edit_message_text("❌ Error processing request. Please try again.")
            logger.error(f"Button handler error: {e}")
        finally:
            db.close()
    
    async def watch_ads(self, query, db_user, db):
        """Dedicated ad watching feature"""
        try:
            ad_text = """
📺 **Monetag Ads Platform**

💰 **Earn extra by watching ads!**
🎯 **High-paying advertisements**
⚡ **Instant earnings**

Loading advertisement...
            """
            
            keyboard = [[InlineKeyboardButton("🔄 Loading Ad...", callback_data="loading")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = await query.edit_message_text(ad_text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Simulate different ad types
            ad_types = ['banner', 'video', 'interstitial']
            total_earnings = 0
            
            for i in range(3):
                ad_type = random.choice(ad_types)
                
                # Show ad loading
                loading_text = f"""
📺 **Advertisement ({i+1}/3)**

🔄 Loading {ad_type.upper()} ad...
⏱️ Please wait 3-5 seconds...

💰 *High-quality ad from Monetag network*
                """
                await message.edit_text(loading_text)
                
                # Simulate ad view
                ad_result = await self.monetag.simulate_ad_view(db_user.user_id, ad_type)
                
                if ad_result['success']:
                    earnings = ad_result['earnings']
                    total_earnings += earnings
                    db_user.balance += earnings
                    db_user.total_earned += earnings
                    db.commit()
                    
                    # Show ad completion
                    complete_text = f"""
✅ **Ad Completed! ({i+1}/3)**

🎉 You earned: ${earnings:.6f}
💰 Total this session: ${total_earnings:.6f}
📺 Ad Type: {ad_type.title()}

📊 **Monetag Stats:**
├ CPM: ${random.uniform(3.0, 8.0):.2f}
├ Viewability: {random.randint(85, 98)}%
└ Quality Score: {random.randint(8, 10)}/10

Next ad loading...
                    """
                    await message.edit_text(complete_text)
                    await asyncio.sleep(2)
            
            # Session complete
            session_text = f"""
🎊 **Ad Session Complete!**

💰 **Total Earnings:** ${total_earnings:.6f}
📈 **New Balance:** {format_balance(db_user.balance)}
🎯 **Ads Watched:** 3
⏱️ **Session Time:** 15 seconds

💎 **Monetag Performance:**
├ Total Earnings: ${total_earnings:.6f}
├ Ads Completed: 3/3
└ Success Rate: 100%

Watch more ads or start mining!
            """
            
            keyboard = [
                [InlineKeyboardButton("📺 Watch More Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
                [InlineKeyboardButton("📊 Dashboard", callback_data="balance")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.edit_text(session_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text("❌ Error watching ads. Please try again.")
            logger.error(f"Watch ads error: {e}")
    
    async def start_mining(self, query, db_user, db):
        try:
            if db_user.is_mining:
                await query.edit_message_text("⛏️ You are already mining! Please wait for current session to complete.")
                return
            
            # Start mining session
            db_user.is_mining = True
            db_user.last_mining = datetime.utcnow()
            db.commit()
            
            # Show mining animation
            mining_text = """
🚀 **Starting Advanced Mining Session...**

🏭 *Initializing Mining Rigs...*
⚡ *Connecting to Global Network...*
🔧 *Optimizing Performance...*
📺 *Loading Monetag Ads...*
            """
            
            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="start_mining")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = await query.edit_message_text(mining_text, reply_markup=reply_markup, parse_mode='Markdown')
            
            total_ad_earnings = 0
            
            # Simulate mining process with Monetag ads
            for i in range(3):
                await asyncio.sleep(2)
                
                # Show Monetag ad
                ad_text = f"""
📺 **Monetag Advertisement ({i+1}/3)**

💰 *Premium Ad Network*
⏱️ Watching ad for {self.config.AD_DURATION} seconds...

⚡ *Earning bonus rewards through Monetag...*
                """
                await message.edit_text(ad_text)
                
                # Simulate Monetag ad view
                ad_result = await self.monetag.simulate_ad_view(db_user.user_id, 'video')
                if ad_result['success']:
                    total_ad_earnings += ad_result['earnings']
                    db_user.balance += ad_result['earnings']
                    db_user.total_earned += ad_result['earnings']
                    db.commit()
                
                await asyncio.sleep(self.config.AD_DURATION)
                
                # Show mining progress with Monetag stats
                stats = generate_mining_stats()
                progress_text = f"""
🎯 **Mining Session Active**

{create_mining_animation()}

📊 **Live Statistics:**
├ CPM: {stats['cpm']} (Professional Grade)
├ Hashrate: {stats['hashrate']} MH/s
├ Efficiency: {stats['efficiency']}
└ Time: {stats['timestamp']} UTC

💰 **Monetag Earnings:** ${total_ad_earnings:.6f}
⏳ Next ad in: {3-i} cycles
                """
                await message.edit_text(progress_text)
                await asyncio.sleep(5)
            
            # Complete mining session
            mining_earnings = calculate_mining_earnings(db_user.mining_power, 1)
            total_earnings = mining_earnings + total_ad_earnings
            
            db_user.balance += mining_earnings
            db_user.total_earned += mining_earnings
            db_user.is_mining = False
            db.commit()
            
            completion_text = f"""
✅ **Mining Session Complete!**

💰 **Total Earnings:** ${total_earnings:.8f}
├ Mining: ${mining_earnings:.8f}
└ Ads: ${total_ad_earnings:.8f}

📈 **New Balance:** {format_balance(db_user.balance)}
⚡ **Mining Power:** {db_user.mining_power}x

🎯 **Session Performance:**
├ Ads Watched: 3 (Monetag)
├ Mining Time: 30 seconds
└ Efficiency: Excellent

💎 **Monetag Performance:**
├ Ads Completed: 3/3
├ Total Ad Revenue: ${total_ad_earnings:.6f}
└ Network: Premium

Click below to continue!
            """
            
            keyboard = [
                [InlineKeyboardButton("⛏️ Mine Again", callback_data="start_mining")],
                [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("📊 Dashboard", callback_data="balance")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.edit_text(completion_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text("❌ Mining error. Please try again.")
            logger.error(f"Mining error: {e}")
            # Reset mining status
            db_user.is_mining = False
            db.commit()
    
    async def show_balance(self, query, db_user):
        try:
            balance_text = f"""
💰 **Your Balance & Statistics**

💵 **Available Balance:** {format_balance(db_user.balance)}
🏦 **Total Earned:** {format_balance(db_user.total_earned)}
⚡ **Mining Power:** {db_user.mining_power}x
👥 **Referral Bonus:** ${db_user.referral_bonus:.6f}

📺 **Monetag Ads:**
├ Ad Earnings: Active
├ CPM Rate: ${random.uniform(3.0, 8.0):.2f}
└ Ad Quality: Premium

📈 **Earning Potential:**
├ Base Mining: $0.10/hour
├ With Current Power: ${0.10 * db_user.mining_power:.2f}/hour
├ Ad Earnings: $0.05-$0.15/hour
└ Estimated Daily: ${(0.10 * db_user.mining_power + 0.10) * 24:.2f}

💎 Boost your mining power to earn more!
            """
            
            keyboard = [
                [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
                [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"),
                 InlineKeyboardButton("🛠️ Boost Power", callback_data="boost")],
                [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text("❌ Error loading balance.")
            logger.error(f"Balance error: {e}")
    
    async def show_referrals(self, query, db_user):
        try:
            referral_text = f"""
👥 **Referral Program**

🎁 **Earn 50% of your referrals' mining AND ad earnings!**

📊 **Your Referral Stats:**
├ Total Referrals: {db_user.referrals}
├ Referral Earnings: ${db_user.referral_bonus:.6f}
└ Active Referrals: {db_user.referrals}

🔗 **Your Personal Referral Link:**
`https://t.me/{(await query.bot.get_me()).username}?start={db_user.user_id}`

💰 **Bonus:** Referrals also earn from Monetag ads!
You get 50% of their ad earnings too!

📣 **Share this message:**
💎 Join CryptoMiner Pro - Advanced Cloud Mining Platform!
⚡ High-performance mining with professional equipment!
💰 Earn from mining AND Monetag ads!
🎁 Use my link to get bonus starting rewards!
            """
            
            keyboard = [
                [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
                [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("💰 Balance", callback_data="balance")],
                [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(referral_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text("❌ Error loading referrals.")
            logger.error(f"Referrals error: {e}")
    
    async def show_withdraw(self, query, db_user):
        try:
            if db_user.balance < 1.0:
                withdraw_text = f"""
💳 **Withdrawal**

❌ **Minimum withdrawal: $1.00**

💰 Your current balance: {format_balance(db_user.balance)}

💎 You need ${1.0 - db_user.balance:.6f} more to withdraw.

🚀 Keep mining and watching ads to reach the minimum amount!
                """
            else:
                withdraw_text = f"""
💳 **Withdrawal Request**

💰 **Available Balance:** {format_balance(db_user.balance)}
✅ **Eligible for withdrawal!**

📝 **Payment Method:** Binance UID
💎 **Accepted Currencies:** BTTC, BONK, PEPE

💰 **Earnings Source:**
├ Mining Rewards
└ Monetag Ad Revenue

To withdraw, please contact admin with your:
1. Binance UID
2. Preferred currency (BTTC/BONK/PEPE)
3. Withdrawal amount

Admin will process your payment manually.
                """
            
            keyboard = [
                [InlineKeyboardButton("⛏️ Continue Mining", callback_data="start_mining")],
                [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("💰 Balance", callback_data="balance")],
                [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(withdraw_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text("❌ Error loading withdrawal.")
            logger.error(f"Withdraw error: {e}")
    
    async def show_stats(self, query, db_user):
        try:
            stats = generate_mining_stats()
            ad_stats = generate_ad_stats()
            stats_text = f"""
📊 **Live Mining & Ad Statistics**

🎯 **Network Performance:**
├ Global CPM: {stats['cpm']}
├ Network Hashrate: {stats['hashrate']} MH/s
├ Efficiency Rating: {stats['efficiency']}
└ Server Time: {stats['timestamp']} UTC

📺 **Monetag Ad Network:**
├ Ad CPM: ${ad_stats['cpm']}
├ Fill Rate: {ad_stats['fill_rate']}%
├ Viewability: {ad_stats['viewability']}%
└ Quality Score: {ad_stats['quality_score']}/10

💎 **Your Performance:**
├ Mining Power: {db_user.mining_power}x
├ Total Sessions: {int(db_user.total_earned / 0.1) if db_user.total_earned > 0 else 0}
├ Ad Views: {int(db_user.total_earned / 0.002) if db_user.total_earned > 0 else 0}
└ Uptime: 99.9%

🏭 **Mining Equipment:**
├ ASIC Miners: Online
├ Cloud Nodes: Active
├ Monetag Ads: Integrated
└ Payment System: Active
            """
            
            keyboard = [
                [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
                [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("💰 Balance", callback_data="balance")],
                [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text("❌ Error loading statistics.")
            logger.error(f"Stats error: {e}")
    
    async def show_boost(self, query, db_user):
        try:
            boost_text = f"""
🛠️ **Boost Your Mining Power**

⚡ **Current Mining Power:** {db_user.mining_power}x

💎 **Available Boosts:**
├ 2x Power - $5.00 (Permanent)
├ 5x Power - $20.00 (Permanent)
└ 10x Power - $35.00 (Permanent)

💰 **Earning Comparison:**
├ Current: ${0.10 * db_user.mining_power:.2f}/hour + ads
├ 2x Power: ${0.10 * 2:.2f}/hour + ads
├ 5x Power: ${0.10 * 5:.2f}/hour + ads
└ 10x Power: ${0.10 * 10:.2f}/hour + ads

📺 **Ad earnings remain the same!**

Contact admin to upgrade your mining power!
            """
            
            keyboard = [
                [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
                [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("📊 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(boost_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text("❌ Error loading boost info.")
            logger.error(f"Boost error: {e}")
    
    async def main_menu(self, query, db_user):
        try:
            welcome_text = f"""
🏆 **CryptoMiner Pro Dashboard** 🏆

💎 *Advanced Cloud Mining Platform*
⚡ *High-Performance Mining Rigs*
📺 *Monetag Ads Integration*

📊 **Your Stats:**
├ Balance: {format_balance(db_user.balance)}
├ Total Earned: {format_balance(db_user.total_earned)}
├ Mining Power: {db_user.mining_power}x
└ Referrals: {db_user.referrals} users

💰 **Earn from both mining and ads!**

Choose an option below:
            """
            
            keyboard = [
                [InlineKeyboardButton("⛏️ Start Mining", callback_data="start_mining")],
                [InlineKeyboardButton("📺 Watch Ads", callback_data="watch_ads")],
                [InlineKeyboardButton("💰 Balance", callback_data="balance"),
                 InlineKeyboardButton("👥 Referrals", callback_data="referrals")],
                [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"),
                 InlineKeyboardButton("📊 Statistics", callback_data="stats")],
                [InlineKeyboardButton("🛠️ Boost Power", callback_data="boost")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text("❌ Error loading menu.")
            logger.error(f"Menu error: {e}")

def main():
    try:
        bot = MiningBot()
        
        # Create application with your token
        application = Application.builder().token(bot.config.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CallbackQueryHandler(bot.button_handler))
        
        print("🤖 Bot is starting...")
        print(f"✅ Token: {bot.config.BOT_TOKEN}")
        print("🚀 Bot is running on Render!")
        
        # Start the bot
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        logging.error(f"Bot startup error: {e}")

if __name__ == '__main__':
    main()
