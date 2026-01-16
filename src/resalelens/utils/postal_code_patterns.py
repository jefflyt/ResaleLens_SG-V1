"""
Singapore Postal Code Pattern-Based Generator.

Based on Singapore postal code structure:
- First 2 digits: Postal sector (corresponds to town/district)
- Last 4 digits: For HDB, incorporates block number

This allows us to construct postal codes without API calls!
"""

# Postal sector mapping by town (first 2 digits)
# Source: https://en.wikipedia.org/wiki/Postal_codes_in_Singapore
# and https://www.99.co/singapore/insider/singapore-postal-codes/

TOWN_TO_POSTAL_SECTOR = {
    # Central Area
    "MARINA SOUTH": ["01", "02", "03", "04", "05", "06"],
    "RAFFLES PLACE": ["01", "02", "03", "04", "05", "06"],
    "CECIL": ["01", "02", "03", "04", "05", "06"],
    "MARINA CENTRE": ["03", "04", "05", "06"],
    "ANSON": ["07", "08"],
    "TANJONG PAGAR": ["07", "08"],
    "CHINATOWN": ["05", "06"],
    "HARBOURFRONT": ["09", "10"],
    "TELOK BLANGAH": ["09", "10"],
    "BUKIT MERAH": ["10", "15", "16"],
    "ALEXANDRA": ["15", "16"],
    "QUEENSTOWN": ["11", "12", "13"],
    "TIONG BAHRU": ["16"],
    "REDHILL": ["15"],
    "BUKIT TIMAH": ["11", "21"],
    "TANGLIN": ["09", "10"],
    "HOLLAND": ["27"],
    "RIVER VALLEY": ["23"], 
    "ORCHARD": ["22", "23"],
    "CAIRNHILL": ["22", "23"],
    
    # North
    "SEMBAWANG": ["75", "76"],
    "YISHUN": ["76"],
    "WOODLANDS": ["73"],
    "ADMIRALTY": ["75"],
    
    # North-East
    "SENGKANG": ["54", "82"],
    "PUNGGOL": ["82"],
    "HOUGANG": ["53"],
    "SERANGOON": ["55"],
    "ANG MO KIO": ["56", "57"],
    
    # East
    "BEDOK": ["46", "47"],
    "SIMEI": ["52"],
    "TAMPINES": ["52"],
    "PASIR RIS": ["51"],
    "LOYANG": ["50"],
    
    # West
    "JURONG WEST": ["64", "65"],
    "JURONG EAST": ["60", "61"],
    "BOON LAY": ["64"],
    "BUKIT BATOK": ["65", "66"],
    "CHOA CHU KANG": ["68", "69"],
    "CLEMENTI": ["12", "13"],
    "BUKIT PANJANG": ["67", "68", "69", "79"],
    
    # Central
    "TOA PAYOH": ["31", "32"],
    "NOVENA": ["30"],
    "THOMSON": ["29", "30"],
    "BISHAN": ["56", "57"],
    "BRADDELL": ["57"],
    
    # Central-East
    "MARINE PARADE": ["44", "45"],
    "KATONG": ["42", "43"],
    "BEDOK": ["46", "47", "48"],
    "SIGLAP": ["45"],
    "EUNOS": ["40", "41"],
    "GEYLANG": ["38", "39", "40", "41"],
    "MACPHERSON": ["36", "37"],
    "PAYA LEBAR": ["53"],
    "KALLANG": ["33", "34", "39"],
    "KALLANG/WHAMPOA": ["32", "33", "34"],
    
    # Others
    "CENTRAL AREA": ["01", "02", "03", "04", "05", "06"],
}


def generate_hdb_postal_code(block: str, town: str) -> list[str]:
    """
    Generate possible postal codes for an HDB block using pattern matching.
    
    For HDB blocks, Singapore postal codes follow the pattern:
    - Sector (2 digits) + Letter Code (1 digit) + Block (3 digits padded)
    
    For blocks WITH alphabetical suffixes:
    - The third digit encodes the letter: A=1, B=2, C=3, D=4, etc.
    - Example: Block 310A in Punggol (sector 82): 821310
    - Example: Block 310B in Punggol (sector 82): 822310
    
    For blocks WITHOUT alphabetical suffixes:
    - The third digit is typically 0
    - Example: Block 123 in Bedok (sector 46): 460123
    
    Args:
        block: Block number (e.g., "123", "5", "128B", "310A")
        town: Town name (e.g., "BEDOK", "YISHUN", "PUNGGOL")
    
    Returns:
        List of possible postal codes (may have multiple for ambiguous sectors)
    """
    import re
    
    # Extract numeric part and letter suffix
    match = re.match(r'^(\d+)([A-Za-z]?)$', block.strip())
    if not match:
        return []
    
    block_numeric = match.group(1)
    letter_suffix = match.group(2).upper()
    
    # Get postal sectors for this town
    sectors = TOWN_TO_POSTAL_SECTOR.get(town.upper(), [])
    if not sectors:
        return []
    
    # Pad block to 3 digits
    try:
        block_num = int(block_numeric)
        block_padded = f"{block_num:03d}"
    except ValueError:
        return []
    
    # Encode letter suffix as third digit
    # A=1, B=2, C=3, D=4, etc.
    if letter_suffix:
        letter_code = str(ord(letter_suffix) - ord('A') + 1)
    else:
        letter_code = "0"
    
    # Generate postal codes: Sector (2) + Letter Code (1) + Block (3)
    postal_codes = []
    for sector in sectors:
        postal_code = f"{sector}{letter_code}{block_padded}"
        postal_codes.append(postal_code)
    
    return postal_codes


# Test the function
if __name__ == "__main__":
    test_cases = [
        ("310A", "PUNGGOL"),  # Should be 821310
        ("310B", "PUNGGOL"),  # Should be 822310
        ("123", "BEDOK"),     # Should be 460123, 470123, 480123
        ("128B", "BEDOK"),    # Should be 462128, 472128, 482128
        ("471C", "SENGKANG"), # Should be 543471, 823471
        ("5", "YISHUN"),      # Should be 760005
    ]
    
    print("=" * 80)
    print("🧪 Testing Postal Code Pattern Generation (with letter suffix support)")
    print("=" * 80)
    
    for block, town in test_cases:
        postal_codes = generate_hdb_postal_code(block, town)
        print(f"\nBlock {block:6s} in {town:15s} →", "  ".join(postal_codes))
