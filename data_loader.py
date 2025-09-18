import pandas as pd
import numpy as np

def load_reference_data(uploaded_file):
    data_ref = []
    if uploaded_file is not None:
        try:
            df_ref = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
            for index, row in df_ref.iterrows():
                name = str(row[0]).strip() if pd.notna(row[0]) else None
                if not name:
                    continue
                # Collect coeffs (high to low degree)
                coefficients = [float(val) for val in row[1:] if pd.notna(val) and np.isfinite(val)]
                if not coefficients:
                    continue
                # Detect degree: highest index with non-zero coeff
                coeffs_rev = coefficients[::-1]
                degree = len(coeffs_rev) - 1
                while degree > 0 and abs(coeffs_rev[degree]) < 1e-10:
                    degree -= 1
                data_ref.append({
                    'name': name,
                    'coefficients': coeffs_rev[:degree+1],
                    'degree': degree
                })
        except Exception as e:
            pass  # Error handling in app.py
    if not data_ref:
        # Sample data
        data_ref = [
            {'name': 'Curve1', 'coefficients': [1e-10, -1e-7, 1e-4, -0.1, 100, 0], 'degree': 5},
            {'name': 'Curve2', 'coefficients': [1.1e-10, -1.1e-7, 1.1e-4, -0.11, 110, 0], 'degree': 5},
        ]
    return data_ref
