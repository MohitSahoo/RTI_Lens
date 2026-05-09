# 🚀 Quick Start Guide - Timeline Visualization

## Prerequisites Check

Before starting, verify you have:
- ✅ Python 3.11+ installed
- ✅ PostgreSQL database with RTI case data
- ✅ All base requirements installed (`pip install -r requirements.txt`)

## 3-Step Quick Start

### Step 1: Install Plotly

```bash
cd IDP
pip install plotly==5.18.0
```

**Verify installation:**
```bash
python -c "import plotly; print(f'✅ Plotly {plotly.__version__} installed')"
```

### Step 2: Start Backend API

**Terminal 1:**
```bash
cd IDP
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

**Verify backend is running:**
```bash
curl http://localhost:8001/health
```

You should see JSON response with system status.

### Step 3: Start Streamlit Frontend

**Terminal 2:**
```bash
cd IDP
streamlit run streamlit_app.py
```

**Or use the quick-start scripts:**

**Linux/Mac:**
```bash
chmod +x start_timeline.sh
./start_timeline.sh
```

**Windows:**
```cmd
start_timeline.bat
```

## Using the Timeline Visualization

### First Time: Try the Demo

1. Open browser to `http://localhost:8501`
2. Click the **"📅 Timeline"** tab (rightmost tab)
3. Select **"Demo: Sample Timeline"** from dropdown
4. Click **"Load Sample Data"** (if button appears)
5. Explore the interactive orbital timeline!

### With Real Data: Case Timeline

1. In the Timeline tab, select **"Case Timeline"**
2. Set filters:
   - Number of cases: 100
   - Filter by outcome: All
   - Ministry filter: (leave blank for all)
3. Click **"Load Case Timeline"**
4. Explore:
   - Hover over points for details
   - Scroll to zoom
   - View monthly distribution chart

### Workflow Monitoring

1. Select **"Workflow Progression"**
2. Click **"Load Workflow Data"**
3. View stage progression timeline
4. Check stage duration metrics

### Section Trends

1. Select **"Section Citation Timeline"**
2. Click **"Load Section Timeline"**
3. View top 10 most cited sections
4. Analyze trends over time

## Troubleshooting

### Issue: "Module not found: plotly"
```bash
pip install plotly==5.18.0
```

### Issue: "Module not found: components"
Make sure you're in the IDP directory:
```bash
cd IDP
python -c "from components.timeline_visualizer import TimelineVisualizer; print('✅ Component found')"
```

### Issue: "No cases found"
Check your database has cases:
```bash
psql -d rtilens -c "SELECT COUNT(*) FROM cases WHERE order_date IS NOT NULL;"
```

If count is 0, you need to run data ingestion:
```bash
python scripts/ingest.py
```

### Issue: Backend not responding
Verify backend is running:
```bash
curl http://localhost:8001/health
```

If not running, start it:
```bash
uvicorn backend.main:app --port 8001
```

### Issue: Port already in use
**Backend (8001):**
```bash
# Find process
lsof -i :8001  # Mac/Linux
netstat -ano | findstr :8001  # Windows

# Kill process and restart
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

**Frontend (8501):**
```bash
# Streamlit will auto-select next available port
# Or specify custom port:
streamlit run streamlit_app.py --server.port 8502
```

## Feature Overview

### 📊 Case Timeline
- **What**: Scatter plot of cases over time
- **Filters**: Outcome, ministry, date range
- **Insights**: Monthly trends, outcome distribution
- **Best for**: Historical analysis, pattern detection

### 🔄 Workflow Progression
- **What**: Stage-by-stage workflow tracking
- **Metrics**: Duration per stage, bottlenecks
- **Insights**: Performance optimization
- **Best for**: System monitoring, debugging

### 🌐 Orbital Timeline
- **What**: Circular visualization with relationships
- **Visual**: Node size = importance, color = status
- **Insights**: Connected events, progression flow
- **Best for**: Case journey visualization

### 📜 Section Citation Timeline
- **What**: Trend analysis of RTI sections
- **Charts**: Line charts, statistics table
- **Insights**: Popular sections, usage patterns
- **Best for**: Legal analysis, compliance tracking

## Performance Tips

### For Large Datasets (500+ cases)

1. **Use filters aggressively:**
   ```python
   # In Streamlit UI
   - Limit to 100-200 cases
   - Filter by specific ministry
   - Use date range filters
   ```

2. **Add database indexes:**
   ```sql
   CREATE INDEX idx_cases_order_date ON cases(order_date);
   CREATE INDEX idx_cases_ministry_id ON cases(ministry_id);
   ```

3. **Enable caching:**
   ```python
   # Already implemented in component
   # Data is cached for 5 minutes
   ```

## Next Steps

### Explore Features
- [ ] Try all 5 visualization modes
- [ ] Apply different filters
- [ ] Export data (hover → download icon)
- [ ] Compare different time periods

### Customize
- [ ] Edit colors in `components/timeline_visualizer.py`
- [ ] Adjust chart heights and layouts
- [ ] Add custom filters in `streamlit_app.py`
- [ ] Create custom timeline views

### Integrate
- [ ] Add timeline to dashboard
- [ ] Create scheduled reports
- [ ] Export timeline images
- [ ] Share with stakeholders

## Support

**Documentation:**
- Full guide: `TIMELINE_INTEGRATION.md`
- Implementation summary: `TIMELINE_IMPLEMENTATION_SUMMARY.md`
- System status: `SYSTEM_STATUS.md`

**Test Component:**
```bash
python test_timeline_component.py
```

**Check Logs:**
```bash
# Backend logs
tail -f backend.log

# Streamlit logs (in terminal where it's running)
```

## Success Checklist

- [ ] Plotly installed (`pip list | grep plotly`)
- [ ] Backend running (http://localhost:8001/health)
- [ ] Frontend running (http://localhost:8501)
- [ ] Timeline tab visible in UI
- [ ] Demo mode works
- [ ] Real data loads successfully

---

**🎉 You're all set!** Start exploring your RTI case timelines.

**Quick Command Reference:**
```bash
# Install
pip install plotly==5.18.0

# Start backend
uvicorn backend.main:app --port 8001

# Start frontend
streamlit run streamlit_app.py

# Test component
python test_timeline_component.py
```

**Need help?** Check `TIMELINE_INTEGRATION.md` for detailed documentation.
