"""
Test script for Backboard integration

Tests:
1. BackboardClient initialization
2. SessionManager session creation
3. Database persistence
"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal
from backend.utils.session_manager import SessionManager
from backend.utils.backboard_client import backboard_client


async def test_backboard_integration():
    """Test Backboard integration end-to-end"""
    print("=" * 60)
    print("Testing Backboard Integration")
    print("=" * 60)

    # Test 1: Check Backboard client
    print("\n1. Backboard Client Status:")
    print(f"   Enabled: {backboard_client.enabled}")
    print(f"   Client: {backboard_client.client}")

    # Test 2: Create workflow session
    print("\n2. Creating workflow session...")
    db = SessionLocal()
    try:
        session = await SessionManager.create_session(
            db=db,
            workflow_type="rti_qa",
            user_id="test_user",
            user_ip="127.0.0.1",
            metadata={"test": "integration_test"}
        )
        print(f"   ✓ Session created: {session.session_id}")
        print(f"   ✓ Thread ID: {session.thread_id}")
        print(f"   ✓ Workflow type: {session.workflow_type}")
        print(f"   ✓ Stage: {session.workflow_stage}")

        # Test 3: Update stage
        print("\n3. Updating workflow stage...")
        await SessionManager.update_stage(
            db=db,
            session_id=session.session_id,
            new_stage="retrieval",
            context={"method": "hybrid"}
        )
        print(f"   ✓ Stage updated to: retrieval")

        # Test 4: Log retrieval
        print("\n4. Logging retrieval operation...")
        await SessionManager.log_retrieval(
            db=db,
            session_id=session.session_id,
            query="test query",
            retrieval_method="hybrid_bm25_vector",
            num_results=5,
            top_sources=["order1", "order2", "order3"]
        )
        print(f"   ✓ Retrieval logged")

        # Test 5: Log generation
        print("\n5. Logging generation operation...")
        await SessionManager.log_generation(
            db=db,
            session_id=session.session_id,
            prompt_type="qa_response",
            response_summary="Test response summary",
            model="groq"
        )
        print(f"   ✓ Generation logged")

        # Test 6: Complete session
        print("\n6. Completing session...")
        SessionManager.complete_session(db, session.session_id)
        print(f"   ✓ Session completed")

        # Test 7: Retrieve session
        print("\n7. Retrieving session from database...")
        retrieved = SessionManager.get_session(db, session.session_id)
        print(f"   ✓ Session retrieved: {retrieved.session_id}")
        print(f"   ✓ Is active: {retrieved.is_active}")
        print(f"   ✓ Retrieval history entries: {len(retrieved.retrieval_history or [])}")
        print(f"   ✓ Generation history entries: {len(retrieved.generation_history or [])}")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_backboard_integration())
