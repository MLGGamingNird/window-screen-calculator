# Window Screen Calculator — Complete Documentation

> A step-by-step guide to understanding, running, and modifying this app.
> Written so that anyone — even someone who has never looked at code before —
> can understand exactly what every piece does and why.

---

## Table of Contents

1. [What This App Does](#what-this-app-does)
2. [How the App Is Structured](#how-the-app-is-structured)
3. [How to Run It](#how-to-run-it)
4. [The File Tour](#the-file-tour)
5. [How the App Flows — Step by Step](#how-the-app-flows-step-by-step)
6. [The Calculations Explained](#the-calculations-explained)
7. [The Visual Layout Tabs](#the-visual-layout-tabs)
8. [Settings and Config](#settings-and-config)
9. [Deploying Online](#deploying-online)
10. [Glossary](#glossary)

---

## What This App Does

This is a **material calculator for building window screens**. You enter:

- Your window measurements (width and height of each window type)
- How many screens you need
- The length of your aluminum frame sticks
- The dimensions of your mesh roll
- The length of your spline roll
- Your spline groove inset measurements

And the app tells you:

- **Frame:** How many frame pieces to cut, which cuts go on which stick, how much you waste
- **Mesh:** How to cut your mesh roll with overage for trimming, optimized to minimize waste
- **Spline:** How much spline you need per window, and how many rolls to buy

Everything is shown visually with color-coded bars and a top-down cut guide.

---

## How the App Is Structured

This is a **web app** with two parts:

```
BACKEND  (Python — app.py)
  Runs as a local server on your computer
  Does all the calculations
  Reads/writes settings to config.json
  Talks to the browser over HTTP

         ▲ ▼  HTTP requests and JSON responses

FRONTEND  (HTML + CSS + JavaScript — templates/index.html)
  What you see in your browser
  The sidebar with all the input fields
  The four result tabs
  The visual bar charts and cut guide
  Sends your inputs to app.py, receives results back
```

**Why split it this way?**
Calculations live in Python because Python is great at math.
Visuals live in HTML/JavaScript because browsers are great at drawing.
They communicate over HTTP — the same protocol your browser uses for websites.

---

## How to Run It

**1. Open PowerShell and navigate to the app folder:**
```powershell
cd "path\to\window-screen-app"
```

**2. Start the server:**
```powershell
& "path\to\.venv\Scripts\python.exe" app.py
```

**3. Open your browser at:**
```
http://localhost:5000
```

**4. To access from your phone** (same WiFi required):
- Change the last line of app.py: `app.run(host='0.0.0.0', debug=True)`
- Run `ipconfig` to find your computer's IP address
- On your phone: `http://YOUR_IP_ADDRESS:5000`

**5. To stop:** Press `Ctrl+C` in PowerShell

---

## The File Tour

```
window-screen-app/
├── app.py                  ← THE BRAIN — Python server + all math
├── templates/
│   └── index.html          ← THE FACE — Everything you see in the browser
├── config.json             ← YOUR SETTINGS — Auto-created when you save
├── requirements.txt        ← Python packages needed (flask, gunicorn)
├── Procfile                ← Deployment instructions for Render/Railway
└── README.md               ← This file
```

### app.py — Five Sections

| Section | What It Does |
|---------|-------------|
| Imports | Loads Python libraries |
| Unit Conversion | Converts between cm, mm, in, ft |
| Default Config | Blank-slate starting values (all zeros, all inches) |
| Calculations | All the material math |
| Web Routes | URL endpoints the browser calls |

### templates/index.html — Three Sections

| Part | What It Does |
|------|-------------|
| `<style>` | All visual styling — colors, layout, fonts, dark/light mode |
| `<body>` HTML | The visible structure — topbar, sidebar, tabs, detail drawer |
| `<script>` JavaScript | All behavior — fetching data, drawing canvases, handling clicks |

### config.json — Your Saved Settings

Created automatically when you save. Example:
```json
{
  "stick_length": 96.0,
  "stick_unit": "in",
  "mesh_roll_width": 48.0,
  "mesh_roll_width_unit": "in",
  "windows": {
    "Kitchen Left": {
      "width": 36.0, "width_unit": "in",
      "height": 24.0, "height_unit": "in",
      "needed": 1, "full": 1
    }
  }
}
```
**To start fresh:** Delete config.json and restart the server.

---

## How the App Flows — Step by Step

### 1. You open the browser at localhost:5000
Your browser asks app.py for the page.
app.py sends index.html back.
Your browser renders it — you see the empty interface.

### 2. The page loads your saved settings
JavaScript sends a request to `/api/config`.
app.py reads config.json (or returns defaults if it doesn't exist yet).
Settings come back as JSON and populate the sidebar input fields.

### 3. You enter your measurements
You type values into the sidebar fields.
Unit dropdowns let you pick cm, mm, in, or ft per field.
Changing a unit auto-converts the displayed number — no manual math needed.

### 4. You click "Calculate"
JavaScript reads all sidebar fields and packages them into JSON.
It sends this to `/api/calculate` on app.py.

### 5. app.py runs all the math
```
Frame:  build_cut_list()  → all frame piece lengths, sorted
        pack_sticks()     → cuts packed onto physical sticks

Mesh:   calc_mesh()           → cut sizes with overage, areas, roll usage
        pack_mesh_rows()      → simple height-grouped layout (reference)
        pack_mesh_rows_opt()  → FFD optimized layout (shown by default)

Spline: calc_spline()     → perimeters with groove inset, roll count
```
All results are bundled into one JSON response and sent back.

### 6. JavaScript renders the results
```
renderResults()       → stat cards and tables on the Results tab
renderFrameLayout()   → stick bars on the Frame Layout tab
renderMeshLayout()    → roll bars + cut guide on the Mesh Layout tab
renderSplineLayout()  → roll bars on the Spline Layout tab
```

### 7. You interact
- **Hover** over any bar segment → tooltip with details
- **Click** any segment → detail drawer slides in from the right
- **Drag the sidebar edge** → resize the sidebar
- **Click a section header** → collapse/expand that section
- **Sun/moon button** → toggle dark/light theme

---

## The Calculations Explained

### Frame

Every rectangular screen frame has **4 pieces**: 2 widths + 2 heights.

All pieces from all windows are collected, sorted longest-first, then packed
onto sticks using **First Fit Decreasing (FFD)**:

```
For each cut (longest first):
  → Try to fit it on an existing stick
  → If it fits, add it there
  → If not, start a new stick
```

**Waste** = (sticks needed × stick length) − (total cut length)
**Corner keys** = total screens × 4

---

### Mesh

**Cut size with overage:**
```
Frame size:    40.50 × 29.25 in
Overage:        1.00 in per side
Cut size:      42.50 × 31.25 in
                └─ adds 1 in each side = +2 in total per dimension
```

**Roll usage per piece:**
Each piece consumes `height_cut` inches along the roll length.
(You unroll, cut across at the height mark, then cut the width from the strip.)

**Optimized layout (shown by default):**
1. Sort all cut pieces tallest-first
2. Place each piece in the first existing row it fits width-wise
3. Row height = the tallest piece in that row
4. If no row fits, start a new row

This mixes different window sizes in the same row, using the roll width more
efficiently than grouping same-height pieces together.

**Cut guide:**
Shows a top-down view of the roll. Each horizontal stripe = one row of cuts.
The dashed line = where you cut straight across. Numbers show the cm/inch
position along the roll so you can mark it with tape and a pen.

---

### Spline

Spline runs along all 4 sides — the full perimeter. But it sits in a groove
slightly INSET from the frame edge, so the effective length per screen is
a little shorter than the outer perimeter.

```
Frame width:        40.50 in
Inset each end:      0.4375 in  (midpoint of your 0.375–0.500 range)
Effective width:    40.50 − (2 × 0.4375) = 39.625 in

Effective perimeter = 2 × (39.625 + 28.375) = 136.0 in per screen
```

Three estimates are shown:
- **Midpoint** — used for roll count (buy this many)
- **Min inset estimate** — most spline (buy at least this)
- **Max inset estimate** — least spline

---

## The Visual Layout Tabs

### Frame Layout

**Stick bars:** One bar per physical stick. Colored segments = cuts placed on it.
Dark segment = wasted end material. Hover to inspect; click for the detail drawer.

**Cut list:** Every cut shown proportionally against one full stick length.

### Mesh Layout

**Roll bar:** Full bar = one roll. Colored segments = cut pieces. Dark green = leftover.

**Cut guide:** Bird's-eye view of the roll laid flat. Each stripe = one row of cuts placed
side by side across the roll width. Dashed line = where you cut across. Dark green
on the right = unused width. The summary below shows exact cut positions in your units.

### Spline Layout

Same roll bar format. Each segment = one screen's worth of spline.
Summary shows per-window-type breakdown and the min/mid/max range.

---

## Settings and Config

**Needed vs Full toggle:** Switch between "screens for this job" and "all screens total."
Useful for planning both immediate and future material needs from the same window list.

**Mesh overage:** Extra material on all four sides of each cut. 1 inch is a good default.
You trim flush after the spline is pressed in.

**Spline groove inset:** Measure from the outside edge of your frame to the center of the
spline groove. Measure several frames since it can vary. Enter smallest and largest values.

**Unit conversion:** Every field has its own unit dropdown. Changing the unit auto-converts
the displayed number — the underlying measurement stays the same.

**Saving settings:** Click "Save settings" to write to config.json. Settings persist between
sessions. Click "Reset" to wipe everything back to zeros.

---

## Deploying Online

To access from anywhere (not just your home WiFi):

### Render (recommended, free tier)

1. Push `window-screen-app` folder to a GitHub repository
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn app:app`
6. Click Deploy — you get a shareable URL like `your-app.onrender.com`

### Railway (alternative)

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Railway auto-detects Flask from the Procfile
4. Grab the URL from the dashboard

> **Note:** On free hosting tiers, config.json resets when the server restarts.
> For permanent storage, a database would be needed. Fine for personal use.

---

## Glossary

| Term | Plain English Explanation |
|------|--------------------------|
| **Backend** | The Python server (app.py) that runs the math |
| **Frontend** | The HTML/CSS/JS that runs in your browser and shows the interface |
| **HTTP** | The language browsers and servers use to communicate |
| **JSON** | A text format for data that both Python and JavaScript understand |
| **Route** | A URL the server responds to (like `/api/calculate`) |
| **FFD** | First Fit Decreasing — packs pieces efficiently by trying largest items first |
| **Overage** | Extra mesh on all sides so you have material to grip and trim after assembly |
| **Spline** | The rubber bead pressed into the frame groove to hold the mesh in place |
| **Inset** | Distance from the frame edge to the spline groove center |
| **Perimeter** | Total distance around all four sides: 2 × (width + height) |
| **Stick** | A raw aluminum extrusion that gets cut into frame pieces |
| **Corner key** | Plastic connector joining two frame pieces at a corner |
| **Roll** | Coiled mesh or spline sold at a fixed width and length |
| **Row** | In the cut guide, one horizontal band of the roll with side-by-side pieces |
| **Cut line** | A straight cut across the full roll width between rows |
| **DPR** | Device Pixel Ratio — on high-resolution screens (like Retina), 1 CSS pixel = 2 physical pixels. We multiply canvas dimensions by DPR to get crisp, sharp drawings instead of blurry ones |
| **Virtual environment** | An isolated Python installation for this project |
| **Gunicorn** | A production-grade Python web server used when deploying online |
| **Debug mode** | A Flask setting that auto-restarts the server when you save — only for local development |
