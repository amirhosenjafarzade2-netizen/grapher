import pandas as pd
import numpy as np

def load_reference_data(uploaded_file, debug=False):
    """
    Load polynomial data from Excel file with enhanced validation and handling.
    
    Expected format:
    - Column 0: Curve name (string)
    - Column 1+: Polynomial coefficients (floats, highest degree first)
    
    Args:
        uploaded_file: Excel file object
        debug: If True, return skipped_rows list for debugging
    
    Returns:
        List of dicts with 'name' and 'coefficients' keys, and optionally skipped_rows
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
        return data_ref, skipped_rows
    
    return data_ref


def process_row(row, index, data_ref, skipped_rows, max_degree, debug=False):
    """Process a single data row and validate its contents."""
    # Extract and clean name
    name_raw = row[0] if pd.notna(row[0]) else None
    name = str(name_raw).strip() if name_raw is not None else None
    
    if not name or name.lower() in ['nan', 'none', '']:
        skipped_rows.append(f"Row {index}: Empty or invalid name")
        return
    
    # Check for duplicate names
    if any(entry['name'].lower() == name.lower() for entry in data_ref):
        skipped_rows.append(f"Row {index} ({name}): Duplicate curve name")
        return
    
    # Extract coefficients from columns 1+ (highest degree first)
    coefficients_raw = row[1:] if len(row) > 1 else []
    
    # Convert to floats, handle NaN as 0.0, and validate
    coefficients = []
    invalid_coeff_count = 0
    
    for col_idx, value in enumerate(coefficients_raw):
        try:
            if pd.isna(value):
                coeff_value = 0.0
            else:
                coeff_value = float(value)
            coefficients.append(coeff_value)
        except (ValueError, TypeError):
            # For large ranges, allow very large coefficients but flag them
            try:
                coeff_value = np.float64(value)
                coefficients.append(coeff_value)
            except (ValueError, TypeError):
                coefficients.append(0.0)
                invalid_coeff_count += 1
                if debug:
                    print(f"Row {index} ({name}): Invalid coefficient in column {col_idx + 2}, using 0.0")
    
    # Check for all-zero coefficients
    if all(abs(c) < 1e-12 for c in coefficients):  # Using small epsilon for floating point comparison
        skipped_rows.append(f"Row {index} ({name}): All coefficients are effectively zero")
        return
    
    # Check polynomial degree
    degree = len(coefficients) - 1
    if degree > max_degree:
        skipped_rows.append(f"Row {index} ({name}): Degree {degree} exceeds maximum allowed ({max_degree}). Truncated.")
        coefficients = coefficients[:max_degree + 1]  # Keep up to degree 10
    
    # Check for extreme coefficient values (for large ranges like -10000 to 10000)
    extreme_coeffs = [c for c in coefficients if abs(c) > 1e12]
    if extreme_coeffs and debug:
        print(f"Row {index} ({name}): Warning - extreme coefficients detected: {extreme_coeffs}")
    
    # Check if leading coefficients are zero (can cause numerical issues)
    while len(coefficients) > 1 and abs(coefficients[0]) < 1e-12:
        coefficients = coefficients[1:]
        if debug:
            print(f"Row {index} ({name}): Removed leading zero coefficient")
    
    # Final validation: at least one non-zero coefficient
    if all(abs(c) < 1e-12 for c in coefficients):
        skipped_rows.append(f"Row {index} ({name}): No non-zero coefficients after cleaning")
        return
    
    # Add to data reference
    data_ref.append({
        'name': name,
        'coefficients': coefficients,
        'original_degree': degree,
        'row_index': index
    })
    
    if debug:
        print(f"Row {index} ({name}): Loaded degree {len(coefficients)-1} polynomial")


def generate_debug_data():
    """Generate sample polynomial data for debugging."""
    # Sample polynomials that work well with large ranges (-10000 to 10000)
    debug_polynomials = [
        # Simple linear: y = 0.001x
        {'name': 'Linear', 'coefficients': [0.001, 0.0]},
        
        # Quadratic: y = 0.000001x² - 0.01x + 50
        {'name': 'Quadratic', 'coefficients': [1e-6, -0.01, 50.0]},
        
        # Cubic: y = 1e-10x³ - 1e-6x² + 0.01x - 1
        {'name': 'Cubic', 'coefficients': [1e-10, -1e-6, 0.01, -1.0]},
        
        # Higher degree but stable: y = sin(x)/1000 (approximated)
        {'name': 'Oscillatory', 'coefficients': [0.0, 0.0, 0.0, 0.0, 0.0, 1e-6, 0.0, 0.0, 0.0, 0.0, 0.001]},
        
        # Constant with large offset
        {'name': 'Constant', 'coefficients': [10000.0]}
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
        return True, f"{name}: High degree ({degree}) - may have numerical issues"
    
    # Check coefficient magnitude (for large x ranges)
    max_coeff = np.max(np.abs(coeffs))
    if max_coeff > 1e12:
        return True, f"{name}: Extremely large coefficients (max: {max_coeff:.2e}) - may cause overflow"
    
    # Check conditioning (simple heuristic)
    if degree > 3:
        coeff_ratio = np.max(np.abs(coeffs)) / np.min(np.abs(coeffs[coeffs != 0]))
        if coeff_ratio > 1e10:
            return True, f"{name}: Poorly conditioned polynomial (coeff ratio: {coeff_ratio:.2e})"
    
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
            "first_row": df.iloc[0].tolist() if len(df) > 0 else None,
            "column_types": [str(type(x).__name__) for x in df.iloc[0]] if len(df) > 0 else []
        }
        return preview
    except Exception as e:
        return {"error": f"Preview failed: {str(e)}"}


# Legacy function for backward compatibility
def load_data(uploaded_file, debug=False):
    """Deprecated: Use load_reference_data instead."""
    import warnings
    warnings.warn("load_data is deprecated. Use load_reference_data instead.", DeprecationWarning)
    return load_reference_data(uploaded_file, debug)
