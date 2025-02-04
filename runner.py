import sys
from Agency import create_production_agency

def main():
    agency = create_production_agency()

    # 1) Start a console-based conversation with the Planner by default:
    # or you can do a direct programmatic call:
    print("=== Starting Production Multi-Agent System ===")
    agency.run_demo()

    # Once the user is done in the console, we can tear down agents
    for ag in agency.agents:
        ag.teardown()

    print("=== All Agents Teardown Complete ===")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(1)
