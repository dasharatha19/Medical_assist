"""
LangGraph Agent Demo
Demonstrates how to use the appointment scheduling agent
"""
from agents import create_scheduling_graph, SchedulerState


def main():
    """
    Run the appointment scheduling workflow
    """
    print("\n" + "=" * 70)
    print("MEDICAL APPOINTMENT SCHEDULING SYSTEM")
    print("LangGraph Agent Layer Demo")
    print("=" * 70 + "\n")
    
    # Create the compiled graph
    print("Initializing scheduling agent...")
    agent = create_scheduling_graph()
    
    # Create initial state
    initial_state = SchedulerState()
    
    # Run the agent
    print("\n" + "-" * 70)
    print("Starting workflow...\n")
    
    try:
        # Invoke the agent with initial state
        final_state = agent.invoke(initial_state)
        
        # Display final results
        print("\n" + "=" * 70)
        print("WORKFLOW SUMMARY")
        print("=" * 70 + "\n")
        
        if final_state.workflow_complete:
            if final_state.booking_success:
                print("✓ Appointment successfully scheduled!")
                print("\nFinal Details:")
                print(final_state.get_summary())
            else:
                if final_state.booking_confirmed:
                    print("⚠ Appointment was confirmed but booking failed.")
                    print(f"Error: {final_state.error_message}")
                else:
                    print("❌ Appointment was not confirmed by patient.")
        else:
            print("⚠ Workflow ended unexpectedly")
            if final_state.error_message:
                print(f"Error: {final_state.error_message}")
        
        print("\n" + "=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n❌ Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during workflow: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
