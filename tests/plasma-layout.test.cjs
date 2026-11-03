// Exercise the reconciliation against a stateful Plasma API double.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../plasma/shell/layout-v2.js'), 'utf8');
const types = ['org.kumios.systemmenu', 'org.kde.plasma.kickerdash', 'org.kumios.activeapp',
    'org.kde.plasma.appmenu', 'org.kde.plasma.panelspacer', 'org.kumios.controlcenter',
    'org.kde.plasma.digitalclock', 'org.kde.plasma.notifications', 'org.kde.plasma.icontasks'];
function environment() {
    let next = 0;
    const panels = [];
    function Panel() {
        this.id = ++next;
        this.items = [];
        this.widgets = () => this.items.slice();
        this.addWidget = type => {
            const w = {id: ++next, type, config: {}, globalShortcut: '',
                writeConfig(key, value) { this.config[key] = value; },
                remove: () => { this.items.splice(this.items.indexOf(w), 1); }};
            this.items.push(w);
            return w;
        };
        panels.push(this);
    }
    const context = {panels: () => panels, Panel, knownWidgetTypes: types.slice(), print: () => {}};
    return {panels, Panel, context, run: () => vm.runInNewContext(script, context)};
}
test('fresh layout has one launcher, notifications, menu and centered dock', () => {
    const e = environment(); e.run();
    assert.equal(e.panels.length, 2);
    assert.deepEqual(e.panels[0].items.map(w => w.type), types.slice(0, -1));
    assert.equal(e.panels[0].items[1].globalShortcut, 'Meta+Space');
    assert.equal(e.panels[1].alignment, 'center');
    assert.equal(e.panels[1].hiding, 'dodgewindows');
});
test('repeated apply preserves identities, dock pins, and unrelated panels/widgets', () => {
    const e = environment();
    const top = new e.Panel(); top.location = 'top'; top.addWidget(types[0]);
    const old = top.addWidget('dev.xarbit.appgrid'); old.globalShortcut = 'Meta+Space';
    const extra = top.addWidget('personal-widget');
    const dock = new e.Panel(); dock.location = 'bottom';
    const tasks = dock.addWidget(types.at(-1)); tasks.config.launchers = ['personal.desktop'];
    const side = new e.Panel(); side.location = 'left';
    e.run(); const ids = top.items.map(w => w.id); e.run();
    assert.equal(e.panels.length, 3);
    assert.equal(e.panels[0], top); assert.equal(e.panels[1], dock);
    assert.equal(e.panels[2], side);
    assert.equal(dock.items[0], tasks);
    assert.deepEqual(tasks.config.launchers, ['personal.desktop']);
    assert.deepEqual(top.items.map(w => w.id), ids);
    assert.ok(top.items.includes(extra)); assert.ok(!top.items.includes(old));
});
test('missing dependencies fail before mutation', () => {
    const e = environment(); e.context.knownWidgetTypes.pop();
    assert.throws(e.run, /Required widget unavailable/); assert.equal(e.panels.length, 0);
});
test('ambiguous docks and duplicate widgets fail before mutation', () => {
    const e = environment();
    for (let i = 0; i < 2; i++) {
        const p = new e.Panel(); p.location = 'bottom'; p.addWidget(types.at(-1));
    }
    assert.throws(e.run, /Multiple matching/); assert.equal(e.panels.length, 2);
    e.panels.pop(); e.panels[0].addWidget(types.at(-1));
    assert.throws(e.run, /Duplicate widget/); assert.equal(e.panels.length, 1);
});
test('failed native launcher creation retains old launcher', () => {
    const e = environment(); const top = new e.Panel(); top.location = 'top';
    top.addWidget(types[0]); const old = top.addWidget('dev.xarbit.appgrid');
    const add = top.addWidget;
    top.addWidget = type => type === types[1] ? null : add(type);
    assert.throws(e.run, /Could not create widget/);
    assert.ok(top.items.includes(old));
});
