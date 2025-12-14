"""Script to verify Supabase credentials"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def verify_supabase_credentials():
    """Verify if Supabase URL and Key are correct"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    print("=" * 60)
    print("Supabase Credentials Verification")
    print("=" * 60)
    
    # Check if variables exist
    if not url:
        print("[ERROR] SUPABASE_URL is not set in .env file")
        return False
    
    if not key:
        print("[ERROR] SUPABASE_KEY is not set in .env file")
        return False
    
    # Display credentials (partially masked for security)
    print(f"\nSUPABASE_URL: {url}")
    print(f"SUPABASE_KEY: {key[:20]}...{key[-10:] if len(key) > 30 else '***'}")
    
    # Validate URL format
    print("\nValidating URL format...")
    if not url.startswith('https://'):
        print("[WARNING] URL should start with 'https://'")
    if '.supabase.co' not in url:
        print("[WARNING] URL should contain '.supabase.co'")
    else:
        print("[OK] URL format looks correct")
    
    # Validate key format
    print("\nValidating key format...")
    if key.startswith('sb_publishable_'):
        print("[OK] Key format: Publishable key (new format)")
        print("[WARNING] The Supabase Python client (v2.3.0) may not support this format yet!")
        print("         It expects JWT-format keys (starting with 'eyJ').")
        print("         You may need to:")
        print("         1. Use the legacy 'anon' key from your Supabase dashboard")
        print("         2. Update to a newer version of supabase-py if available")
        print("         3. Check Supabase dashboard: Settings > API > anon/public key")
    elif key.startswith('sb_secret_'):
        print("[OK] Key format: Secret key (new format)")
        print("[WARNING] Secret keys should only be used server-side!")
        print("[WARNING] The Supabase Python client (v2.3.0) may not support this format yet!")
    elif key.startswith('eyJ'):
        print("[OK] Key format: Legacy JWT key (anon or service_role)")
        print("[OK] This format is compatible with the current Supabase Python client")
    else:
        print("[WARNING] Key format doesn't match expected patterns")
    
    # Try to create client and test connection
    print("\nTesting connection to Supabase...")
    try:
        client = create_client(url, key)
        print("[OK] Supabase client created successfully")
        
        # Try a simple query to verify the connection works
        print("\nTesting database connection...")
        try:
            # Try to query a table (this will fail if RLS is blocking, but will succeed if connection is valid)
            # We'll catch the error to see if it's a connection issue or RLS issue
            result = client.table('users').select('id').limit(1).execute()
            print("[OK] Database connection successful!")
            print("[OK] Credentials are CORRECT and working!")
            return True
        except Exception as db_error:
            error_msg = str(db_error)
            # Check if it's an RLS error (which means connection works but RLS is blocking)
            if 'permission denied' in error_msg.lower() or 'row-level security' in error_msg.lower():
                print("[OK] Database connection successful!")
                print("[NOTE] Query blocked by Row Level Security (RLS) - this is normal")
                print("       Your credentials are correct, but RLS policies are restricting access.")
                print("       This is expected behavior for publishable keys.")
                return True
            elif 'relation' in error_msg.lower() and 'does not exist' in error_msg.lower():
                print("[OK] Database connection successful!")
                print("[NOTE] Table doesn't exist yet - you may need to run the SQL setup from README.md")
                return True
            else:
                print(f"[ERROR] Database query failed: {error_msg}")
                print("        This might indicate incorrect credentials or connection issues.")
                return False
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Failed to create Supabase client: {error_msg}")
        
        # Provide helpful error messages
        if 'Invalid URL' in error_msg:
            print("        -> Check that your SUPABASE_URL is correct")
        elif 'Invalid API key' in error_msg:
            print("        -> Check that your SUPABASE_KEY is correct")
        elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            print("        -> Check your internet connection")
        else:
            print("        -> Verify your credentials in the Supabase dashboard")
        
        return False

if __name__ == "__main__":
    success = verify_supabase_credentials()
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] VERIFICATION COMPLETE: Your Supabase credentials are correct!")
    else:
        print("[FAILED] VERIFICATION FAILED: Please check your credentials")
    print("=" * 60)
    exit(0 if success else 1)
