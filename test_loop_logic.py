"""
Test the while loop logic to verify it doesn't infinite loop
This simulates different scenarios without running the full system
"""

def test_loop_logic():
    print("=" * 60)
    print("TESTING MAIN.PY LOOP LOGIC")
    print("=" * 60)
    
    # Test Scenario 1: Agent3 returns programs
    print("\n1. Testing: Agent3 returns 1 program")
    state = {"ranked_programs": [{"name": "Test Program"}], "_agent3_displayed": False}
    
    # Simulate the checks
    if state.get("reports_generated"):
        print("   → Would break at CHECK 1 (reports_generated)")
    elif state.get("ranked_programs") and not state.get("_agent3_displayed"):
        print("   ✅ Would enter CHECK 2 (display programs)")
        print("   ✅ Would break after running Agents 4-6")
    elif "ranked_programs" in state and not state.get("ranked_programs"):
        print("   → Would break at SAFETY CHECK (empty programs)")
    else:
        print("   ❌ INFINITE LOOP - no break condition matched!")
    
    # Test Scenario 2: Agent3 returns empty list
    print("\n2. Testing: Agent3 returns empty list []")
    state = {"ranked_programs": [], "_agent3_displayed": False}
    
    if state.get("reports_generated"):
        print("   → Would break at CHECK 1 (reports_generated)")
    elif state.get("ranked_programs") and not state.get("_agent3_displayed"):
        print("   → Would enter CHECK 2 (display programs)")
    elif "ranked_programs" in state and not state.get("ranked_programs"):
        print("   ✅ Would break at SAFETY CHECK (empty programs)")
    else:
        print("   ❌ INFINITE LOOP - no break condition matched!")
    
    # Test Scenario 3: After displaying programs
    print("\n3. Testing: After displaying (_agent3_displayed=True)")
    state = {"ranked_programs": [{"name": "Test"}], "_agent3_displayed": True}
    
    if state.get("reports_generated"):
        print("   → Would break at CHECK 1 (reports_generated)")
    elif state.get("ranked_programs") and not state.get("_agent3_displayed"):
        print("   → Would enter CHECK 2 (display programs)")
    elif "ranked_programs" in state:
        if not state.get("ranked_programs"):
            print("   → Would break at SAFETY CHECK (empty)")
        elif state.get("_agent3_displayed"):
            print("   ✅ Would break at SAFETY CHECK (_agent3_displayed)")
    else:
        print("   ❌ INFINITE LOOP - no break condition matched!")
    
    # Test Scenario 4: Agent6 completed
    print("\n4. Testing: Agent6 completed (reports_generated=True)")
    state = {"ranked_programs": [{"name": "Test"}], "reports_generated": True}
    
    if state.get("reports_generated"):
        print("   ✅ Would break at CHECK 1 (reports_generated)")
    elif state.get("ranked_programs") and not state.get("_agent3_displayed"):
        print("   → Would enter CHECK 2 (display programs)")
    else:
        print("   ❌ INFINITE LOOP - no break condition matched!")
    
    # Test Scenario 5: Initial state (before Agent3 runs)
    print("\n5. Testing: Initial state (no ranked_programs yet)")
    state = {"user_intent": "test"}
    
    if state.get("reports_generated"):
        print("   → Would break at CHECK 1")
    elif state.get("ranked_programs") and not state.get("_agent3_displayed"):
        print("   → Would enter CHECK 2")
    elif "ranked_programs" in state:
        print("   → Would enter SAFETY CHECK")
    else:
        print("   ✅ Would continue to next loop iteration (expected - Agent3 hasn't run yet)")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("All scenarios should either break or continue (only for initial state)")
    print("If any scenario shows '❌ INFINITE LOOP', the logic is broken")

if __name__ == "__main__":
    test_loop_logic()
