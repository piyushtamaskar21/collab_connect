import json
import sys
import os
import getpass
from dotenv import load_dotenv
from generator import generate_synthetic_data

load_dotenv()
from engine import CollabEngine
from models import Employee, Profile

def print_json(data):
    print(json.dumps(data, indent=2, default=str))

def main():
    print("Welcome to CollabConnect (AI Powered)!")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API Key not found in environment variables.")
        api_key = getpass.getpass("Please enter your OpenAI API Key: ").strip()
        if not api_key:
            print("API Key is required for AI features. Exiting.")
            return

    engine = CollabEngine(api_key=api_key)
    employees = []

    while True:
        print("\nAvailable commands:")
        print("1. Generate synthetic data")
        print("2. Find similar profiles")
        print("3. Exit")
        
        choice = input("Enter command (1-3): ").strip()

        if choice == "1":
            count = input("Enter number of profiles to generate (default 30): ").strip()
            count = int(count) if count.isdigit() else 30
            employees = generate_synthetic_data(count)
            engine.load_employees(employees)
            print(f"Generated and loaded {len(employees)} profiles.")
            
            # Save to file for inspection
            with open("synthetic_employees.json", "w") as f:
                json.dump([e.to_dict() for e in employees], f, indent=2)
            print("Saved to synthetic_employees.json")

        elif choice == "2":
            if not employees:
                print("No data loaded. Please generate data first.")
                continue
            
            print("\nSelect a target employee by ID or Name (partial match):")
            # List first 5 for convenience
            for i, emp in enumerate(employees[:5]):
                print(f"{i+1}. {emp.name} ({emp.profile.role}) - ID: {emp.id}")
            
            query = input("Enter Name or ID: ").strip()
            
            target_emp = None
            for emp in employees:
                if emp.id == query or query.lower() in emp.name.lower():
                    target_emp = emp
                    break
            
            if target_emp:
                print(f"\nFinding matches for: {target_emp.name} ({target_emp.profile.role})")
                recommendations = engine.find_similar_employees(target_emp.id)
                
                # Structured JSON Output
                output = {
                    "target_employee": target_emp.to_dict(),
                    "recommendations": [
                        {
                            "employee": rec["employee"].to_dict(),
                            "score": rec["score"],
                            "reason": rec["reason"],
                            "common_skills": rec["common_skills"],
                            "common_projects": rec["common_projects"]
                        }
                        for rec in recommendations
                    ]
                }
                print("\n--- JSON Output ---")
                print_json(output)
                
                # Narrative Output
                print("\n--- Narrative Summary ---")
                summary = engine.generate_collaboration_summary(target_emp, recommendations)
                print(summary)
            else:
                print("Employee not found.")

        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
