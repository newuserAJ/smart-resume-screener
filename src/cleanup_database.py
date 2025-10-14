# src/cleanup_database.py
import sqlite3
import os

DB_PATH = 'database/resume_screener.db'

def cleanup_database():
    """Clean up old test data and reset the database"""
    
    if not os.path.exists(DB_PATH):
        print("Database doesn't exist yet. Nothing to clean.")
        return
    
    print("⚠️  WARNING: This will delete ALL data from the database!")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm != 'YES':
        print("Cleanup cancelled.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Count existing data
        cursor.execute('SELECT COUNT(*) FROM resumes')
        resume_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM job_descriptions')
        job_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM match_results')
        match_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        print(f"\nCurrent database contents:")
        print(f"- Users: {user_count}")
        print(f"- Resumes: {resume_count}")
        print(f"- Jobs: {job_count}")
        print(f"- Matches: {match_count}")
        
        # Ask what to delete
        print("\nWhat would you like to delete?")
        print("1. Everything (including users)")
        print("2. Only resumes, jobs, and matches (keep users)")
        print("3. Cancel")
        
        choice = input("Enter choice (1-3): ")
        
        if choice == '1':
            # Delete everything
            cursor.execute('DELETE FROM match_results')
            cursor.execute('DELETE FROM resumes')
            cursor.execute('DELETE FROM job_descriptions')
            cursor.execute('DELETE FROM users')
            print("✓ Deleted all data including users")
            
        elif choice == '2':
            # Keep users, delete everything else
            cursor.execute('DELETE FROM match_results')
            cursor.execute('DELETE FROM resumes')
            cursor.execute('DELETE FROM job_descriptions')
            print("✓ Deleted resumes, jobs, and matches. Users kept.")
            
        else:
            print("Cleanup cancelled.")
            return
        
        conn.commit()
        
        # Show new counts
        cursor.execute('SELECT COUNT(*) FROM resumes')
        resume_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM job_descriptions')
        job_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM match_results')
        match_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        print(f"\nNew database contents:")
        print(f"- Users: {user_count}")
        print(f"- Resumes: {resume_count}")
        print(f"- Jobs: {job_count}")
        print(f"- Matches: {match_count}")
        
        print("\n✅ Database cleaned successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    cleanup_database()