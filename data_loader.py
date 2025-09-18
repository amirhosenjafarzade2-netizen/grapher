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
                    # Coefficients from highest to lowest degree (col1+)
                    coefficients = [float(x) if pd.notna(x) else 0.0 for x in row[1:]]
                    if not any(coefficients):
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
            {'name': 'Curve1', 'coefficients': [1e-10, -1e-7, 1e-4, -0.1, 100, 0]},  # 5th-degree
            {'name': 'Curve2', 'coefficients': [1.1e-10, -1.1e-7, 1.1e-4, -0.11, 110, 0]},  # 5th-degree
            {'name': 'Curve3', 'coefficients': [1e-4, -0.1, 100, 0]}  # 3rd-degree
        ]
    if debug:
        return data_ref, skipped_rows
    return data_ref
