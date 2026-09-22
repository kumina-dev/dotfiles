// KumiOS Plasma Shell
// Layout v1

const currentPanels = panels();

// Remove the stock Plasma panels.
// Desktop containment and widgets are left untouched.
for (const panel of currentPanels) {
    panel.remove();
}


// ---------------------------------------------------------
// Top system panel
// ---------------------------------------------------------

const topPanel = new Panel();

topPanel.location = "top";
topPanel.height = 34;

// Application launcher
const launcher = topPanel.addWidget("org.kde.plasma.kickoff");

// Flexible space between launcher and system controls
topPanel.addWidget("org.kde.plasma.panelspacer");

// System tray
topPanel.addWidget("org.kde.plasma.systemtray");

// Clock
const clock = topPanel.addWidget("org.kde.plasma.digitalclock");

clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", false);


// ---------------------------------------------------------
// Bottom application dock
// ---------------------------------------------------------

const dock = new Panel();

dock.location = "bottom";
dock.height = 52;

// Keep the first iteration intentionally boring.
// This will later become the proper KumiOS dock.
dock.addWidget("org.kde.plasma.icontasks");
