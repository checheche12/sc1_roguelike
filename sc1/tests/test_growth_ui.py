"""Withdrawn Tk widgets only: read-only checks, not a visual/gameplay claim."""
from pathlib import Path
import gc
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from sc1.manager.ui import ManagerWindow


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class GrowthWindowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sc1-growth-ui-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ManagerWindow(self.root, Path(self.tmp.name) / "original.sqlite3")

    def tearDown(self):
        # Release all Tcl references on their owning thread before later
        # SQLite concurrency tests can trigger cyclic garbage collection.
        self.app.closed = True
        for timer in self.root.tk.call("after", "info"):
            self.root.after_cancel(timer)
        self.root.destroy()
        self.app = None
        self.root = None
        gc.collect()

    def inspect_hidden_read_only_dialog(self):
        original_toplevel = tk.Toplevel
        windows, labels, errors = [], [], []
        before = self.app.store.path.read_bytes()

        def hidden_toplevel(*args, **kwargs):
            dialog = original_toplevel(*args, **kwargs)
            dialog.withdraw()
            windows.append(dialog)
            return dialog

        def inspect():
            dialog = windows[0]
            try:
                self.assertEqual(self.root.state(), "withdrawn")
                self.assertEqual(dialog.state(), "withdrawn")
                widgets = list(descendants(dialog))
                self.assertFalse(any(isinstance(widget, ttk.Radiobutton) for widget in widgets))
                buttons = [widget for widget in widgets if isinstance(widget, ttk.Button)]
                self.assertEqual([str(widget.cget("text")) for widget in buttons], ["닫기"])
                for widget in widgets:
                    if isinstance(widget, ttk.Label):
                        variable = str(widget.cget("textvariable"))
                        labels.append(str(widget.getvar(variable)) if variable else str(widget.cget("text")))
                buttons[0].invoke()
            except BaseException as exc:
                errors.append(exc)
                dialog.destroy()

        self.root.after(1, inspect)
        with (patch("sc1.manager.ui.tk.Toplevel", side_effect=hidden_toplevel),
              patch.object(self.app.store, "prepare_growth", side_effect=AssertionError("viewer must not prepare")) as prepare,
              patch.object(self.app.store, "choose_growth", side_effect=AssertionError("viewer must not choose")) as choose,
              patch.object(self.app.store, "choose_growth_slot", side_effect=AssertionError("viewer must not choose slot")) as choose_slot):
            self.app.show_growth()
        if errors:
            raise errors[0]
        prepare.assert_not_called()
        choose.assert_not_called()
        choose_slot.assert_not_called()
        self.assertEqual(self.app.store.path.read_bytes(), before)
        self.assertEqual(self.app.growth_button.cget("text"), "보유 재능·저주 보기")
        self.assertTrue(any("게임 안에서 선택" in label for label in labels))
        return labels

    def test_unprepared_record_view_does_not_create_growth_or_offer(self):
        labels = self.inspect_hidden_read_only_dialog()
        self.assertTrue(any("선택 결과는 자동으로 저장됩니다." in label for label in labels))
        self.assertEqual(self.app.store.growth_status()["state"], "not_started")

    def test_pending_record_view_shows_counts_but_no_candidates_or_selection(self):
        state = self.app.store.prepare_growth()
        labels = self.inspect_hidden_read_only_dialog()
        self.assertTrue(any("재능 3회·저주 2회" in label for label in labels))
        for candidate in state["offer"]["candidates"]:
            self.assertNotIn(candidate["name"], labels)
        self.assertEqual(self.app.store.growth_status(), state)

    def test_owned_record_view_preserves_prior_choices_and_shows_stacks(self):
        state = self.app.store.prepare_growth()
        while state["offer"]:
            offer = state["offer"]
            state = self.app.store.choose_growth_slot(offer["offer_id"], 1, offer["revision"], choice_kind=1 if offer["kind"] == "talent" else 2)
        labels = self.inspect_hidden_read_only_dialog()
        for curse in state["curses"]:
            self.assertTrue(any(f"{curse['name']} · {curse['stacks']}중첩" == label for label in labels))
        self.assertTrue(all(item["name"] in labels for item in state["talents"]))
        self.assertEqual(len(self.app.store.growth_status()["history"]), 5)

    def test_growth_wait_event_directs_selection_to_game(self):
        self.app.update_connection_status('{"status":"waiting_for_choices"}')
        self.assertIn("게임 안에서 재능·저주 선택", self.app.connection.get())
        self.assertNotIn("관리자에서", self.app.connection.get())
        self.assertIsNone(self.app.last_connection_error)

    def test_ingame_offer_and_wait_statuses_only_update_connection_text(self):
        before = self.app.store.path.read_bytes()
        with (patch.object(self.app.store, "prepare_growth", side_effect=AssertionError("status must not prepare")) as prepare,
              patch.object(self.app.store, "choose_growth", side_effect=AssertionError("status must not choose")) as choose,
              patch.object(self.app.store, "choose_growth_slot", side_effect=AssertionError("status must not choose slot")) as choose_slot):
            for status in ("choice_offered", "waiting_for_ingame_choice"):
                with self.subTest(status=status):
                    self.app.update_connection_status('{"status":"' + status + '"}')
                    self.assertIn("게임 안", self.app.connection.get())
                    self.assertIn("재능·저주 선택", self.app.connection.get())
                    self.assertNotIn("관리자에서", self.app.connection.get())
                    self.assertIsNone(self.app.last_connection_error)
        prepare.assert_not_called()
        choose.assert_not_called()
        choose_slot.assert_not_called()
        self.assertEqual(self.app.store.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
