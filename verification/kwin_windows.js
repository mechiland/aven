// Temporary KWin script. request and receiver are prepended by window_tool.py.
// Uses public Workspace/Window API only. No shortcuts, rules, or config writes.
(function () {
    function rect(r) {
        return {x: r.x, y: r.y, width: r.width, height: r.height};
    }
    function describe(w) {
        return {
            id: String(w.internalId), caption: String(w.caption),
            app: String(w.desktopFileName), resource_class: String(w.resourceClass),
            resource_name: String(w.resourceName), pid: w.pid,
            active: w.active, minimized: w.minimized, full_screen: w.fullScreen,
            hidden: w.hidden, skip_taskbar: w.skipTaskbar, skip_switcher: w.skipSwitcher,
            normal_window: w.normalWindow, dialog: w.dialog, special: w.specialWindow,
            frame: rect(w.frameGeometry), client: rect(w.clientGeometry),
            output: w.output ? String(w.output.name) : null,
            movable: w.moveable, resizable: w.resizeable,
            minimum_client_size: {width: w.minSize.width, height: w.minSize.height}
        };
    }
    function matches(w) {
        if (request.id && String(w.internalId) !== request.id) return false;
        if (request.app && [String(w.desktopFileName), String(w.resourceClass), String(w.resourceName)].indexOf(request.app) < 0) return false;
        if (request.caption && String(w.caption).indexOf(request.caption) < 0) return false;
        return true;
    }
    function inventory() {
        var windows = [], screens = [], stack = workspace.stackingOrder;
        for (var i = 0; i < stack.length; i++) {
            var w = stack[i];
            if (w.deleted || (!request.include_special && w.specialWindow)) continue;
            if (matches(w)) windows.push(describe(w));
        }
        var outputs = workspace.screens;
        for (var j = 0; j < outputs.length; j++) {
            screens.push({name: String(outputs[j].name), scale: outputs[j].devicePixelRatio, geometry: rect(outputs[j].geometry)});
        }
        return {windows: windows, screens: screens, active_window: workspace.activeWindow ? String(workspace.activeWindow.internalId) : null};
    }
    var result;
    try {
        if (request.command === "inventory") {
            result = inventory();
        } else {
            var candidates = [], stack = workspace.stackingOrder;
            for (var i = 0; i < stack.length; i++) {
                var w = stack[i];
                if (!w.deleted && !w.specialWindow && (w.normalWindow || w.dialog) && matches(w)) candidates.push(w);
            }
            if (candidates.length !== 1) throw new Error("Expected exactly one ordinary application window; matched " + candidates.length + ". Narrow --app/--caption or use --id.");
            var target = candidates[0];
            var before = describe(target);
            var requested = request.geometry;
            if (request.maximize && !target.maximizable) throw new Error("Selected window cannot be maximized.");
            if (requested) {
                if (!target.moveable || !target.resizeable) throw new Error("Selected window cannot be moved/resized.");
                var area = workspace.clientArea(KWin.WorkArea, target);
                if (requested.x < area.x || requested.y < area.y || requested.x + requested.width > area.x + area.width || requested.y + requested.height > area.y + area.height) throw new Error("Requested frame exceeds the output work area; use logical coordinates at the current scale.");
                var frameExtraWidth = target.frameGeometry.width - target.clientGeometry.width;
                var frameExtraHeight = target.frameGeometry.height - target.clientGeometry.height;
                if (requested.width < target.minSize.width + frameExtraWidth || requested.height < target.minSize.height + frameExtraHeight) throw new Error("Requested frame is smaller than the application's minimum size.");
            }
            if (request.geometry || request.maximize || request.activate) target.minimized = false;
            if (request.geometry || request.maximize) target.fullScreen = false;
            if (request.geometry) {
                target.setMaximize(false, false);
                target.frameGeometry = requested;
            }
            if (request.maximize) target.setMaximize(true, true);
            if (request.activate) workspace.activeWindow = target;
            result = {before: before, requested_geometry: requested, requested_maximize: request.maximize, requested_activate: request.activate};
        }
        result.ok = true;
    } catch (error) {
        result = {ok: false, error: String(error)};
    }
    callDBus(receiver, "/org/aven/Verification", "org.aven.Verification", "Report", JSON.stringify(result));
})();
