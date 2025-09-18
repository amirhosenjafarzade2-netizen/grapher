import pandas as pd
import numpy as np

def load_reference_data(uploaded_file, debug=False):
    data_ref = []
    skipped_rows = []
    if uploaded_file is not None:
        try:
            df_ref = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
            for index, row in df_ref.iterrows():
                name = str(row[0]).strip() if pd.notna(row[0]) else None
                if not name:
                    skipped_rows.append(f"Row {index}: Empty or invalid name")
                    continue
                # Collect coeffs (high to low degree)
                try:
                    coefficients = [float(val) for val in row[1:] if pd.notna(val)]
                    if not coefficients:
                        skipped_rows.append(f"Row {index} ({name}): No valid coefficients")
                        continue
                    # Validate coefficients
                    if not all(np.isfinite(c) for c in coefficients):
                        skipped_rows.append(f"Row {index} ({name}): Non-finite coefficients")
                        continue
                    # Detect degree
                    coeffs_rev = coefficients[::-1]
                    degree = len(coeffs_rev) - 1
                    while degree > 0 and abs(coeffs_rev[degree]) < 1e-10:
                        degree -= 1
                    if degree == 0 and abs(coeffs_rev[0]) < 1e-10:
                        skipped_rows.append(f"Row {index} ({name}): All coefficients near zero")
                        continue
                    data_ref.append({
                        'name': name,
                        'coefficients': coeffs_rev[:degree+1],
                        'degree': degree
                    })
                except (ValueError, TypeError) as e:
                    skipped_rows.append(f"Row {index} ({name}): Invalid coefficients ({str(e)})")
        except Exception as e:
            skipped_rows.append(f"Excel parsing failed: {str(e)}")
    if not data_ref:
        skipped_rows.append("No valid data from Excel. Using sample data.")
        # Sample data: more varied for testing
        data_ref = [
            {'name': 'Curve1', 'coefficients': [1e-5, -0.01, 10, 100], 'degree': 3},
            {'name': 'Curve2', 'coefficients': [2e-5, -0.02, 20, 200], 'degree': 3},
            {'name': 'Curve3', 'coefficients': [0, 0, 0.1, 50], 'degree': 2},
        ]
    if debug:
        return data_ref, skipped_rows
    return data_ref
