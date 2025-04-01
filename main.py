from pyrogram import Client, filters
from pyrogram.raw.functions.account import ReportPeer
from pyrogram.raw.types import (
    InputReportReasonChildAbuse, InputReportReasonFake, 
    InputReportReasonCopyright, InputReportReasonGeoIrrelevant, 
    InputReportReasonOther, InputPeerChannel
)
from loguru import logger
from config import *


logger.add("bot.log", rotation="1 MB", level="DEBUG")
# Custom Channel ID & Access Hash

CUSTOM_CHANNEL_ID = -1002165645213  # Replace with your actual channel ID
CUSTOM_ACCESS_HASH = 1234567890123456789  # Replace with the actual access hash

def get_custom_peer():
    return InputPeerChannel(CUSTOM_CHANNEL_ID, CUSTOM_ACCESS_HASH)

# Create the client with a name
app = Client(
    "bot",
    api_id=api_id,
    api_hash=api_hash,
    session_string=session
)

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

def format_peer_id(peer_id):
    """Format peer ID to handle both user and channel IDs"""
    if str(peer_id).startswith('-100'):
        # For channels, we need to remove the -100 prefix and use the channel ID directly
        channel_id = int(str(peer_id)[4:])
        access_hash = 0  # This will be filled by resolve_peer
        return InputPeerChannel(channel_id=channel_id, access_hash=access_hash)
    return peer_id

# Add a handler for all messages to debug
@app.on_message()
async def debug_messages(client, message):
    logger.debug(f"Received message: {message.text} from {message.from_user.id if message.from_user else 'Unknown'}")

@app.on_message(filters.command("start"))
async def start_command(client, message):
    logger.info(f"Received start command from user {message.from_user.id}")
    try:
        await message.reply("Hello! I'm a reporting bot. Use /report <user_id/channel_id> <message_id> <reason> to report content.\n\nAvailable reasons:\n- child_abuse\n- impersonation\n- copyrighted_content\n- irrelevant_geogroup\n- other")
        logger.info("Start message sent successfully")
    except Exception as e:
        logger.error(f"Error sending start message: {str(e)}")

@app.on_message(filters.command("report"))
async def report_user(client, message):
    try:
        logger.info(f"Received /report command from user {message.from_user.id}")
        logger.info(f"Full command text: {message.text}")

        command = message.text.split(maxsplit=3)
        logger.info(f"Split command: {command}")
        
        if len(command) != 4:
            await message.reply("Usage: /report <user_id/channel_id> <message_id> <reason>")
            logger.warning("Invalid command format")
            return

        try:
            peer_id = int(command[1])
            message_id = int(command[2])
            logger.info(f"Parsed peer_id: {peer_id}, message_id: {message_id}")
        except ValueError as e:
            logger.error(f"Error parsing IDs: {str(e)}")
            await message.reply("Peer ID and Message ID must be integers.")
            logger.warning("Invalid Peer ID or Message ID format")
            return

        reason_text = command[3]
        logger.info(f"Report reason: {reason_text}")
        reason = get_report_reason(reason_text)
        logger.info(f"Attempting to report peer {peer_id} for message {message_id} with reason {reason_text}")

        try:
            # First try to resolve the peer directly
            logger.info("Attempting direct peer resolution...")
            peer = await client.resolve_peer(peer_id)
            logger.info("Direct peer resolution successful")
        except Exception as e:
            logger.warning(f"Failed to resolve peer directly: {str(e)}")
            try:
                # If direct resolution fails, try with formatted peer ID
                logger.info("Attempting formatted peer resolution...")
                formatted_peer = format_peer_id(peer_id)
                if isinstance(formatted_peer, InputPeerChannel):
                    # For channels, we need to get the channel info first
                    logger.info("Getting channel info...")
                    channel = await client.get_chat(peer_id)
                    logger.info(f"Got channel info: {channel.title}")
                    peer = await client.resolve_peer(channel.id)
                else:
                    peer = await client.resolve_peer(formatted_peer)
                logger.info("Formatted peer resolution successful")
            except Exception as e:
                logger.error(f"Failed to resolve peer with formatted ID: {str(e)}")
                await message.reply("Failed to resolve the peer. Make sure the ID is correct and the bot has access to the channel.")
                return
            
        logger.info(f"Resolved peer information for ID {peer_id}")

        try:
            logger.info("Creating report peer object...")
            report_peer = ReportPeer(
                peer=peer, 
                reason=reason, 
                message="Reported for inappropriate content."
            )
            logger.info("Invoking report...")
            result = await client.invoke(report_peer)
            logger.info(f"Report invocation result: {result}")

            if result:
                await message.reply("Peer reported successfully.")
                logger.info(f"Successfully reported peer {peer_id} for message {message_id}")
            else:
                await message.reply("Failed to report the peer.")
                logger.error(f"Failed to report peer {peer_id} for message {message_id}")
        except Exception as e:
            logger.error(f"Error during report invocation: {str(e)}")
            await message.reply("Failed to send the report. The bot might not have permission to report this peer.")

    except Exception as e:
        logger.exception("An error occurred while reporting the peer")
        await message.reply(f"An error occurred: {str(e)}")

async def main():
    logger.info("Starting bot...")
    try:
        await app.start()
        logger.info("Bot started successfully!")
        logger.info(f"Bot username: {(await app.get_me()).username}")
        await app.idle()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
    finally:
        await app.stop()

# Run the bot
logger.info("Initializing bot...")
app.run()

