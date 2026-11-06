import asyncio

from AppKit import NSPasteboard, NSPasteboardTypeString # pyright: ignore[reportAttributeAccessIssue]
from pynput.keyboard import Controller, Key

pasteboard = NSPasteboard.generalPasteboard()

# Créé à l'import, donc dans le thread principal : son constructeur interroge
# macOS sur la disposition du clavier, ce qui est interdit hors du thread principal.
keyboard = Controller()

async def inject(text):
    previous_content = pasteboard.stringForType_(NSPasteboardTypeString)
    try:
        pasteboard.clearContents()
        pasteboard.setString_forType_(text, NSPasteboardTypeString)
        paste()
        await asyncio.sleep(0.3)
    finally:
        restore(previous_content)

def paste():
    with keyboard.pressed(Key.cmd):
            keyboard.tap("v")

def restore(previous_content):
    if previous_content is not None:
        pasteboard.clearContents()
        pasteboard.setString_forType_(previous_content, NSPasteboardTypeString)
