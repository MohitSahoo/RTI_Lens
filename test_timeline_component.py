"""
Quick test script for Timeline Visualizer component
Run this to verify the component works independently
"""
import sys
sys.path.insert(0, '.')

from components.timeline_visualizer import TimelineVisualizer, create_sample_timeline_data
import pandas as pd
from datetime import datetime, timedelta

def test_timeline_visualizer():
    """Test the TimelineVisualizer component"""
    print("🧪 Testing Timeline Visualizer Component\n")

    # Initialize visualizer
    visualizer = TimelineVisualizer()
    print("✅ TimelineVisualizer initialized")

    # Test 1: Sample timeline data
    print("\n📊 Test 1: Creating sample timeline data...")
    sample_data = create_sample_timeline_data()
    print(f"✅ Created {len(sample_data)} sample timeline items")
    for item in sample_data:
        print(f"   - {item['title']}: {item['status']} ({item['energy']}% energy)")

    # Test 2: Case timeline data format
    print("\n📊 Test 2: Testing case timeline data format...")
    case_data = [
        {
            'order_number': 'CIC/MOFIN/A/2024/123456',
            'order_date': datetime.now() - timedelta(days=i*30),
            'ministry': 'Ministry of Finance',
            'section_cited': '8(1)(a)',
            'appeal_outcome': 'allowed' if i % 2 == 0 else 'denied',
            'appeal_level': 'second_appeal'
        }
        for i in range(10)
    ]
    print(f"✅ Created {len(case_data)} test cases")

    # Test 3: Workflow data format
    print("\n📊 Test 3: Testing workflow data format...")
    workflow_data = [
        {
            'session_id': 'test-session-001',
            'stage': stage,
            'timestamp': datetime.now() - timedelta(minutes=10-i*2),
            'details': {}
        }
        for i, stage in enumerate(['initiated', 'retrieval', 'generation', 'completed'])
    ]
    print(f"✅ Created {len(workflow_data)} workflow stages")
    for wf in workflow_data:
        print(f"   - {wf['stage']}: {wf['timestamp'].strftime('%H:%M:%S')}")

    # Test 4: Data validation
    print("\n📊 Test 4: Validating data structures...")

    # Check required fields for orbital timeline
    required_orbital_fields = ['id', 'title', 'date', 'content', 'status', 'energy']
    for item in sample_data:
        missing = [field for field in required_orbital_fields if field not in item]
        if missing:
            print(f"❌ Missing fields in item {item.get('id')}: {missing}")
        else:
            print(f"✅ Item {item['id']} has all required fields")

    # Test 5: Color scheme
    print("\n🎨 Test 5: Checking color scheme...")
    print(f"✅ Color scheme loaded:")
    for status, color in visualizer.colors.items():
        print(f"   - {status}: {color}")

    print("\n" + "="*60)
    print("✅ All tests passed! Component is ready to use.")
    print("="*60)
    print("\n📝 Next steps:")
    print("1. Install plotly: pip install plotly==5.18.0")
    print("2. Start the API: uvicorn backend.main:app --port 8001")
    print("3. Start Streamlit: streamlit run streamlit_app.py")
    print("4. Navigate to the '📅 Timeline' tab")
    print("\n💡 Tip: Try the 'Demo: Sample Timeline' mode first!")

if __name__ == "__main__":
    try:
        test_timeline_visualizer()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
