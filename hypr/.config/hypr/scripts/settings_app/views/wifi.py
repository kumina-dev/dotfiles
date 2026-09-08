from gi.repository import Gtk, Gdk

from .. import network
from ..async_utils import run_async


class WifiView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self._refreshing = False
        self._ignore_toggle = False

        self.get_style_context().add_class(
            "content"
        )

        self.build()

    def build(self):
        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        titles = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
        )

        title = Gtk.Label(
            label="Wi-Fi"
        )

        title.set_halign(
            Gtk.Align.START
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Manage wireless networks "
                "and connections."
            )
        )

        description.set_halign(
            Gtk.Align.START
        )

        description.get_style_context().add_class(
            "page-description"
        )

        titles.pack_start(
            title,
            False,
            False,
            0,
        )

        titles.pack_start(
            description,
            False,
            False,
            0,
        )

        self.refresh_button = Gtk.Button(
            label="󰑓"
        )

        self.refresh_button.set_tooltip_text(
            "Refresh networks"
        )

        self.refresh_button.connect(
            "clicked",
            lambda _button: self.refresh(),
        )

        header.pack_start(
            titles,
            True,
            True,
            0,
        )

        header.pack_end(
            self.refresh_button,
            False,
            False,
            0,
        )

        self.pack_start(
            header,
            False,
            False,
            0,
        )

        self.build_status_card()
        self.build_network_list()

    def build_status_card(self):
        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        label = Gtk.Label(
            label="Wi-Fi"
        )

        label.set_halign(
            Gtk.Align.START
        )

        self.toggle = Gtk.Switch()

        self.toggle.set_halign(
            Gtk.Align.END
        )

        self.toggle.connect(
            "notify::active",
            self.toggle_changed,
        )

        row.pack_start(
            label,
            True,
            True,
            0,
        )

        row.pack_end(
            self.toggle,
            False,
            False,
            0,
        )

        self.status_label = Gtk.Label(
            label="Loading…"
        )

        self.status_label.set_halign(
            Gtk.Align.START
        )

        self.status_label.get_style_context().add_class(
            "page-description"
        )

        card.pack_start(
            row,
            False,
            False,
            0,
        )

        card.pack_start(
            self.status_label,
            False,
            False,
            0,
        )

        self.pack_start(
            card,
            False,
            False,
            0,
        )

    def build_network_list(self):
        self.saved_title = Gtk.Label(
            label="Known Networks"
        )

        self.saved_title.set_halign(
            Gtk.Align.START
        )

        self.saved_title.get_style_context().add_class(
            "section-title"
        )

        self.pack_start(
            self.saved_title,
            False,
            False,
            0,
        )

        self.saved_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
        )

        self.saved_box.get_style_context().add_class(
            "network-list"
        )

        self.pack_start(
            self.saved_box,
            False,
            False,
            0,
        )

        self.other_title = Gtk.Label(
            label="Other Networks"
        )

        self.other_title.set_halign(
            Gtk.Align.START
        )

        self.other_title.get_style_context().add_class(
            "section-title"
        )

        self.pack_start(
            self.other_title,
            False,
            False,
            0,
        )

        self.scroller = Gtk.ScrolledWindow()

        self.scroller.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC,
        )

        self.scroller.set_hexpand(True)
        self.scroller.set_vexpand(True)

        self.other_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
        )

        self.other_box.get_style_context().add_class(
            "network-list"
        )

        self.scroller.add(
            self.other_box
        )

        self.pack_start(
            self.scroller,
            True,
            True,
            0,
        )

    def refresh(self):
        if self._refreshing:
            return

        self._refreshing = True

        self.refresh_button.set_sensitive(
            False
        )

        self.clear_networks()

        self.saved_title.hide()
        self.other_title.hide()

        loading = Gtk.Label(
            label="Searching for networks..."
        )

        loading.set_halign(
            Gtk.Align.START
        )

        loading.get_style_context().add_class(
            "page-description"
        )

        self.other_box.pack_start(
            loading,
            False,
            False,
            12,
        )

        self.other_box.show_all()

        run_async(
            network.get_state,
            self.apply_state,
            self.refresh_failed,
        )

    def apply_state(
        self,
        state,
    ):
        self._refreshing = False

        self.refresh_button.set_sensitive(
            True
        )

        enabled = state["enabled"]

        self._ignore_toggle = True
        self.toggle.set_active(enabled)
        self._ignore_toggle = False

        if not enabled:
            self.status_label.set_text(
                "Wi-Fi is turned off."
            )

            self.clear_networks()

            self.saved_title.hide()
            self.other_title.hide()

            disabled = Gtk.Label(
                label=(
                    "Turn on Wi-Fi to see "
                    "available networks."
                )
            )

            disabled.set_halign(
                Gtk.Align.START
            )

            disabled.get_style_context().add_class(
                "page-description"
            )

            self.other_box.pack_start(
                disabled,
                False,
                False,
                12,
            )

            self.other_box.show_all()

            return False

        ssid = state["ssid"]

        if ssid:
            self.status_label.set_text(
                f"Connected to {ssid}"
            )
        else:
            self.status_label.set_text(
                "Not connected"
            )

        self.render_networks(
            state["networks"]
        )

        return False

    def refresh_failed(
        self,
        error,
    ):
        self._refreshing = False

        self.refresh_button.set_sensitive(
            True
        )

        self.status_label.set_text(
            "Unable to load Wi-Fi state."
        )

        self.clear_networks()

        self.saved_title.hide()
        self.other_title.hide()

        label = Gtk.Label(
            label=str(error)
        )

        label.set_halign(
            Gtk.Align.START
        )

        self.other_box.pack_start(
            label,
            False,
            False,
            12,
        )

        self.other_box.show_all()

        return False

    def render_networks(
        self,
        networks,
    ):
        self.clear_networks()

        saved = [
            item
            for item in networks
            if item["saved"]
        ]

        other = [
            item
            for item in networks
            if not item["saved"]
        ]

        if saved:
            self.saved_title.show()

            for item in saved:
                self.add_network(
                    self.saved_box,
                    item,
                )
        else:
            self.saved_title.hide()

        if other:
            self.other_title.show()

            for item in other:
                self.add_network(
                    self.other_box,
                    item,
                )
        else:
            self.other_title.hide()

        if (
            not saved
            and not other
        ):
            label = Gtk.Label(
                label="No networks found."
            )

            label.set_halign(
                Gtk.Align.START
            )

            label.get_style_context().add_class(
                "page-description"
            )

            self.other_box.pack_start(
                label,
                False,
                False,
                12,
            )

            self.other_title.show()

        self.saved_box.show_all()
        self.other_box.show_all()

    def add_network(
        self,
        container,
        item,
    ):
        outer = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )

        outer.get_style_context().add_class(
            "network-row"
        )

        content = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        icon = Gtk.Label(
            label=self.signal_icon(
                item["signal"]
            )
        )

        name = Gtk.Label(
            label=item["ssid"]
        )

        name.set_halign(
            Gtk.Align.START
        )

        name.set_xalign(0)

        content.pack_start(
            icon,
            False,
            False,
            0,
        )

        content.pack_start(
            name,
            True,
            True,
            0,
        )

        if item["connected"]:
            status = Gtk.Label(
                label="Connected"
            )

            status.get_style_context().add_class(
                "connected-label"
            )

            content.pack_end(
                status,
                False,
                False,
                0,
            )

        elif item["secured"]:
            lock = Gtk.Label(
                label="󰌾"
            )

            content.pack_end(
                lock,
                False,
                False,
                0,
            )

        click_area = Gtk.EventBox()

        click_area.set_visible_window(
            False
        )

        click_area.add(
            content
        )

        click_area.connect(
            "button-release-event",
            self.network_clicked,
            item,
        )

        outer.pack_start(
            click_area,
            True,
            True,
            0,
        )

        if item["saved"]:
            menu_button = Gtk.Button(
                label="⋮"
            )

            menu_button.get_style_context().add_class(
                "network-action"
            )

            menu_button.connect(
                "clicked",
                self.show_network_menu,
                item,
            )

            outer.pack_end(
                menu_button,
                False,
                False,
                0,
            )

        container.pack_start(
            outer,
            False,
            False,
            0,
        )

    def network_clicked(
        self,
        _widget,
        _event,
        item,
    ):
        if item["connected"]:
            return

        if item["saved"]:
            run_async(
                lambda: network.connect_saved(
                    item["profile_uuid"]
                ),
                self.connection_finished,
                self.operation_failed,
            )

            return False

        if item["secured"]:
            self.show_password_dialog(
                item["ssid"],
            )

            return False

        run_async(
            lambda: network.connect_new(
                item["ssid"]
            ),
            self.connection_finished,
            self.operation_failed,
        )

        return False

    def show_password_dialog(
        self,
        ssid,
    ):
        dialog = Gtk.Dialog(
            title=f"Connect to {ssid}",
            transient_for=self.get_toplevel(),
            modal=True,
        )

        dialog.add_button(
            "Cancel",
            Gtk.ResponseType.CANCEL,
        )

        dialog.add_button(
            "Connect",
            Gtk.ResponseType.OK,
        )

        content = (
            dialog.get_content_area()
        )

        content.set_spacing(12)
        content.set_border_width(18)

        label = Gtk.Label(
            label=f"Password for {ssid}"
        )

        label.set_halign(
            Gtk.Align.START
        )

        entry = Gtk.Entry()

        entry.set_visibility(False)

        entry.set_activates_default(
            True
        )

        entry.set_placeholder_text(
            "Password"
        )

        dialog.set_default_response(
            Gtk.ResponseType.OK
        )

        content.pack_start(
            label,
            False,
            False,
            0,
        )

        content.pack_start(
            entry,
            False,
            False,
            0,
        )

        dialog.show_all()

        response = dialog.run()

        password = entry.get_text()

        dialog.destroy()

        if (
            response
            != Gtk.ResponseType.OK
        ):
            return

        if not password:
            return

        run_async(
            lambda: network.connect_new(
                ssid,
                password,
            ),
            self.connection_finished,
            self.operation_failed,
        )

    def connection_finished(
        self,
        result,
    ):
        if result.returncode != 0:
            self.show_connection_error(
                result.stderr.strip()
                or result.stdout.strip()
                or "Connection failed."
            )

            return False

        self.refresh()

        return False

    def show_connection_error(
        self,
        message,
    ):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Unable to connect",
        )

        dialog.format_secondary_text(
            message
        )

        dialog.run()
        dialog.destroy()

    def toggle_changed(
        self,
        switch,
        _param,
    ):
        if self._ignore_toggle:
            return

        enabled = switch.get_active()

        switch.set_sensitive(False)

        run_async(
            lambda: network.set_wifi_enabled(
                enabled
            ),
            self.toggle_finished,
        )

    def toggle_finished(
        self,
        _result,
    ):
        self.toggle.set_sensitive(
            True
        )

        self.refresh()

        return False

    def clear_networks(self):
        for box in (
            self.saved_box,
            self.other_box,
        ):
            for child in box.get_children():
                box.remove(child)

    @staticmethod
    def signal_icon(
        signal,
    ):
        if signal >= 75:
            return "󰤨"

        if signal >= 50:
            return "󰤥"

        if signal >= 25:
            return "󰤢"

        return "󰤟"

    def show_network_menu(
        self,
        button,
        item,
    ):
        menu = Gtk.Menu()

        if item["connected"]:
            disconnect_item = Gtk.MenuItem(
                label="Disconnect"
            )

            disconnect_item.connect(
                "activate",
                lambda _item: self.disconnect_network(),
            )

            menu.append(
                disconnect_item
            )

        if item["saved"]:
            forget_item = Gtk.MenuItem(
                label="Forget Network"
            )

            forget_item.connect(
                "activate",
                lambda _item: self.confirm_forget(
                    item
                ),
            )

            menu.append(
                forget_item
            )

        menu.show_all()

        menu.popup_at_widget(
            button,
            Gdk.Gravity.SOUTH_EAST,
            Gdk.Gravity.NORTH_EAST,
            None,
        )

    def disconnect_network(
        self,
    ):
        self.status_label.set_text(
            "Disconnecting…"
        )

        run_async(
            network.disconnect,
            self.disconnect_finished,
            self.operation_failed,
        )


    def disconnect_finished(
        self,
        result,
    ):
        if (
            result is None
            or result.returncode != 0
        ):
            self.show_connection_error(
                "Unable to disconnect."
            )

            return False

        self.refresh()

        return False

    def confirm_forget(
        self,
        item,
    ):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Forget {item['ssid']}?",
        )

        dialog.format_secondary_text(
            "You will need to enter the password "
            "again the next time you connect."
        )

        dialog.add_button(
            "Cancel",
            Gtk.ResponseType.CANCEL,
        )

        dialog.add_button(
            "Forget",
            Gtk.ResponseType.OK,
        )

        response = dialog.run()

        dialog.destroy()

        if response != Gtk.ResponseType.OK:
            return

        run_async(
            lambda: network.forget(
                item["profile_uuid"]
            ),
            self.forget_finished,
            self.operation_failed,
        )


    def forget_finished(
        self,
        result,
    ):
        if result.returncode != 0:
            self.show_connection_error(
                result.stderr.strip()
                or "Unable to forget network."
            )

            return False

        self.refresh()

        return False

    def operation_failed(
        self,
        error,
    ):
        self.show_connection_error(
            str(error)
        )

        self.refresh()

        return False