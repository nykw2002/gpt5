import re
from typing import List, Dict, Any

def find_israel_complaints(file_path: str) -> List[Dict[str, Any]]:
    """
    Find all complaints from Israel in the text file
    Returns list with complaint details and line numbers
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    complaints = []
    
    # Search patterns for Israel
    israel_patterns = [
        r'\bisrael\b',
        r'\bisraeli\b',
        r'\bIsrael\b',
        r'\bIsraeli\b'
    ]
    
    # Compile patterns for efficiency
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in israel_patterns]
    
    print(f"Searching {len(lines)} lines for Israel complaints...")
    print("=" * 80)
    
    for line_num, line in enumerate(lines, 1):
        line_text = line.strip()
        
        # Skip empty lines
        if not line_text:
            continue
        
        # Check if line contains Israel
        israel_found = False
        for pattern in compiled_patterns:
            if pattern.search(line_text):
                israel_found = True
                break
        
        if israel_found:
            # Check if it's likely a complaint (contains common complaint keywords)
            complaint_keywords = [
                'complaint', 'batch', 'material', 'defect', 'issue', 
                'problem', 'error', 'fail', 'not work', 'broken',
                'substance', 'spray', 'come out', 'identifier'
            ]
            
            is_complaint = any(keyword.lower() in line_text.lower() for keyword in complaint_keywords)
            
            if is_complaint or len(line_text) > 50:  # Include longer lines that might be complaints
                complaints.append({
                    'line_number': line_num,
                    'content': line_text,
                    'is_likely_complaint': is_complaint
                })
    
    return complaints

def extract_complaint_details(text: str) -> Dict[str, str]:
    """
    Extract structured information from complaint text
    """
    details = {}
    
    # Common patterns to extract
    patterns = {
        'identifier': r'(?:identifier|id)[:\s]*([0-9]+)',
        'batch': r'(?:batch|material)[:\s]*([0-9]+)',
        'description': r'(?:description|issue|problem)[:\s]*([^,\n]+)',
        'market': r'(?:market|country)[:\s]*([^,\n]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details[key] = match.group(1).strip()
    
    return details

def analyze_israel_complaints(file_path: str = "test.txt"):
    """
    Main function to find and analyze Israel complaints
    """
    print("Israel Complaints Finder")
    print("=" * 50)
    
    # Find all potential Israel-related lines
    results = find_israel_complaints(file_path)
    
    if not results:
        print("No Israel-related content found in the file.")
        return
    
    print(f"\nFound {len(results)} lines mentioning Israel:")
    print("=" * 80)
    
    complaint_count = 0
    detailed_complaints = []
    
    for i, result in enumerate(results, 1):
        line_num = result['line_number']
        content = result['content']
        is_complaint = result['is_likely_complaint']
        
        print(f"\n{i}. Line {line_num}:")
        print(f"   Content: {content}")
        print(f"   Likely complaint: {'Yes' if is_complaint else 'No'}")
        
        if is_complaint:
            complaint_count += 1
            
            # Try to extract structured details
            details = extract_complaint_details(content)
            if details:
                print(f"   Extracted details: {details}")
                detailed_complaints.append({
                    'line': line_num,
                    'content': content,
                    'details': details
                })
        
        print("-" * 60)
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"Total lines mentioning Israel: {len(results)}")
    print(f"Likely complaints: {complaint_count}")
    print(f"Complaints with extracted details: {len(detailed_complaints)}")
    
    if detailed_complaints:
        print(f"\nDETAILED COMPLAINT LIST:")
        print("=" * 50)
        
        for i, complaint in enumerate(detailed_complaints, 1):
            print(f"\nComplaint {i}:")
            print(f"  Line: {complaint['line']}")
            print(f"  Content: {complaint['content']}")
            
            if complaint['details']:
                print(f"  Details:")
                for key, value in complaint['details'].items():
                    print(f"    {key.title()}: {value}")
    
    return detailed_complaints

def search_specific_patterns(file_path: str = "test.txt"):
    """
    Search for specific complaint patterns that might be structured differently
    """
    print("\nAdvanced Pattern Search for Israel Complaints")
    print("=" * 60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Split content into potential complaint blocks
    # Look for patterns like numbers, dates, or structured data
    
    # Pattern 1: Lines with Israel and numbers (likely complaint IDs)
    pattern1 = r'.*israel.*\d{6,}.*'
    matches1 = re.findall(pattern1, content, re.IGNORECASE | re.MULTILINE)
    
    print(f"Pattern 1 - Lines with Israel + 6+ digit numbers: {len(matches1)}")
    for i, match in enumerate(matches1, 1):
        print(f"  {i}. {match.strip()}")
    
    # Pattern 2: Structured complaint entries
    pattern2 = r'[^\n]*israel[^\n]*(?:\n[^\n]*(?:batch|material|complaint|defect)[^\n]*){0,3}'
    matches2 = re.findall(pattern2, content, re.IGNORECASE | re.MULTILINE)
    
    print(f"\nPattern 2 - Structured complaint blocks: {len(matches2)}")
    for i, match in enumerate(matches2, 1):
        print(f"  {i}. {match.strip()}")
    
    # Pattern 3: Table-like structures
    lines = content.split('\n')
    table_complaints = []
    
    for i, line in enumerate(lines):
        if 'israel' in line.lower():
            # Check surrounding lines for context
            start = max(0, i-2)
            end = min(len(lines), i+3)
            context = '\n'.join(lines[start:end])
            
            # If it looks like tabular data (multiple columns/separators)
            if line.count('\t') >= 2 or line.count('|') >= 2 or line.count(',') >= 3:
                table_complaints.append({
                    'line_number': i+1,
                    'content': line.strip(),
                    'context': context
                })
    
    print(f"\nPattern 3 - Tabular format: {len(table_complaints)}")
    for i, entry in enumerate(table_complaints, 1):
        print(f"  {i}. Line {entry['line_number']}: {entry['content']}")

def main():
    """
    Main execution function
    """
    file_path = "test.txt"
    
    print("Starting comprehensive search for Israel complaints...")
    print("=" * 80)
    
    # Run basic analysis
    complaints = analyze_israel_complaints(file_path)
    
    # Run advanced pattern search
    search_specific_patterns(file_path)
    
    print(f"\n" + "=" * 80)
    print("Search complete!")
    
    if complaints:
        print(f"Found {len(complaints)} detailed complaints from Israel.")
    else:
        print("No detailed complaint patterns found.")
        print("Check the advanced pattern results above for raw matches.")

if __name__ == "__main__":
    main()