import asyncio
import threading
import logging
import rumps
from AppKit import NSApp
from functools import partial
from whisper_client import status
from whisper_client.settings import save


ICONS = {
    status.STARTING: "⚪",
    status.READY: "🟢",
    status.RECORDING: "🔴",
    status.TRANSCRIBING: "🟠",
    status.ERROR: "⚠️",
}
LANGUAGE_NAMES = {"fr": "Français", "en": "English"}

log = logging.getLogger(__name__)


class Backend:
    """Runs the asyncio part in its own thread."""

    def __init__(self, main):
        self.main = main

    def start(self):
        self.thread = threading.Thread(target=asyncio.run, args=(self._run(),))
        self.thread.start()

    async def _run(self):
        self.loop = asyncio.get_running_loop()
        self.task = asyncio.current_task()
        try:
            await self.main()
        except BaseException:
            status.set(status.ERROR)
            raise

    def stop(self):
        self.loop.call_soon_threadsafe(self.task.cancel)
        self.thread.join(timeout=10)

class App(rumps.App):
    def __init__(self, backend, settings):
        super().__init__(ICONS[status.STARTING], quit_button=None)
        self.backend = backend
        self.settings = settings
        self.language_menu = rumps.MenuItem("Language")
        self.model_menu = rumps.MenuItem("Models")
        self.vocabulary_menu = rumps.MenuItem("Vocabulaire")
        self.menu = [self.language_menu, self.model_menu, self.vocabulary_menu, None, "Quitter"]
        self.build_language_menu()
        self.build_vocabulary_menu()

        self.model_menu.add(rumps.MenuItem("Loading..."))
        self.models_loaded = False


    def check_only(self, menu, title):
        for item in menu.values():
            item.state = item.title == title

    def build_language_menu(self):
        for code, name in LANGUAGE_NAMES.items():
            item = rumps.MenuItem(name, callback=partial(self.choose_language, code))
            item.state = code == self.settings.language
            self.language_menu.add(item)

    def build_model_menu(self):
        self.model_menu.clear()
        if len(status.models) == 0:
            return
        for model in status.models:
            item = rumps.MenuItem(model, callback=partial(self.choose_model, model))
            item.state = model == self.settings.model
            self.model_menu.add(item)

    def build_vocabulary_menu(self):
        if len(self.vocabulary_menu):
               self.vocabulary_menu.clear()
        for term in self.settings.vocabulary:
            self.vocabulary_menu.add(rumps.MenuItem(term, callback=partial(self.remove_term, term)))
        if self.settings.vocabulary:
            self.vocabulary_menu.add(rumps.separator)
        self.vocabulary_menu.add(rumps.MenuItem("Add a term", callback=self.add_term))

    def add_term(self, _sender):
        window = rumps.Window(
            title="Add a term",
            message="Word, or name that whisper should know how to spell.\nEx. : AWS, Kubernetes, pytest",
            ok="Add",
            cancel="Cancel",
            dimensions=(260, 24),
        )
        NSApp.activateIgnoringOtherApps_(True)
        response = window.run()
        term = response.text
        if not response.clicked or not term or term in self.settings.vocabulary:
            return
        self.settings.vocabulary = self.settings.vocabulary + [term]
        save(self.settings)
        self.build_vocabulary_menu()

    def remove_term(self, term, _sender):
        self.settings.vocabulary = [t for t in self.settings.vocabulary if t != term]
        save(self.settings)

    def choose_language(self, code, _sender):
        self.settings.language = code
        save(self.settings)
        self.check_only(self.language_menu, LANGUAGE_NAMES[code])

    def choose_model(self, model, _sender):
        self.settings.model = model
        save(self.settings)
        self.check_only(self.model_menu, model)


    @rumps.timer(0.2)
    def refresh(self, _):
        self.title = ICONS[status.current]
        if not self.models_loaded and len(status.models) > 0:
            self.build_model_menu()
            self.models_loaded = True

    @rumps.clicked("Quitter")
    def quit(self, _):
        self.backend.stop()
        rumps.quit_application()
