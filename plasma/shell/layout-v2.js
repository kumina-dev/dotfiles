// KumiOS Plasma Shell
// Layout v2
//
// Goals:
// - compact top system bar
// - centered, content-sized bottom dock
// - keep desktop containment untouched
// - stay entirely within supported Plasma 6 scripting APIs

// ---------------------------------------------------------
// Remove existing panels
// ---------------------------------------------------------

for (const panel of panels()) {
    panel.remove();
}


// ---------------------------------------------------------
// Top system bar
// ---------------------------------------------------------

const topPanel = new Panel();

topPanel.location = "top";
topPanel.height = 32;
topPanel.lengthMode = "fill";
topPanel.alignment = "center";
topPanel.hiding = "none";


// Launcher
const launcher = topPanel.addWidget("org.kumios.systemmenu");

launcher.currentConfigGroup = ["General"];

// We'll replace this with a KumiOS launcher later.
launcher.writeConfig("icon", "start-here-kde");

const activeApp = topPanel.addWidget("org.kumios.activeapp");

// Left-side spacing
topPanel.addWidget("org.kde.plasma.panelspacer");

const controlCenter =
    topPanel.addWidget("org.kumios.controlcenter");

// Clock
const clock =
    topPanel.addWidget("org.kde.plasma.digitalclock");

clock.currentConfigGroup = ["Appearance"];

clock.writeConfig("showDate", false);
clock.writeConfig("showSeconds", false);


// ---------------------------------------------------------
// Bottom application dock
// ---------------------------------------------------------

const dock = new Panel();

dock.location = "bottom";
dock.height = 56;
dock.lengthMode = "fit";
dock.alignment = "center";
dock.offset = 0;
dock.hiding = "dodgewindows";

dock.addWidget("org.kde.plasma.icontasks");
