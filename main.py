from pyrogram import Client, filters
from pyrogram.raw.functions.account import ReportPeer
from pyrogram.raw.types import (
    InputReportReasonChildAbuse, InputReportReasonFake, 
    InputReportReasonCopyright, InputReportReasonGeoIrrelevant, 
    InputReportReasonOther
)
from loguru import logger
from config import *


logger.add("bot.log", rotation="1 MB")

app = Client("bot", api_id=api_id, api_hash=api_hash, session_string=session)

def get_report_reason(text):
    if text == "child_abuse":
        return InputReportReasonChildAbuse()
    elif text == "impersonation":
        return InputReportReasonFake()
    elif text == "copyrighted_content":
        return InputReportReasonCopyright()
    elif text == "irrelevant_geogroup":
        return InputReportReasonGeoIrrelevant()
    else:
        return InputReportReasonOther()

@app.on_message(filters.command("report") & filters.private)
async def report_user(client, message):
    try:
        logger.info(f"Received /report command from user {message.from_user.id}")

        command = message.text.split(maxsplit=3)
        if len(command) != 4:
            await message.reply("Usage: /report <user_id> <message_id> <reason>")
            logger.warning("Invalid command format")
            return

        try:
            user_id = int(command[1])
            message_id = int(command[2])
        except ValueError:
            await message.reply("User ID and Message ID must be integers.")
            logger.warning("Invalid User ID or Message ID format")
            return

        reason_text = command[3]
        reason = get_report_reason(reason_text)
        logger.info(f"Attempting to report user {user_id} for message {message_id} with reason {reason_text}")

        peer = await client.resolve_peer(user_id)
        logger.info(f"Resolved peer information for user {user_id}")

   
        report_peer = ReportPeer(
            peer=peer, 
            reason=reason, 
            message="Reported for inappropriate content."
        )

        result = await client.invoke(report_peer)

        if result:
            await message.reply("User reported successfully.")
            logger.info(f"Successfully reported user {user_id} for message {message_id}")
        else:
            await message.reply("Failed to report the user.")
            logger.error(f"Failed to report user {user_id} for message {message_id}")

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
        logger.exception("An error occurred while reporting the user")

logger.info("Starting bot")
app.run()
