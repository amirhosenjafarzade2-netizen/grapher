import pandas as pd
import numpy as np

def load_reference_data(uploaded_file, debug=False):
    """
    Load polynomial data from Excel file with enhanced validation and handling.
    
    Expected format:
    - Column 0: Curve name (string) - must be non-empty and valid
    - Column 1+: Polynomial coefficients (floats, highest degree first)
    
    Args:
        uploaded_file: Excel file object
        debug: If True, return skipped_rows list for debugging
    
    Returns:
        Tuple: (List of dicts with 'name' and 'coefficients' keys, list of skipped rows)
        When debug=False, second element is empty list []
    """
    data_ref = []
    skipped_rows = []
    
    # Maximum allowed polynomial degree (10)
    MAX_DEGREE = 10
    
    if uploaded_file is not None:
        try:
            # Read Excel without assuming header
            df_ref = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
            
            if df_ref.empty:
                skipped_rows.append("Excel file is empty")
            else:
                # Validate that we have at least 2 columns (name + coefficients)
                if df_ref.shape[1] < 2:
                    skipped_rows.append(f"Excel file has only {df_ref.shape[1]} column(s). Need at least 2 (name + coefficients)")
                else:
                    # Skip header rows and process only data rows
                    for index, row in df_ref.iterrows():
                        # Process each row - PASS DEBUG PARAMETER
                        process_row(row, index, data_ref, skipped_rows, MAX_DEGREE, debug)
                        
        except Exception as e:
            skipped_rows.append(f"Excel parsing failed: {str(e)}")
            if debug:
                print(f"Error reading Excel: {e}")
    
    # If no valid data and debug mode, add sample data
    if not data_ref and debug:
        skipped_rows.append("No valid data from Excel. Using default data for debug mode.")
        data_ref = generate_debug_data()
    
    if debug:
        print(f"Data loaded: {len(data_ref)} valid curves, {len(skipped_rows)} skipped rows")
        if skipped_rows:
            print("Skipped rows:")
            for skip in skipped_rows:
                print(f"  - {skip}")
    
    # FIXED: Always return 2 values for consistency
    # When debug=False, skipped_rows is empty list []
    return data_ref, skipped_rows


def process_row(row, index, data_ref, skipped_rows, max_degree, debug=False):
    """Process a single data row with strict validation."""
    
    # STRICT VALIDATION: Skip header rows, empty rows, and invalid data
    if not is_valid_data_row(row, index, debug):
        if debug:
            print(f"Row {index}: Skipped - invalid data row")
        return
    
    # Extract and validate name
    name = extract_valid_name(row[0], index)
    if not name:
        skipped_rows.append(f"Row {index}: Invalid or empty name")
        return
    
    # Check for duplicate names
    if any(entry['name'].lower() == name.lower() for entry in data_ref):
        skipped_rows.append(f"Row {index} ({name}): Duplicate curve name")
        return
    
    # Extract and validate coefficients
    coefficients = extract_valid_coefficients(row[1:], index, name, debug)
    if not coefficients:
        skipped_rows.append(f"Row {index} ({name}): No valid coefficients")
        return
    
    # Check for all-zero coefficients
    if all(abs(c) < 1e-12 for c in coefficients):  # Using small epsilon for floating point comparison
        skipped_rows.append(f"Row {index} ({name}): All coefficients are effectively zero")
        return
    
    # Check polynomial degree
    degree = len(coefficients) - 1
    if degree > max_degree:
        if debug:
            print(f"Row {index} ({name}): Truncating from degree {degree} to {max_degree}")
        coefficients = coefficients[:max_degree + 1]  # Keep up to degree 10
    
    # Remove leading zero coefficients
    while len(coefficients) > 1 and abs(coefficients[0]) < 1e-12:
        coefficients = coefficients[1:]
        if debug:
            print(f"Row {index} ({name}): Removed leading zero coefficient")
    
    # Final validation: at least one non-zero coefficient
    if all(abs(c) < 1e-12 for c in coefficients):
        skipped_rows.append(f"Row {index} ({name}): No non-zero coefficients after cleaning")
        return
    
    # Check for extreme coefficient values (for large ranges like -10000 to 10000)
    extreme_coeffs = [c for c in coefficients if abs(c) > 1e12]
    if extreme_coeffs and debug:
        print(f"Row {index} ({name}): Warning - extreme coefficients detected: {extreme_coeffs}")
    
    # Validate polynomial stability
    is_valid, warning = validate_polynomial(coefficients, name)
    if not is_valid:
        skipped_rows.append(f"Row {index} ({name}): {warning}")
        return
    elif warning and debug:
        print(f"Row {index} ({name}): {warning}")
    
    # Add to data reference
    data_ref.append({
        'name': name,
        'coefficients': coefficients,
        'original_degree': degree,
        'row_index': index
    })
    
    if debug:
        print(f"Row {index} ({name}): Loaded degree {len(coefficients)-1} polynomial")


def is_valid_data_row(row, index, debug=False):
    """Strict validation to determine if a row contains valid polynomial data."""
    # Skip if row is completely empty or NaN
    if len(row) == 0 or all(pd.isna(val) for val in row):
        return False
    
    # Skip header-like rows (common patterns)
    name_raw = row[0] if len(row) > 0 else None
    if name_raw is None or pd.isna(name_raw):
        return False
    
    name_str = str(name_raw).strip().lower()
    
    # Skip common header patterns
    header_patterns = [
        'name', 'curve', 'polynomial', 'coeff', 'coefficient', 'degree',
        'header', 'title', 'data', 'row', 'index', 'id', 'label',
        'a0', 'a1', 'a2', 'b0', 'c0', 'x', 'y'
    ]
    
    if name_str in header_patterns or name_str.startswith('header') or name_str.startswith('title'):
        return False
    
    # Skip if name looks like a number or empty
    try:
        float(name_str)
        return False  # Name is a number, likely a coefficient row
    except ValueError:
        pass  # Not a number, continue
    
    # Skip if name is too short (likely not meaningful)
    if len(name_str) < 2:
        return False
    
    # Check if we have at least one potential coefficient column with data
    has_data = False
    for val in row[1:]:
        if not pd.isna(val) and str(val).strip() != '':
            has_data = True
            break
    
    if not has_data:
        return False
    
    return True


def extract_valid_name(name_raw, index):
    """Extract and validate curve name from raw value."""
    if pd.isna(name_raw):
        return None
    
    name = str(name_raw).strip()
    
    # Skip empty names
    if not name or name.lower() in ['nan', 'none', '', 'null']:
        return None
    
    # Clean up name (remove extra whitespace, common prefixes)
    name = name.strip().replace('  ', ' ')
    
    # Skip if name is too generic or looks like data
    invalid_patterns = [
        'unnamed', 'curve', 'poly', 'equation', 'data', 'row', 
        'sample', 'test', 'example', 'default'
    ]
    
    name_lower = name.lower()
    if any(pattern in name_lower for pattern in invalid_patterns):
        return None
    
    # Ensure name is reasonable length
    if len(name) > 100:  # Too long for a name
        name = name[:50] + "..."
    
    return name


def extract_valid_coefficients(coeffs_raw, index, name, debug=False):
    """Extract and validate polynomial coefficients from raw values."""
    coefficients = []
    
    if len(coeffs_raw) == 0:
        return None
    
    for col_idx, value in enumerate(coeffs_raw):
        if pd.isna(value):
            # NaN values get 0.0 - but if ALL are NaN, we'll catch that later
            coefficients.append(0.0)
            continue
        
        value_str = str(value).strip()
        
        # Skip empty strings
        if value_str == '' or value_str.lower() in ['nan', 'none', 'null']:
            coefficients.append(0.0)
            continue
        
        # Try to convert to float
        try:
            coeff_value = float(value)
            coefficients.append(coeff_value)
        except (ValueError, TypeError):
            # Try numpy float64 for very large numbers
            try:
                coeff_value = np.float64(value)
                coefficients.append(coeff_value)
            except (ValueError, TypeError):
                if debug:
                    print(f"Row {index} ({name}): Invalid coefficient '{value}' in column {col_idx + 2}, using 0.0")
                coefficients.append(0.0)
    
    # If we have coefficients but they're all zero, return None to skip this row
    if all(abs(c) < 1e-12 for c in coefficients):
        return None
    
    return coefficients


def generate_debug_data():
    """Generate sample polynomial data for debugging."""
    # Sample polynomials that work well with large ranges (-10000 to 10000)
    debug_polynomials = [
        # Simple linear: y = 0.001x
        {'name': 'Linear Growth', 'coefficients': [0.001, 0.0]},
        
        # Quadratic: y = 0.000001x² - 0.01x + 50
        {'name': 'Parabolic', 'coefficients': [1e-6, -0.01, 50.0]},
        
        # Cubic: y = 1e-10x³ - 1e-6x² + 0.01x - 1
        {'name': 'Cubic Curve', 'coefficients': [1e-10, -1e-6, 0.01, -1.0]},
        
        # Higher degree but stable: y = sin(x)/1000 (approximated)
        {'name': 'Oscillatory', 'coefficients': [1e-6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.001]},
        
        # Constant with large offset
        {'name': 'Baseline', 'coefficients': [1000.0]}
    ]
    
    # Add metadata for compatibility
    for poly in debug_polynomials:
        poly['original_degree'] = len(poly['coefficients']) - 1
        poly['row_index'] = 'debug'
    
    return debug_polynomials


def validate_polynomial(coefficients, name=""):
    """
    Validate a single polynomial for numerical stability.
    
    Args:
        coefficients: List of float coefficients
        name: Curve name for error reporting
    
    Returns:
        Tuple (is_valid, warning_message)
    """
    if not coefficients:
        return False, f"{name}: Empty coefficients"
    
    # Convert to numpy array for better numerical analysis
    try:
        coeffs = np.array(coefficients, dtype=np.float64)
    except (ValueError, TypeError):
        return False, f"{name}: Invalid coefficient types"
    
    # Check for all zeros
    if np.all(np.abs(coeffs) < 1e-12):
        return False, f"{name}: All coefficients are zero"
    
    # Check degree
    degree = len(coeffs) - 1
    if degree > 10:
        return False, f"{name}: Degree {degree} exceeds maximum allowed (10)"
    
    # Check coefficient magnitude (for large x ranges)
    max_coeff = np.max(np.abs(coeffs))
    if max_coeff > 1e15:  # Even stricter limit
        return False, f"{name}: Extremely large coefficients (max: {max_coeff:.2e}) - will cause overflow"
    
    # Check for reasonable polynomial (at least one significant coefficient)
    significant_coeffs = [c for c in coeffs if abs(c) > 1e-10]
    if len(significant_coeffs) < 1:
        return False, f"{name}: No significant coefficients"
    
    # Check conditioning (simple heuristic for high degrees)
    if degree > 3:
        non_zero_coeffs = coeffs[np.abs(coeffs) > 1e-12]
        if len(non_zero_coeffs) > 1:
            coeff_ratio = np.max(np.abs(non_zero_coeffs)) / np.min(np.abs(non_zero_coeffs))
            if coeff_ratio > 1e12:  # Stricter limit
                return False, f"{name}: Poorly conditioned polynomial (coeff ratio: {coeff_ratio:.2e})"
    
    return True, f"{name}: Valid polynomial"


def preview_data(uploaded_file, max_rows=5):
    """
    Quick preview of Excel data structure without full processing.
    
    Args:
        uploaded_file: Excel file object
        max_rows: Maximum number of rows to preview
    
    Returns:
        Dictionary with preview information
    """
    if uploaded_file is None:
        return {"error": "No file provided"}
    
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl', nrows=max_rows)
        preview = {
            "rows": len(df),
            "columns": len(df.columns),
            "sample_data": df.head().to_dict('records'),
            "first_row": df.iloc[0].to_list() if len(df) > 0 else None,
            "column_types": [str(type(x).__name__) for x in df.iloc[0]] if len(df) > 0 else [],
            "potential_curves": []
        }
        
        # Quick scan for potential valid curves
        for i, row in df.head(max_rows).iterrows():
            if is_valid_data_row(row, i, debug=False):
                preview["potential_curves"].append({
                    "row": i,
                    "name": str(row[0]) if len(row) > 0 and not pd.isna(row[0]) else "Unnamed",
                    "coeff_count": len([x for x in row[1:] if not pd.isna(x)])
                })
        
        return preview
    except Exception as e:
        return {"error": f"Preview failed: {str(e)}"}


# Legacy function for backward compatibility
def load_data(uploaded_file, debug=False):
    """Deprecated: Use load_reference_data instead."""
    import warnings
    warnings.warn("load_data is deprecated. Use load_reference_data instead.", DeprecationWarning)
    return load_reference_data(uploaded_file, debug)
