#!/usr/bin/env python3
"""
Timeline Visualization - Complete Integration Verification
Run this script to verify all components are properly installed and configured
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_mark(condition, success_msg, fail_msg):
    """Print check mark or X based on condition"""
    if condition:
        print(f"✅ {success_msg}")
        return True
    else:
        print(f"❌ {fail_msg}")
        return False

def main():
    print_header("RTI-Lens Timeline Visualization - Integration Verification")

    all_checks_passed = True

    # Check 1: Python version
    print("\n📋 Checking Python Environment...")
    python_version = sys.version_info
    all_checks_passed &= check_mark(
        python_version >= (3, 11),
        f"Python {python_version.major}.{python_version.minor}.{python_version.micro} (>= 3.11)",
        f"Python {python_version.major}.{python_version.minor} - Need 3.11+"
    )

    # Check 2: Required packages
    print("\n📦 Checking Required Packages...")

    packages = {
        'streamlit': 'Streamlit',
        'plotly': 'Plotly',
        'pandas': 'Pandas',
        'sqlalchemy': 'SQLAlchemy',
        'fastapi': 'FastAPI'
    }

    for package, name in packages.items():
        try:
            __import__(package)
            version = __import__(package).__version__
            check_mark(True, f"{name} {version} installed", "")
        except ImportError:
            all_checks_passed &= check_mark(False, "", f"{name} not installed")

    # Check 3: File structure
    print("\n📁 Checking File Structure...")

    required_files = {
        'components/timeline_visualizer.py': 'Timeline Visualizer Component',
        'components/__init__.py': 'Components Package Init',
        'streamlit_app.py': 'Streamlit Application',
        'requirements.txt': 'Requirements File',
        'TIMELINE_INTEGRATION.md': 'Integration Documentation',
        'QUICKSTART_TIMELINE.md': 'Quick Start Guide',
        'test_timeline_component.py': 'Test Script'
    }

    for file_path, description in required_files.items():
        exists = Path(file_path).exists()
        all_checks_passed &= check_mark(
            exists,
            f"{description} exists",
            f"{description} missing at {file_path}"
        )

    # Check 4: Component import
    print("\n🔧 Checking Component Import...")
    try:
        sys.path.insert(0, '.')
        from components.timeline_visualizer import TimelineVisualizer, create_sample_timeline_data
        check_mark(True, "TimelineVisualizer can be imported", "")

        # Test instantiation
        visualizer = TimelineVisualizer()
        check_mark(True, "TimelineVisualizer can be instantiated", "")

        # Test sample data
        sample_data = create_sample_timeline_data()
        all_checks_passed &= check_mark(
            len(sample_data) > 0,
            f"Sample data created ({len(sample_data)} items)",
            "Sample data creation failed"
        )

    except Exception as e:
        all_checks_passed &= check_mark(False, "", f"Component import failed: {str(e)}")

    # Check 5: Streamlit app structure
    print("\n📱 Checking Streamlit App Integration...")
    try:
        with open('streamlit_app.py', 'r') as f:
            content = f.read()

        checks = {
            'from components.timeline_visualizer import': 'Timeline import statement',
            'tab6': 'Timeline tab (tab6) defined',
            'with tab6:': 'Timeline tab content block',
            'TimelineVisualizer()': 'TimelineVisualizer instantiation',
            'render_case_timeline': 'Case timeline rendering',
            'render_workflow_timeline': 'Workflow timeline rendering',
            'render_orbital_timeline': 'Orbital timeline rendering'
        }

        for check_str, description in checks.items():
            all_checks_passed &= check_mark(
                check_str in content,
                description,
                f"{description} not found"
            )

    except Exception as e:
        all_checks_passed &= check_mark(False, "", f"Streamlit app check failed: {str(e)}")

    # Check 6: Requirements file
    print("\n📋 Checking Requirements...")
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()

        all_checks_passed &= check_mark(
            'plotly' in requirements,
            "Plotly in requirements.txt",
            "Plotly not in requirements.txt"
        )
    except Exception as e:
        all_checks_passed &= check_mark(False, "", f"Requirements check failed: {str(e)}")

    # Check 7: Database connection (optional)
    print("\n🗄️  Checking Database Connection (Optional)...")
    try:
        from backend.database import SessionLocal
        from backend.models import Case

        db = SessionLocal()
        case_count = db.query(Case).count()
        db.close()

        check_mark(
            case_count > 0,
            f"Database connected ({case_count} cases found)",
            "Database connected but no cases found"
        )
    except Exception as e:
        print(f"⚠️  Database check skipped: {str(e)}")
        print("   (This is optional - timeline will work with demo data)")

    # Final summary
    print_header("Verification Summary")

    if all_checks_passed:
        print("\n🎉 SUCCESS! All checks passed.")
        print("\n✅ Timeline Visualization is ready to use!")
        print("\n📝 Next Steps:")
        print("   1. Install plotly: pip install plotly==5.18.0")
        print("   2. Start backend: uvicorn backend.main:app --port 8001")
        print("   3. Start frontend: streamlit run streamlit_app.py")
        print("   4. Navigate to the '📅 Timeline' tab")
        print("   5. Try 'Demo: Sample Timeline' first")
        print("\n📚 Documentation:")
        print("   - Quick Start: QUICKSTART_TIMELINE.md")
        print("   - Full Guide: TIMELINE_INTEGRATION.md")
        print("   - Summary: TIMELINE_COMPLETE.md")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
        print("\n🔧 Common fixes:")
        print("   - Install missing packages: pip install -r requirements.txt")
        print("   - Ensure you're in the IDP directory")
        print("   - Check file permissions")
        print("\n📚 See QUICKSTART_TIMELINE.md for detailed setup instructions")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Verification failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
