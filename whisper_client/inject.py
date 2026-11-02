import asyncio

from AppKit import NSPasteboard, NSPasteboardTypeString # pyright: ignore[reportAttributeAccessIssue]
from pynput.keyboard import Controller, Key

pasteboard = NSPasteboard.generalPasteboard()

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
    clavier = Controller()
    with clavier.pressed(Key.cmd):
        clavier.tap("v")

def restore(previous_content):
    if previous_content is not None:
        pasteboard.clearContents()
        pasteboard.setString_forType_(previous_content, NSPasteboardTypeString)
