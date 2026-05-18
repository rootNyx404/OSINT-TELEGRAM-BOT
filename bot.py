import re
import logging
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

logging.basicConfig(level=logging.INFO)

def extract_phone_number(text: str):
    cleaned = re.sub(r"[^\d+]", "", text)

    if not cleaned.startswith("+"):
        return None

    if len(cleaned) < 8 or len(cleaned) > 16:
        return None

    return cleaned

def get_number_type_name(num_type):
    types = {
        phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
        phonenumbers.PhoneNumberType.MOBILE: "Mobile",
        phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed/Mobile",
        phonenumbers.PhoneNumberType.TOLL_FREE: "Toll-Free",
        phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
        phonenumbers.PhoneNumberType.VOIP: "VoIP",
        phonenumbers.PhoneNumberType.UNKNOWN: "Unknown",
    }
    return types.get(num_type, "Unknown")

def analyze_phone_number(phone_number: str):
    try:
        parsed = phonenumbers.parse(phone_number, None)

        return {
            "valid": phonenumbers.is_valid_number(parsed),
            "possible": phonenumbers.is_possible_number(parsed),
            "country_code": parsed.country_code,
            "national_number": parsed.national_number,
            "international_format": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
            "national_format": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            ),
            "country": geocoder.country_name_for_number(parsed, "en"),
            "region": geocoder.description_for_number(parsed, "en"),
            "carrier": carrier.name_for_number(parsed, "en"),
            "timezone": ", ".join(timezone.time_zones_for_number(parsed)),
            "number_type": get_number_type_name(phonenumbers.number_type(parsed)),
        }

    except Exception as e:
        return {"error": str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🌍 Phone Number Validation Bot

Send a phone number with country code.

Example:
+919876543210
+14155552671

This bot only shows basic public telecom metadata.
"""
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
How to use:

1. Send a number with country code.
2. Example: +8801712345678
3. Bot will check validity, country, carrier, timezone, and number type.

Use only for educational or authorized purposes.
"""
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    phone_number = extract_phone_number(user_text)

    if not phone_number:
        await update.message.reply_text(
            "Invalid format. Please send number with country code, like +919876543210"
        )
        return

    info = analyze_phone_number(phone_number)

    if "error" in info:
        await update.message.reply_text(f"Error: {info['error']}")
        return

    result = f"""
📱 Phone Number Analysis

Number: {info['international_format']}
Valid: {info['valid']}
Possible: {info['possible']}

🌍 Country: {info['country']}
📍 Region: {info['region']}
📞 Carrier: {info['carrier'] or "Unknown"}
🕒 Timezone: {info['timezone']}
🔢 Type: {info['number_type']}

Country Code: +{info['country_code']}
National Number: {info['national_number']}
National Format: {info['national_format']}
"""
    await update.message.reply_text(result)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
