# 🎨 RTI-Lens Frontend - Visual Guide

## 🌐 Access the Frontend

**URL:** http://localhost:8501

---

## 📱 Interface Overview

### Main Navigation Tabs (Top of Page)

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 RTI-Lens API Test Interface                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [💬 Q&A] [✨ RTI Query Assistant] [🎯 Predict Outcome]         │
│  [📊 Analytics] [🕸️ Knowledge Graph] [📅 Timeline] ← NEW!      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Sidebar (Left Side)

```
┌──────────────────────┐
│  System Status       │
│  ─────────────────   │
│  [Check Health]      │
│                      │
│  ─────────────────   │
│  Session History     │
│  [Refresh Sessions]  │
│                      │
│  Recent 5 sessions:  │
│  • qa - 10:30:15     │
│  • draft - 10:25:03  │
│  • ...               │
└──────────────────────┘
```

---

## 📅 Timeline Tab - What You'll See

### Step 1: Select Visualization Mode

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 Interactive Timeline Visualization                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  💡 Visualize RTI cases, workflows, and trends over time        │
│                                                                   │
│  Select Timeline View:                                           │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Demo: Sample Timeline                      ▼     │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                   │
│  Options:                                                        │
│  • Case Timeline                                                 │
│  • Workflow Progression                                          │
│  • Orbital Timeline                                              │
│  • Section Citation Timeline                                     │
│  • Demo: Sample Timeline  ← Start here!                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Step 2: Demo Mode View

When you select "Demo: Sample Timeline", you'll see:

```
┌─────────────────────────────────────────────────────────────────┐
│  🎨 Demo: Sample Timeline                                       │
│  Interactive demonstration with sample data                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ✅ Loaded 5 sample timeline items                              │
│                                                                   │
│  🌐 Orbital Timeline Visualization                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │                    ●  Planning                              │ │
│  │                   ╱                                         │ │
│  │                  ╱                                          │ │
│  │      Release  ●─────────⊙─────────●  Design               │ │
│  │                  ╲       │       ╱                          │ │
│  │                   ╲      │      ╱                           │ │
│  │                    ●─────┴─────●                            │ │
│  │                  Testing    Development                     │ │
│  │                                                             │ │
│  │  Legend:                                                    │ │
│  │  ⊙ = Center Hub                                            │ │
│  │  ● Green = Completed                                       │ │
│  │  ● Blue = In Progress                                      │ │
│  │  ● Gray = Pending                                          │ │
│  │                                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  💡 Hover over nodes for details • Click to expand              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Expanded Node Details

When you click a node:

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Timeline Details                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ✅ Planning                                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Date: Jan 2024                                            │ │
│  │  Status: Completed                                         │ │
│  │  Content: Project planning and requirements gathering      │ │
│  │                                                             │ │
│  │  Energy: [████████████████████] 100%                       │ │
│  │                                                             │ │
│  │  🔗 Connected to: 1 items                                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  🔄 Design                                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Date: Feb 2024                                            │ │
│  │  Status: Completed                                         │ │
│  │  Content: UI/UX design and system architecture            │ │
│  │                                                             │ │
│  │  Energy: [██████████████████  ] 90%                        │ │
│  │                                                             │ │
│  │  🔗 Connected to: 2 items                                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  🔄 Development                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Date: Mar 2024                                            │ │
│  │  Status: In Progress                                       │ │
│  │  Content: Core features implementation and testing         │ │
│  │                                                             │ │
│  │  Energy: [████████████        ] 60%                        │ │
│  │                                                             │ │
│  │  🔗 Connected to: 2 items                                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Case Timeline View

When you select "Case Timeline":

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Case Timeline Analysis                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Filters:                                                        │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────┐      │
│  │ Cases:   │  │ Outcome:     │  │ Ministry:           │      │
│  │ 100   ▼  │  │ All       ▼  │  │ (optional)          │      │
│  └──────────┘  └──────────────┘  └─────────────────────┘      │
│                                                                   │
│  [Load Case Timeline]                                            │
│                                                                   │
│  ✅ Loaded 100 cases                                            │
│                                                                   │
│  📅 Case Timeline                                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Metrics:                                                   │ │
│  │  Total Cases: 100  |  Allowed: 45  |  Denied: 55          │ │
│  │  Date Range: 365 days                                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Cases Over Time by Ministry                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Ministry of Finance    ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●   │ │
│  │  Ministry of Home       ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●   │ │
│  │  Ministry of Health     ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●   │ │
│  │                                                             │ │
│  │  ● Green = Allowed  ● Red = Denied  ● Amber = Partial     │ │
│  │                                                             │ │
│  │  ├────────┼────────┼────────┼────────┼────────┤           │ │
│  │  Jan     Feb     Mar     Apr     May     Jun               │ │
│  │                                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  📊 Monthly Case Distribution                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Cases per Month                                            │ │
│  │                                                             │ │
│  │  20 ┤                                                       │ │
│  │  15 ┤     ██                                                │ │
│  │  10 ┤  ██ ██ ██                                            │ │
│  │   5 ┤  ██ ██ ██ ██ ██                                      │ │
│  │   0 ┼──┴──┴──┴──┴──┴──                                     │ │
│  │     Jan Feb Mar Apr May Jun                                │ │
│  │                                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Progression View

```
┌─────────────────────────────────────────────────────────────────┐
│  🔄 Workflow Timeline                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [Load Workflow Data]                                            │
│                                                                   │
│  ✅ Loaded 100 workflow actions                                 │
│                                                                   │
│  Workflow Stage Progression                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Completed   ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●   │ │
│  │  Generation  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━●               │ │
│  │  Retrieval   ●━━━━━━━━━━━━━━━━━●                           │ │
│  │  Initiated   ●━━━━━●                                        │ │
│  │                                                             │ │
│  │              ├────┼────┼────┼────┼────┤                    │ │
│  │              0s   5s   10s  15s  20s  25s                  │ │
│  │                                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ⏱️ Stage Durations                                             │
│  ┌──────────┬──────────┬──────────┬──────────┐                │
│  │ Initiated│ Retrieval│Generation│ Completed│                │
│  │   5.0s   │   10.0s  │   15.0s  │   20.0s  │                │
│  └──────────┴──────────┴──────────┴──────────┘                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Interactive Features

### Hover Tooltips
```
When you hover over any data point:
┌─────────────────────────┐
│ Order: CIC/MOFIN/...   │
│ Date: 2024-03-15       │
│ Ministry: Finance      │
│ Section: 8(1)(a)       │
│ Outcome: Allowed       │
└─────────────────────────┘
```

### Zoom & Pan
- **Scroll**: Zoom in/out
- **Click & Drag**: Pan around
- **Double Click**: Reset view

### Export Options
- **Camera Icon**: Download as PNG
- **Download Icon**: Export data as CSV

---

## 💡 Tips for Using the Frontend

1. **Start with Demo Mode**
   - No database required
   - See all features in action
   - Learn the interface

2. **Use Filters**
   - Narrow down results
   - Faster loading
   - More focused analysis

3. **Explore Interactively**
   - Hover for details
   - Click to expand
   - Zoom to focus

4. **Check Sidebar**
   - System health status
   - Recent session history
   - Backboard integration status

5. **Try All Tabs**
   - Q&A: Ask questions about RTI rulings
   - Query Assistant: Optimize RTI queries
   - Predict: Forecast appeal outcomes
   - Analytics: Statistical insights
   - Knowledge Graph: Relationship visualization
   - Timeline: Temporal analysis (NEW!)

---

## 🚀 Quick Actions

### To Access Timeline:
1. Open: http://localhost:8501
2. Click: "📅 Timeline" tab
3. Select: "Demo: Sample Timeline"
4. Explore!

### To Load Real Data:
1. Select: "Case Timeline"
2. Set filters (optional)
3. Click: "Load Case Timeline"
4. Analyze results

### To Monitor Workflows:
1. Select: "Workflow Progression"
2. Click: "Load Workflow Data"
3. View stage progression
4. Check duration metrics

---

## 📱 Mobile/Responsive View

The interface adapts to smaller screens:
- Tabs become scrollable
- Charts resize automatically
- Sidebar collapses
- Touch-friendly controls

---

## 🎨 Color Scheme

- **Green** (#10b981): Completed, Allowed
- **Blue** (#3b82f6): In Progress
- **Gray** (#6b7280): Pending
- **Red** (#ef4444): Denied
- **Amber** (#f59e0b): Partially Allowed
- **Purple** (#8b5cf6): Center/Hub nodes

---

**Your frontend is now running at: http://localhost:8501**

Open it in your browser to see the full interactive experience!
