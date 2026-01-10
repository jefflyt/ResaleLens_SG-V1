"""
Environment validation script.

Checks .env.local for placeholder values and guides user to fix them.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")


def check_env_var(name: str, placeholder_values: list[str]) -> tuple[bool, str]:
    """
    Check if environment variable is set and not a placeholder.

    Args:
        name: Environment variable name
        placeholder_values: List of placeholder values to check against

    Returns:
        Tuple of (is_valid, current_value_or_message)
    """
    value = os.getenv(name)

    if not value:
        return False, "❌ NOT SET"

    if value in placeholder_values:
        return False, f"⚠️  PLACEHOLDER: {value}"

    # Hide sensitive values
    if any(x in name.lower() for x in ["password", "key", "secret"]):
        return True, f"✅ SET (***)"
    else:
        return True, f"✅ SET: {value}"


def main() -> None:
    """Validate environment configuration."""
    print("\n🔍 Environment Configuration Validation\n")
    print("=" * 70)

    # Check if .env.local exists
    env_local = Path(".env.local")
    if not env_local.exists():
        print("❌ ERROR: .env.local not found!")
        print("\n📝 To fix:")
        print("   cp .env.example .env.local")
        print("   # Then edit .env.local with your actual values")
        return

    print("✅ .env.local found\n")

    # Define checks
    checks = {
        "Database": {
            "DATABASE_URL": [
                "postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
            ],
        },
        "Data.gov.sg": {
            "DATA_GOV_SG_RESOURCE_ID": ["YOUR_RESOURCE_ID_HERE", "your-resource-id-here"],
        },
        "OneMap API": {
            "ONEMAP_EMAIL": ["your-onemap-email-here", "your@email.com"],
            "ONEMAP_PASSWORD": ["your-onemap-password-here", "your-password"],
        },
        "Optional - AI Features": {
            "GEMINI_API_KEY": ["your-gemini-api-key-here"],
        },
    }

    all_valid = True
    needs_fixing = []

    for section, vars_dict in checks.items():
        print(f"📋 {section}")
        print("-" * 70)

        for var_name, placeholders in vars_dict.items():
            is_valid, message = check_env_var(var_name, placeholders)

            if not is_valid:
                all_valid = False
                needs_fixing.append(var_name)

            print(f"   {var_name}: {message}")

        print()

    if all_valid:
        print("=" * 70)
        print("🎉 All required variables are set!\n")
        print("Next step: Run connection tests")
        print("   uv run python scripts/test_connections.py")
    else:
        print("=" * 70)
        print("⚠️  Configuration Issues Found\n")
        print("Variables that need fixing:")
        for var in needs_fixing:
            print(f"   - {var}")

        print("\n📝 How to fix:")
        print("   1. Open .env.local in your editor")
        print("   2. Replace placeholder values with actual credentials:")
        print()

        if "DATA_GOV_SG_RESOURCE_ID" in needs_fixing:
            print("   ✅ DATA_GOV_SG_RESOURCE_ID is already correct:")
            print("      d_8b84c4ee58e3cfc0ece0d773c8ca6abc")
            print()

        if "ONEMAP_EMAIL" in needs_fixing or "ONEMAP_PASSWORD" in needs_fixing:
            print("   🔑 OneMap credentials:")
            print("      • Register at: https://www.onemap.gov.sg/apidocs/")
            print("      • Use the email/password from your OneMap account")
            print()

        if "DATABASE_URL" in needs_fixing:
            print("   💾 Database:")
            print("      • For local dev: Leave commented (uses SQLite)")
            print("      • For Supabase: Get URL from Supabase dashboard")
            print()


if __name__ == "__main__":
    main()
