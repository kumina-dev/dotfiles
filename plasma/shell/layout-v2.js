// KumiOS Plasma layout. Reconcile in place; never delete panels or dock pins.
// Run through plasma/setup.py --apply-layout after approving a live layout change.
(function () {
    const required = [
        "org.kumios.systemmenu", "org.kde.plasma.kickerdash",
        "org.kumios.activeapp", "org.kde.plasma.appmenu",
        "org.kde.plasma.panelspacer", "org.kumios.controlcenter",
        "org.kde.plasma.digitalclock", "org.kde.plasma.notifications",
        "org.kde.plasma.icontasks"
    ];
    for (const type of required) {
        if (knownWidgetTypes.indexOf(type) < 0) {
            throw new Error("Required widget unavailable: " + type);
        }
    }
    const existing = panels();
    function candidates(location, type) {
        return existing.filter(p => p.location === location &&
            p.widgets().some(w => w.type === type));
    }
    const tops = candidates("top", "org.kumios.systemmenu");
    const docks = candidates("bottom", "org.kde.plasma.icontasks");
    // Resolve both before any mutation. Never guess in a multi-panel setup.
    if (tops.length > 1 || docks.length > 1) {
        throw new Error("Multiple matching bars/docks; select the intended panel before applying.");
    }
    // Validate duplicates on both existing target panels before touching either.
    for (const panel of tops.concat(docks)) {
        for (const type of required) {
            if (panel.widgets().filter(w => w.type === type).length > 1) {
                throw new Error("Duplicate widget requires manual review: " + type);
            }
        }
    }
    function ensure(panel, type) {
        const found = panel.widgets().filter(w => w.type === type);
        const widget = found[0] || panel.addWidget(type);
        if (!widget || widget.type !== type) {
            throw new Error("Could not create widget: " + type);
        }
        return widget;
    }
    const top = tops[0] || new Panel();
    top.location = "top";
    top.height = 32;
    top.lengthMode = "fill";
    top.alignment = "center";
    top.hiding = "none";
    const widgets = required.slice(0, -1).map(type => ensure(top, type));
    const launcher = widgets[1];
    launcher.currentConfigGroup = ["General"];
    launcher.writeConfig("icon", "view-app-grid");
    // Retire only the incompatible launcher, after its replacement exists.
    for (const widget of top.widgets()) {
        if (widget.type === "dev.xarbit.appgrid" || widget.type === "dev.xarbit.appgrid.panel") {
            widget.globalShortcut = "";
            widget.remove();
        }
    }
    launcher.globalShortcut = "Meta+Space";
    widgets.forEach((widget, index) => { widget.index = index; });
    const clock = widgets[6];
    clock.currentConfigGroup = ["Appearance"];
    clock.writeConfig("showDate", false);
    clock.writeConfig("showSeconds", false);
    const dock = docks[0] || new Panel();
    dock.location = "bottom";
    dock.height = 56;
    dock.lengthMode = "fit";
    dock.alignment = "center";
    dock.offset = 0;
    dock.hiding = "dodgewindows";
    ensure(dock, "org.kde.plasma.icontasks");
    print("KumiOS layout reconciled; existing panels, dock pins and desktop retained.");
})();
