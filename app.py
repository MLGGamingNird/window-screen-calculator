# =============================================================================
# app.py  —  Window Screen Calculator  —  Backend Server
# =============================================================================
#
# WHAT THIS FILE IS:
#   This is the "brain" of the app. It runs on your computer as a small web
#   server. When you open the calculator in your browser, your browser talks
#   to this file to get information, run calculations, and save your settings.
#
# HOW IT FITS INTO THE APP:
#
#   YOUR BROWSER  (shows the pretty interface)
#   File: templates/index.html
#
#   When you press "Calculate", the browser sends your measurements here,
#   this file does all the math, then sends results back.
#
#   YOUR SETTINGS FILE  (remembers your preferences)
#   File: config.json  —  created automatically when you save settings
#
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS  —  Loading tools we need from Python's toolbox
# -----------------------------------------------------------------------------

import math
# "math" gives us access to extra math functions Python doesn't have built in.
# We specifically use math.ceil() — "round UP to the nearest whole number".
# Example: math.ceil(2.1) = 3, math.ceil(2.9) = 3, math.ceil(3.0) = 3
# We use this when counting rolls/sticks — you can't buy 2.3 rolls, so we
# always round UP to make sure you have enough material.

import json
# "json" lets us read and write JSON files.
# JSON (JavaScript Object Notation) is a text format for storing data that
# both Python and JavaScript can understand. It looks like:
#   {"name": "Alice", "age": 30}
# We use it to save your settings to config.json between sessions.

import os
# "os" lets us interact with your operating system — things like checking
# whether a file exists before trying to open it.
# We use os.path.exists() to check if config.json has been created yet.

from flask import Flask, request, jsonify, render_template
# "flask" is a Python web framework — it turns this script into a web server
# that your browser can talk to.
#
#   Flask           = the main web server class
#   request         = lets us read data sent FROM the browser TO this server
#   jsonify         = converts Python dictionaries into JSON to send back
#   render_template = loads and sends the HTML file (index.html) to the browser


# -----------------------------------------------------------------------------
# APP SETUP
# -----------------------------------------------------------------------------

app = Flask(__name__)
# Creates our web server.
# Think of this like opening a restaurant — before you can serve customers
# (browsers), you have to unlock the doors first.
# __name__ is a Python special variable that equals the filename ("app").

CONFIG_FILE = "config.json"
# The name of the file where we save all your settings.
# It will be created in the same folder as this script when you first save.
# Storing it as a variable means we only have to change it in one place
# if we ever want to rename it.


# =============================================================================
# SECTION 1: UNIT CONVERSION
# =============================================================================
#
# WHY WE NEED THIS:
#   All measurements in the app can be entered in different units —
#   inches, centimeters, millimeters, or feet. Internally, ALL calculations
#   are done in centimeters. This keeps the math simple and consistent.
#
# ANALOGY:
#   Imagine friends in different countries — one measures in miles, one in
#   kilometers. To compare fairly, you convert everything to km first, do
#   your math, then convert back to each person's preferred unit.

TO_CM = {"cm": 1.0, "mm": 0.1, "in": 2.54, "ft": 30.48}
# A dictionary (lookup table) storing how many centimeters are in each unit.
#   "cm": 1.0    →  1 centimeter = 1.0 cm  (needed for consistency)
#   "mm": 0.1    →  1 millimeter = 0.1 cm  (10mm in 1cm)
#   "in": 2.54   →  1 inch       = 2.54 cm (exact international definition)
#   "ft": 30.48  →  1 foot       = 30.48 cm (12 inches × 2.54)

UNIT_FMT = {"cm": 2, "mm": 1, "in": 3, "ft": 4}
# How many decimal places to show for each unit when displaying results.
#   cm → 2 decimals  (e.g. 40.19 cm)
#   mm → 1 decimal   (e.g. 401.9 mm)
#   in → 3 decimals  (e.g. 15.823 in)  — needs more precision
#   ft → 4 decimals  (e.g. 1.3186 ft)  — needs even more because feet are large


def to_cm(v, u):
    # Converts a measurement FROM any unit TO centimeters.
    # v = the number (e.g. 15.823)
    # u = the unit   (e.g. "in")
    # Example: to_cm(15.823, "in") → 15.823 × 2.54 → 40.19 cm
    return v * TO_CM[u]


def from_cm(v, u):
    # Converts a measurement FROM centimeters BACK TO any unit.
    # v = the number in cm (e.g. 40.19)
    # u = the target unit  (e.g. "in")
    # Example: from_cm(40.19, "in") → 40.19 ÷ 2.54 → 15.823 in
    return v / TO_CM[u]


def fmt(v, u):
    # Rounds a number to the appropriate decimal places for its unit.
    # v = the value (e.g. 15.82677165...)
    # u = the unit  (e.g. "in")
    # Example: fmt(15.82677, "in") → round(15.82677, 3) → 15.827
    return round(v, UNIT_FMT[u])


# =============================================================================
# SECTION 2: DEFAULT CONFIGURATION
# =============================================================================
#
# When someone runs the app for the very first time (no config.json yet),
# we need something to show. This is the blank-slate starting point.
# All values are 0.0 and all units are inches.

DEFAULT_CONFIG = {
    # FRAME ───────────────────────────────────────────────────────────────────
    "stick_length":           0.0,   # Length of one raw aluminum frame stick
    "stick_unit":             "in",  # Unit for stick length

    # MESH ────────────────────────────────────────────────────────────────────
    "mesh_roll_width":        0.0,   # How wide the mesh roll is
    "mesh_roll_width_unit":   "in",

    "mesh_roll_length":       0.0,   # Total length of the mesh roll
    "mesh_roll_length_unit":  "in",

    "mesh_overage":           0.0,   # Extra mesh added on ALL FOUR sides of each cut piece.
                                      # A 40×30 frame with 1 in overage → cut piece is 42×32.
                                      # Gives you material to grab while pressing spline in;
                                      # you trim the excess after the spline is seated.
    "mesh_overage_unit":      "in",

    # SPLINE ──────────────────────────────────────────────────────────────────
    "spline_roll_length":     0.0,   # Total length of the spline roll
    "spline_roll_length_unit":"in",

    "spline_inset_min":       0.0,   # Minimum distance from frame edge to spline groove.
                                      # Measured on your actual frames with a ruler.
    "spline_inset_max":       0.0,   # Maximum distance. We store min+max because the groove
                                      # depth can vary slightly frame to frame.
                                      # The midpoint is used for calculations;
                                      # the full range is shown as a safety reference.
    "spline_inset_unit":      "in",

    # WINDOWS ─────────────────────────────────────────────────────────────────
    "windows": {}
    # Empty — no windows defined yet. Each window gets added as:
    #   "My Window Name": {
    #       "width": 36.0, "width_unit": "in",
    #       "height": 24.0, "height_unit": "in",
    #       "needed": 1,   ← screens for THIS job
    #       "full": 1      ← total screens this window type needs overall
    #   }
}


def load_config():
    # Reads saved settings from config.json if it exists.
    # If the file doesn't exist yet, returns a fresh copy of DEFAULT_CONFIG.
    # Also "patches in" any new settings that didn't exist in older saved files,
    # so updating the app doesn't break your existing config.

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            # json.load() reads the file and converts JSON text to a Python dict.

            # setdefault(key, value) = "add this key only if it's missing"
            # This handles old config files that pre-date newer features.
            data.setdefault("stick_unit",              "cm")
            data.setdefault("mesh_roll_width_unit",    "cm")
            data.setdefault("mesh_roll_length_unit",   "cm")
            data.setdefault("mesh_overage",            DEFAULT_CONFIG["mesh_overage"])
            data.setdefault("mesh_overage_unit",       DEFAULT_CONFIG["mesh_overage_unit"])
            data.setdefault("spline_roll_length",      DEFAULT_CONFIG["spline_roll_length"])
            data.setdefault("spline_roll_length_unit", "cm")
            data.setdefault("spline_inset_min",        DEFAULT_CONFIG["spline_inset_min"])
            data.setdefault("spline_inset_max",        DEFAULT_CONFIG["spline_inset_max"])
            data.setdefault("spline_inset_unit",       DEFAULT_CONFIG["spline_inset_unit"])

            # Patch each saved window too
            for d in data["windows"].values():
                d.setdefault("width_unit",  "cm")
                d.setdefault("height_unit", "cm")

            return data

        except Exception:
            # If the file is corrupted or unreadable, fall through to defaults
            pass

    # config.json doesn't exist or couldn't be read — return fresh defaults.
    # json.loads(json.dumps(...)) creates a deep copy so the caller can't
    # accidentally modify the original DEFAULT_CONFIG dictionary.
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(data):
    # Writes current settings to config.json so they survive closing the app.
    # data = Python dictionary of all current settings
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    # indent=2 makes the file human-readable with 2-space indentation.
    # Without it, everything would be on one ugly line.


# =============================================================================
# SECTION 3: CALCULATIONS
# =============================================================================
#
# All measurements arrive from the browser in the user's chosen unit.
# Every function here converts to cm first, does math, and returns results
# in cm. The browser then converts back to the user's chosen unit for display.


def build_cut_list(config, mode):
    # Builds a flat sorted list of every frame piece length needed.
    #
    # A rectangular frame has 4 pieces: 2 widths + 2 heights.
    # This function creates that list for ALL windows combined.
    #
    # mode = "needed" (screens for this job) or "full" (all screens total)
    #
    # Returns: list of lengths in cm, sorted longest to shortest.
    # Example: [52.25, 52.25, 40.50, 40.50, 40.19, 40.19, 17.00, 17.00, ...]
    #
    # WHY SORT LONGEST FIRST?
    #   The packing algorithm works best with largest pieces first —
    #   this is called "First Fit Decreasing" and minimizes material waste.

    cuts = []

    for d in config["windows"].values():
        w = to_cm(d["width"],  d["width_unit"])   # Frame width in cm
        h = to_cm(d["height"], d["height_unit"])  # Frame height in cm

        for _ in range(d[mode]):
            # Repeat for each screen of this type.
            # _ means "I don't need the loop counter, just repeat N times."
            cuts.extend([w, w, h, h])
            # Each screen = 2 width pieces + 2 height pieces

    return sorted(cuts, reverse=True)  # Longest first


def pack_sticks(cuts, stick_cm):
    # Figures out how to fit all cut pieces onto physical sticks with minimal waste.
    # Uses "First Fit Decreasing" (FFD) — a classic bin-packing algorithm:
    #   → Go through cuts longest to shortest
    #   → For each cut, try existing sticks first
    #   → If it fits, add it there; if not, start a new stick
    #
    # cuts     = sorted list of cut lengths (cm), longest first
    # stick_cm = length of one raw aluminum stick (cm)
    #
    # Returns: list of sticks. Each stick = list of cut lengths placed on it.
    # Example: [[52.25, 40.50, 40.50, 40.19], [40.50, 40.19, 17.00, 17.00], ...]
    #
    # ANALOGY: Packing pieces of wood onto 8-foot boards to minimize how
    # many boards you buy. Always try to fill existing boards before opening new ones.

    sticks = []

    for cut in cuts:
        placed = False

        for stick in sticks:
            if sum(stick) + cut <= stick_cm:
                # This cut fits on this stick — add it
                stick.append(cut)
                placed = True
                break  # Stop searching — found a home for this cut

        if not placed:
            # Doesn't fit anywhere — start a brand new stick
            sticks.append([cut])

    return sticks


def calc_mesh(config, mode):
    # Calculates all mesh (screen material) requirements.
    # For each window type: figures out cut size (with overage), area, and roll usage.
    #
    # KEY CONCEPT — OVERAGE:
    #   Don't cut mesh to exactly the frame size. Add a border so you have
    #   material to grip while pressing the spline in. Trim excess after.
    #   Overage applies to ALL FOUR SIDES.
    #   Example: 40×30 frame + 1 in overage → cut 42×32 (adds 1 in per side)
    #
    # Returns: dict with per-window cuts list + overall totals

    roll_w   = to_cm(config["mesh_roll_width"],  config["mesh_roll_width_unit"])
    roll_len = to_cm(config["mesh_roll_length"], config["mesh_roll_length_unit"])
    overage  = to_cm(config.get("mesh_overage", 1.0), config.get("mesh_overage_unit", "in"))
    # config.get(key, default) safely reads a value, using the default if it's missing

    cuts = []; total_area = 0.0; total_roll = 0.0

    for name, d in config["windows"].items():
        qty = d[mode]
        if not qty: continue  # Skip window types with zero quantity

        w = to_cm(d["width"],  d["width_unit"])
        h = to_cm(d["height"], d["height_unit"])

        w_cut = w + 2 * overage   # Width to cut = frame width + overage on LEFT + RIGHT
        h_cut = h + 2 * overage   # Height to cut = frame height + overage on TOP + BOTTOM
        # Why 2× overage? Because overage adds to BOTH ends of each dimension.

        cuts.append({
            "name":           name,
            "width":          w,          # Frame width (no overage)
            "height":         h,          # Frame height (no overage)
            "width_cut":      w_cut,      # Actual cut width (with overage)
            "height_cut":     h_cut,      # Actual cut height (with overage)
            "overage":        overage,
            "qty":            qty,
            "piece_area":     w_cut * h_cut,         # Area of ONE cut piece
            "total_area":     w_cut * h_cut * qty,   # Area of ALL pieces this type
            "roll_per_piece": h_cut,                  # Roll length used per piece
                                                       # (each piece consumes h_cut of roll)
            "total_roll":     h_cut * qty,            # Total roll length for this type
            "fits":           w_cut <= roll_w         # Does the piece fit the roll width?
                                                       # False = roll too narrow — warning shown
        })

        total_area += w_cut * h_cut * qty
        total_roll += h_cut * qty

    rolls = math.ceil(total_roll / roll_len)
    # Rolls to buy. Always round UP — can't buy a fraction of a roll.

    return {
        "cuts":       cuts,
        "total_area": total_area,
        "total_roll": total_roll,
        "rolls":      rolls,
        "roll_len":   roll_len,
        "roll_w":     roll_w,
        "overage":    overage,
        "leftover":   rolls * roll_len - total_roll
        # Leftover = (rolls you buy × roll length) − (roll length actually used)
    }


def pack_mesh_rows(config, mode):
    # Lays out mesh pieces grouped by HEIGHT — the simple approach.
    # Same-height pieces sit side by side in one row. One straight cut ends the row.
    # Not used in the main display (optimized is shown instead), but still calculated
    # and returned for reference.

    roll_w  = to_cm(config["mesh_roll_width"], config["mesh_roll_width_unit"])
    overage = to_cm(config.get("mesh_overage", 1.0), config.get("mesh_overage_unit", "in"))

    pieces = []
    for i, (name, d) in enumerate(config["windows"].items()):
        w = to_cm(d["width"],  d["width_unit"])  + 2 * overage
        h = to_cm(d["height"], d["height_unit"]) + 2 * overage
        for _ in range(d[mode]):
            pieces.append({"name": name, "width": w, "height": h, "idx": i})

    rows = []; i = 0
    while i < len(pieces):
        row = []; used = 0.0; h = pieces[i]["height"]; j = i

        # Pack same-height pieces side by side until roll width is full
        while j < len(pieces) and pieces[j]["height"] == h and used + pieces[j]["width"] <= roll_w:
            row.append(pieces[j]); used += pieces[j]["width"]; j += 1

        if not row:
            # Single piece too wide — place it alone
            row.append(pieces[i]); used = pieces[i]["width"]; j = i + 1

        rows.append({"pieces": row, "row_height": max(p["height"] for p in row), "used_width": used})
        i = j

    return rows


def pack_mesh_rows_optimized(config, mode):
    # Smarter layout — mixes different window sizes in the same row to minimize waste.
    # This is what the app shows by default in the Mesh Layout tab.
    #
    # ALGORITHM — "First Fit Decreasing":
    #   1. Sort all pieces tallest first (tallest pieces anchor rows)
    #   2. For each piece, try to fit it in an existing row (width must fit)
    #   3. Row height = the tallest piece placed in it
    #   4. If no row fits, start a new one
    #
    # WHY TALLEST FIRST?
    #   Big pieces placed early create rows that shorter pieces can fill.
    #   This typically uses fewer rows and wastes less material than grouping by height.

    roll_w  = to_cm(config["mesh_roll_width"], config["mesh_roll_width_unit"])
    overage = to_cm(config.get("mesh_overage", 1.0), config.get("mesh_overage_unit", "in"))

    pieces = []
    for i, (name, d) in enumerate(config["windows"].items()):
        w = to_cm(d["width"],  d["width_unit"])  + 2 * overage
        h = to_cm(d["height"], d["height_unit"]) + 2 * overage
        for _ in range(d[mode]):
            pieces.append({"name": name, "width": w, "height": h, "idx": i})

    # Sort tallest first
    pieces.sort(key=lambda p: p["height"], reverse=True)
    # lambda p: p["height"] means "use the height field of each piece for sorting"

    rows = []
    for piece in pieces:
        placed = False

        for row in rows:
            if row["used_width"] + piece["width"] <= roll_w:
                row["pieces"].append(piece)
                row["used_width"] += piece["width"]
                row["row_height"] = max(row["row_height"], piece["height"])
                placed = True
                break

        if not placed:
            rows.append({"pieces": [piece], "row_height": piece["height"], "used_width": piece["width"]})

    return rows


def calc_spline(config, mode):
    # Calculates spline requirements for the job.
    #
    # WHAT IS SPLINE?
    #   The rubber bead/rope pressed into the frame groove to hold the mesh.
    #   It runs along all 4 sides of every screen — the full perimeter.
    #
    # GROOVE INSET:
    #   The spline sits inside a groove slightly INSET from the frame edge.
    #   So the effective spline length per side is slightly SHORTER than the frame.
    #   We store a MIN and MAX inset because groove depth varies between frames.
    #   MIDPOINT is used for the main calculation; MIN/MAX show the safety range.
    #
    # SPLINE PER SCREEN:
    #   Outer perimeter    = 2 × (width + height)
    #   Effective perim    = 2 × ((width − 2×inset) + (height − 2×inset))
    #   Why 2×inset per dimension? The groove is inset at BOTH ENDS of each side.

    roll_len = to_cm(config["spline_roll_length"], config["spline_roll_length_unit"])
    imin     = to_cm(config["spline_inset_min"],   config["spline_inset_unit"])
    imax     = to_cm(config["spline_inset_max"],   config["spline_inset_unit"])
    imid     = (imin + imax) / 2   # Average of min and max

    rows = []; total = 0.0; total_min = 0.0; total_max = 0.0

    for name, d in config["windows"].items():
        qty = d[mode]
        if not qty: continue

        w = to_cm(d["width"],  d["width_unit"])
        h = to_cm(d["height"], d["height_unit"])

        outer    = 2 * (w + h)                                # Full outer perimeter
        pmid     = 2 * ((w - 2*imid) + (h - 2*imid))         # Effective at midpoint
        pmin     = 2 * ((w - 2*imin) + (h - 2*imin))         # Effective at min inset
        pmax_val = 2 * ((w - 2*imax) + (h - 2*imax))         # Effective at max inset

        rows.append({
            "name":      name,
            "width":     w,
            "height":    h,
            "qty":       qty,
            "outer":     outer,         # Full perimeter (no inset subtracted)
            "perimeter": pmid,          # Effective perimeter used for main calc
            "perim_min": pmin,          # Effective at minimum inset
            "perim_max": pmax_val,      # Effective at maximum inset
            "total":     pmid     * qty,
            "total_min": pmin     * qty,
            "total_max": pmax_val * qty,
        })
        total     += pmid     * qty
        total_min += pmin     * qty
        total_max += pmax_val * qty

    # Guard against division by zero if roll_len not set yet
    rolls = math.ceil(total / roll_len) if roll_len > 0 else 0

    return {
        "rows":      rows,
        "total":     total,         # Total spline needed at midpoint inset
        "total_min": total_min,     # Conservative estimate (buy at least this)
        "total_max": total_max,     # Optimistic estimate
        "inset_mid": imid,
        "inset_min": imin,
        "inset_max": imax,
        "rolls":     rolls,
        "roll_len":  roll_len,
        "leftover":  rolls * roll_len - total
    }


# =============================================================================
# SECTION 4: WEB ROUTES  —  How the browser talks to this server
# =============================================================================
#
# A "route" is a URL the server responds to. The browser "visits" a URL
# and gets back either a page (HTML) or data (JSON).
#
# Routes in this app:
#   GET  /                  → Sends the HTML interface page
#   GET  /api/config        → Sends your saved settings as JSON
#   POST /api/config        → Receives + saves updated settings
#   POST /api/config/reset  → Resets all settings to defaults
#   POST /api/calculate     → Receives measurements, returns all results


@app.route("/")
def index():
    # Serves the main HTML page when you open the app in a browser.
    # Runs when you visit http://localhost:5000
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    # Returns your saved settings as JSON when the browser asks.
    # Runs when the page loads — browser immediately fetches settings
    # to pre-fill all the input fields.
    return jsonify(load_config())


@app.route("/api/config", methods=["POST"])
def set_config():
    # Receives updated settings from the browser and saves them to config.json.
    # Runs when you click "Save settings".
    data = request.json   # Read the JSON the browser sent
    save_config(data)     # Write it to config.json
    return jsonify({"ok": True})  # Acknowledge success


@app.route("/api/config/reset", methods=["POST"])
def reset_config():
    # Resets all settings to defaults (all zeros, all inches).
    # Runs when you click "Reset" and confirm.
    save_config(json.loads(json.dumps(DEFAULT_CONFIG)))
    return jsonify(DEFAULT_CONFIG)  # Send defaults back so UI updates immediately


@app.route("/api/calculate", methods=["POST"])
def calculate():
    # THE MAIN EVENT. Receives all your measurements, runs every calculation,
    # returns a complete set of results for all four display tabs.
    # Runs when you click "Calculate".

    body   = request.json    # All data the browser sent
    config = body["config"]  # Full settings dictionary
    mode   = body["mode"]    # "needed" or "full"

    # ── FRAME ─────────────────────────────────────────────────────────────────
    stick_cm      = to_cm(config["stick_length"], config["stick_unit"])
    cuts          = build_cut_list(config, mode)       # All frame cut lengths
    sticks        = pack_sticks(cuts, stick_cm)        # Cuts packed onto sticks
    total_screens = sum(d[mode] for d in config["windows"].values())
    total_len     = sum(cuts)                          # Total raw material needed
    frame_waste   = len(sticks) * stick_cm - total_len # Material trimmed and discarded

    # ── MESH ──────────────────────────────────────────────────────────────────
    mesh          = calc_mesh(config, mode)             # Cut sizes + totals
    mesh_rows     = pack_mesh_rows(config, mode)        # Simple row layout (reference)
    mesh_rows_opt = pack_mesh_rows_optimized(config, mode)  # Optimized layout (shown)

    # ── SPLINE ────────────────────────────────────────────────────────────────
    spline        = calc_spline(config, mode)           # Perimeters + roll count

    # ── RESPONSE ──────────────────────────────────────────────────────────────
    return jsonify({
        "stick_cm":      stick_cm,                         # Stick length in cm
        "cuts":          cuts,                             # All cut lengths (cm), sorted
        "sticks":        sticks,                           # Packed stick layout
        "total_screens": total_screens,                    # Total screens
        "total_len":     total_len,                        # Total frame material (cm)
        "sticks_needed": math.ceil(total_len / stick_cm), # Sticks to buy
        "frame_waste":   frame_waste,                      # Wasted material (cm)
        "corner_keys":   total_screens * 4,               # Corner keys needed (4 per screen)
        "mesh":          mesh,
        "mesh_rows":     mesh_rows,
        "mesh_rows_opt": mesh_rows_opt,
        "spline":        spline,
        "mode":          mode,
    })


# =============================================================================
# SECTION 5: ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # This block only runs when you start the file directly: "python app.py"
    # It does NOT run when a production server (gunicorn) imports this file.
    app.run(debug=True)
    # debug=True → auto-restarts when you save this file; shows detailed errors.
    # NEVER use debug=True in production — it exposes too much information.
    # To allow phone/tablet access on the same WiFi, use:
    #   app.run(host='0.0.0.0', debug=True)
