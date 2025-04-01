from pyrogram import Client, filters
from pyrogram.raw.functions.account import ReportPeer
from pyrogram.raw.types import (
    InputReportReasonChildAbuse, InputReportReasonFake, 
    InputReportReasonCopyright, InputReportReasonGeoIrrelevant, 
    InputReportReasonOther, InputPeerChannel
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

def format_peer_id(peer_id):
    """Format peer ID to handle both user and channel IDs"""
    if str(peer_id).startswith('-100'):
        # For channels, we need to remove the -100 prefix and use the channel ID directly
        channel_id = int(str(peer_id)[4:])
        access_hash = 0  # This will be filled by resolve_peer
        return InputPeerChannel(channel_id=channel_id, access_hash=access_hash)
    return peer_id

@app.on_message(filters.command("report") & filters.private)
async def report_user(client, message):
    try:
        logger.info(f"Received /report command from user {message.from_user.id}")

        command = message.text.split(maxsplit=3)
        if len(command) != 4:
            await message.reply("Usage: /report <user_id/channel_id> <message_id> <reason>")
            logger.warning("Invalid command format")
            return

        try:
            peer_id = int(command[1])
            message_id = int(command[2])
        except ValueError:
            await message.reply("Peer ID and Message ID must be integers.")
            logger.warning("Invalid Peer ID or Message ID format")
            return

        reason_text = command[3]
        reason = get_report_reason(reason_text)
        logger.info(f"Attempting to report peer {peer_id} for message {message_id} with reason {reason_text}")

        try:
            # First try to resolve the peer directly
            peer = await client.resolve_peer(peer_id)
        except Exception as e:
            logger.warning(f"Failed to resolve peer directly: {str(e)}")
            try:
                # If direct resolution fails, try with formatted peer ID
                formatted_peer = format_peer_id(peer_id)
                if isinstance(formatted_peer, InputPeerChannel):
                    # For channels, we need to get the channel info first
                    channel = await client.get_chat(peer_id)
                    peer = await client.resolve_peer(channel.id)
                else:
                    peer = await client.resolve_peer(formatted_peer)
            except Exception as e:
                logger.error(f"Failed to resolve peer with formatted ID: {str(e)}")
                await message.reply("Failed to resolve the peer. Make sure the ID is correct and the bot has access to the channel.")
                return
            
        logger.info(f"Resolved peer information for ID {peer_id}")

        try:
            report_peer = ReportPeer(
                peer=peer, 
                reason=reason, 
                message="Reported for inappropriate content."
            )

            result = await client.invoke(report_peer)

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
        await message.reply(f"An error occurred: {str(e)}")
        logger.exception("An error occurred while reporting the peer")

# Ignore updates from channels we haven't interacted with
@app.on_message(filters.channel)
async def ignore_channel_updates(client, message):
    pass

logger.info("Starting bot")
app.run()
