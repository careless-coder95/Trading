"""
📝 JOURNAL HANDLER
ForexBot Pro - Trading Journal & Notes
"""

import logging
from datetime import date
from telegram import Update
from telegram.ext import (
    CommandHandler, ConversationHandler, MessageHandler,
    ContextTypes, filters
)
from config import JOURNAL_CONTENT, JOURNAL_TAGS, IDEA_PAIR, IDEA_CONTENT
from database import Database

logger = logging.getLogger(__name__)


class Journal:
    """Trading journal and ideas management"""

    def __init__(self):
        self.db = Database()

    def get_journal_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("journal", self.start_journal)],
            states={
                JOURNAL_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.journal_content)],
                JOURNAL_TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.journal_tags)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def get_idea_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("idea", self.start_idea)],
            states={
                IDEA_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.idea_pair)],
                IDEA_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.idea_content)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    async def start_journal(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start journal entry"""
        self.db.ensure_user(update.effective_user.id)
        await update.message.reply_text(
            "📝 *Trading Journal Entry*\n\n"
            "Aaj ka trading experience share karein:\n"
            "Market conditions, emotions, lessons learned...\n\n"
            "_Long message bhi likh sakte hain!_\n"
            "_/cancel se cancel karein_",
            parse_mode="Markdown"
        )
        return JOURNAL_CONTENT

    async def journal_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        content = update.message.text.strip()
        if len(content) < 10:
            await update.message.reply_text(
                "❌ Thoda zyada detail mein likhein (kam se kam 10 characters).",
                parse_mode="Markdown"
            )
            return JOURNAL_CONTENT
        
        context.user_data["journal"] = {"content": content}
        await update.message.reply_text(
            "✅ Journal entry saved!\n\n"
            "Tags add karein (comma-separated, optional):\n"
            "Example: `psychology, breakout, patience`\n\n"
            "Ya `skip` type karein.",
            parse_mode="Markdown"
        )
        return JOURNAL_TAGS

    async def journal_tags(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        tags_input = update.message.text.strip()
        tags = "" if tags_input.lower() == "skip" else tags_input
        
        journal = context.user_data["journal"]
        today = date.today()
        
        entry_id = self.db.add_journal_entry(
            update.effective_user.id,
            today,
            journal["content"],
            tags
        )
        
        await update.message.reply_text(
            f"📝 *Journal Entry #{entry_id} Saved!*\n\n"
            f"📅 Date: `{today}`\n"
            f"📄 Content: {journal['content'][:100]}{'...' if len(journal['content']) > 100 else ''}\n"
            f"🏷️ Tags: `{tags if tags else 'None'}`\n\n"
            f"_View entries: `/notes`_",
            parse_mode="Markdown"
        )
        context.user_data.pop("journal", None)
        return ConversationHandler.END

    async def view_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """View past journal entries"""
        user_id = update.effective_user.id
        limit = 10
        
        # Check for args (optional date filter)
        args = context.args
        date_filter = None
        if args:
            try:
                date_filter = args[0]
            except:
                pass
        
        entries = self.db.get_journal_entries(user_id, limit, date_filter)
        
        if not entries:
            await update.message.reply_text(
                "📭 Koi journal entry nahi mili!\n\n"
                "`/journal` se entry add karein.",
                parse_mode="Markdown"
            )
            return
        
        msg = "📝 *Recent Journal Entries*\n" + "━" * 35 + "\n\n"
        
        for entry in entries:
            content_preview = entry["content"][:150]
            if len(entry["content"]) > 150:
                content_preview += "..."
            
            tags_display = f"🏷️ {entry['tags']}" if entry["tags"] else ""
            
            msg += (
                f"📅 *{entry['entry_date']}* — Entry #{entry['id']}\n"
                f"{content_preview}\n"
                f"{tags_display}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
            )
        
        msg += f"_Showing {len(entries)} entries_\n"
        msg += "_Filter by date: `/notes YYYY-MM-DD`_"
        
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def start_idea(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Save trade idea for future"""
        await update.message.reply_text(
            "💡 *Trade Idea Save Karein*\n\n"
            "Currency pair enter karein:\n"
            "Example: `EURUSD`",
            parse_mode="Markdown"
        )
        return IDEA_PAIR

    async def idea_pair(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        pair = update.message.text.upper().strip()
        context.user_data["idea"] = {"pair": pair}
        
        await update.message.reply_text(
            f"✅ Pair: *{pair}*\n\n"
            "Ab trade idea detail mein likhein:\n"
            "Entry level, SL, TP, reason for trade...",
            parse_mode="Markdown"
        )
        return IDEA_CONTENT

    async def idea_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        content = update.message.text.strip()
        idea = context.user_data["idea"]
        
        idea_id = self.db.add_trade_idea(
            update.effective_user.id,
            idea["pair"],
            content
        )
        
        await update.message.reply_text(
            f"💡 *Trade Idea #{idea_id} Saved!*\n\n"
            f"💱 Pair: *{idea['pair']}*\n"
            f"📝 Idea: {content[:150]}{'...' if len(content) > 150 else ''}\n\n"
            f"_Jab execute karo tab `/addtrade` use karein!_",
            parse_mode="Markdown"
        )
        context.user_data.pop("idea", None)
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancel ho gaya.")
        return ConversationHandler.END
