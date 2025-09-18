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
                try:
                    coefficients = {
                        'a': float(row[1]) if pd.notna(row[1]) else 0.0,
                        'b': float(row[2]) if pd.notna(row[2]) else 0.0,
                        'c': float(row[3]) if pd.notna(row[3]) else 0.0,
                        'd': float(row[4]) if pd.notna(row[4]) else 0.0,
                        'e': float(row[5]) if pd.notna(row[5]) else 0.0,
                        'f': float(row[6]) if len(row) > 6 and pd.notna(row[6]) else 0.0
                    }
                    if not any(coefficients.values()):
                        skipped_rows.append(f"Row {index} ({name}): All coefficients are zero")
                        continue
                    data_ref.append({
                        'name': name,
                        'coefficients': coefficients
                    })
                except (ValueError, TypeError) as e:
                    skipped_rows.append(f"Row {index} ({name}): Invalid coefficients ({str(e)})")
        except Exception as e:
            skipped_rows.append(f"Excel parsing failed: {str(e)}")
    if not data_ref and debug:
        skipped_rows.append("No valid data from Excel. Using default data for debug mode.")
        data_ref = [
            {'name': 'Curve1', 'coefficients': {'a': 1e-10, 'b': -1e-7, 'c': 1e-4, 'd': -0.1, 'e': 100, 'f': 0}},
            {'name': 'Curve2', 'coefficients': {'a': 1.1e-10, 'b': -1.1e-7, 'c': 1.1e-4, 'd': -0.11, 'e': 110, 'f': 0}},
            {'name': 'Curve3', 'coefficients': {'a': 0, 'b': 0, 'c': 1e-4, 'd': -0.1, 'e': 100, 'f': 0}}
        ]
    if debug:
        return data_ref, skipped_rows
    return data_ref
