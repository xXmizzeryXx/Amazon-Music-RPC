import asyncio
import time
import sys
import logging
from typing import Optional, Tuple

try:
    import psutil
except ImportError:
    sys.exit("Missing: pip install psutil")

try:
    from pypresence import Presence, DiscordNotFound
except ImportError:
    sys.exit("Missing: pip install pypresence")

try:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    )
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )
except ImportError:
    sys.exit("Missing: pip install winsdk\n  (requires Windows 10 1903+ and Python 3.9+)")

DISCORD_CLIENT_ID = "YOUR_DISCORD_CLIENT_ID_HERE"
POLL_INTERVAL = 3
LARGE_IMAGE_KEY = "amazon_music_logo"
LARGE_IMAGE_TEXT = "Amazon Music"
FILTER_APP_NAME = "AmazonMobileLLC"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("amazon_rpc")


async def _get_smtc_track() -> Optional[Tuple[str, str, str, bool, Optional[int], Optional[int]]]:
    sessions = await SessionManager.request_async()
    current = sessions.get_current_session()

    candidates = []
    if current:
        candidates.append(current)

    for s in sessions.get_sessions():
        try:
            app_id = s.source_app_user_model_id or ""
            if s is not current and (
                FILTER_APP_NAME is None
                or FILTER_APP_NAME.lower() in app_id.lower()
            ):
                candidates.append(s)
        except Exception:
            pass

    for session in candidates:
        try:
            app_id = session.source_app_user_model_id or ""
            if FILTER_APP_NAME and FILTER_APP_NAME.lower() not in app_id.lower():
                continue

            info = await session.try_get_media_properties_async()
            if not info or (not info.title and not info.artist):
                continue

            playback = session.get_playback_info()
            is_playing = (
                playback is not None
                and playback.playback_status == PlaybackStatus.PLAYING
            )

            position_sec = None
            duration_sec = None
            try:
                timeline = session.get_timeline_properties()
                if timeline:
                    pos_100ns = timeline.position.duration
                    dur_100ns = timeline.end_time.duration
                    if dur_100ns > 0:
                        position_sec = int(pos_100ns / 10_000_000)
                        duration_sec = int(dur_100ns / 10_000_000)
            except Exception as exc:
                log.debug("Timeline read error: %s", exc)

            return (
                info.title or "",
                info.artist or "Unknown Artist",
                info.album_title or "",
                is_playing,
                position_sec,
                duration_sec,
            )
        except Exception as exc:
            log.debug("Session read error: %s", exc)

    return None


def get_now_playing() -> Optional[Tuple[str, str, str, bool, Optional[int], Optional[int]]]:
    try:
        return asyncio.run(_get_smtc_track())
    except Exception as exc:
        log.debug("SMTC error: %s", exc)
        return None


def main() -> None:
    if DISCORD_CLIENT_ID == "YOUR_DISCORD_CLIENT_ID_HERE":
        log.error(
            "\n"
            "  !! Set your Discord Client ID first !!\n"
            "  1. https://discord.com/developers/applications\n"
            "  2. New Application -> copy the Application ID\n"
            "  3. Paste it into DISCORD_CLIENT_ID at the top of this script\n"
        )
        sys.exit(1)

    rpc: Optional[Presence] = None
    connected = False
    last_track_key: Optional[str] = None
    start_timestamp: Optional[int] = None

    log.info("Amazon Music -> Discord RPC started (polling every %ds).", POLL_INTERVAL)

    while True:
        if not connected:
            try:
                rpc = Presence(DISCORD_CLIENT_ID)
                rpc.connect()
                connected = True
                log.info("Connected to Discord RPC.")
            except DiscordNotFound:
                log.warning("Discord not running - retrying in 15s...")
                time.sleep(15)
                continue
            except Exception as exc:
                log.warning("Discord connect error (%s) - retrying in 15s...", exc)
                time.sleep(15)
                continue

        track = get_now_playing()

        try:
            if track:
                title, artist, album, is_playing, position_sec, duration_sec = track
                track_key = f"{title}||{artist}"

                if track_key != last_track_key:
                    last_track_key = track_key
                    log.info(
                        "%s  %s - %s%s",
                        ">" if is_playing else "||",
                        title or "(no title)",
                        artist,
                        f"  [{album}]" if album else "",
                    )

                now = int(time.time())
                if is_playing and position_sec is not None and duration_sec is not None:
                    ts_start = now - position_sec
                    ts_end = now - position_sec + duration_sec
                elif is_playing:
                    if last_track_key != track_key or start_timestamp is None:
                        start_timestamp = now
                    ts_start = start_timestamp
                    ts_end = None
                else:
                    ts_start = None
                    ts_end = None

                start_timestamp = ts_start

                if title:
                    details = title
                    state_line = f"by {artist}"
                    if album:
                        state_line += f" · {album}"
                else:
                    details = artist
                    state_line = album if album else "Amazon Music"

                rpc.update(
                    details=details,
                    state=state_line,
                    start=ts_start,
                    end=ts_end,
                    large_image=LARGE_IMAGE_KEY,
                    large_text=LARGE_IMAGE_TEXT,
                    small_image="playing" if is_playing else "paused",
                    small_text="Playing" if is_playing else "Paused",
                )

            else:
                if last_track_key is not None:
                    log.info("No Amazon Music session - clearing presence.")
                    rpc.clear()
                    last_track_key = None
                    start_timestamp = None

        except (BrokenPipeError, ConnectionResetError, OSError) as exc:
            log.warning("Discord RPC disconnected (%s) - reconnecting...", exc)
            connected = False
            last_track_key = None
            try:
                rpc.close()
            except Exception:
                pass

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Stopped.")
