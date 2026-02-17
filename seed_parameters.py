"""
Seed test parameters for all common pathology tests.
Run: python seed_parameters.py
"""
from app import create_app
from extensions import db
from models import Test, TestParameter

app = create_app()

# ─── Parameter data: { test_name: [(param_name, unit, range_text, min, max, order), ...] }
PARAMETERS = {
    'Complete Blood Count (CBC)': [
        ('Hemoglobin', 'g/dL', '12.0 - 17.5', 12.0, 17.5, 1),
        ('RBC Count', 'million/cumm', '4.5 - 5.5', 4.5, 5.5, 2),
        ('WBC Count (TLC)', '/cumm', '4000 - 11000', 4000, 11000, 3),
        ('Platelet Count', 'lakh/cumm', '1.5 - 4.0', 1.5, 4.0, 4),
        ('PCV / Hematocrit', '%', '36 - 46', 36, 46, 5),
        ('MCV', 'fL', '76 - 96', 76, 96, 6),
        ('MCH', 'pg', '27 - 32', 27, 32, 7),
        ('MCHC', 'g/dL', '32 - 36', 32, 36, 8),
        ('RDW', '%', '11.5 - 14.5', 11.5, 14.5, 9),
        ('Neutrophils', '%', '40 - 70', 40, 70, 10),
        ('Lymphocytes', '%', '20 - 40', 20, 40, 11),
        ('Eosinophils', '%', '1 - 6', 1, 6, 12),
        ('Monocytes', '%', '2 - 10', 2, 10, 13),
        ('Basophils', '%', '0 - 1', 0, 1, 14),
        ('ESR', 'mm/hr', '0 - 20', 0, 20, 15),
    ],

    'Liver Function Test (LFT)': [
        ('Total Bilirubin', 'mg/dL', '0.1 - 1.2', 0.1, 1.2, 1),
        ('Direct Bilirubin', 'mg/dL', '0.0 - 0.3', 0.0, 0.3, 2),
        ('Indirect Bilirubin', 'mg/dL', '0.1 - 0.9', 0.1, 0.9, 3),
        ('SGOT (AST)', 'U/L', '0 - 40', 0, 40, 4),
        ('SGPT (ALT)', 'U/L', '0 - 40', 0, 40, 5),
        ('Alkaline Phosphatase (ALP)', 'U/L', '44 - 147', 44, 147, 6),
        ('GGT', 'U/L', '9 - 48', 9, 48, 7),
        ('Total Protein', 'g/dL', '6.3 - 8.2', 6.3, 8.2, 8),
        ('Albumin', 'g/dL', '3.5 - 5.5', 3.5, 5.5, 9),
        ('Globulin', 'g/dL', '2.0 - 3.5', 2.0, 3.5, 10),
        ('A/G Ratio', '', '1.0 - 2.2', 1.0, 2.2, 11),
    ],

    'Kidney Function Test (KFT)': [
        ('Blood Urea', 'mg/dL', '15 - 40', 15, 40, 1),
        ('Serum Creatinine', 'mg/dL', '0.6 - 1.4', 0.6, 1.4, 2),
        ('Uric Acid', 'mg/dL', '3.4 - 7.0', 3.4, 7.0, 3),
        ('BUN', 'mg/dL', '7 - 20', 7, 20, 4),
        ('Sodium (Na+)', 'mEq/L', '135 - 145', 135, 145, 5),
        ('Potassium (K+)', 'mEq/L', '3.5 - 5.1', 3.5, 5.1, 6),
        ('Chloride (Cl-)', 'mEq/L', '96 - 106', 96, 106, 7),
        ('Calcium', 'mg/dL', '8.5 - 10.5', 8.5, 10.5, 8),
    ],

    'Lipid Profile': [
        ('Total Cholesterol', 'mg/dL', '< 200 (Desirable)', None, 200, 1),
        ('Triglycerides', 'mg/dL', '< 150 (Normal)', None, 150, 2),
        ('HDL Cholesterol', 'mg/dL', '> 40 (Desirable)', 40, None, 3),
        ('LDL Cholesterol', 'mg/dL', '< 100 (Optimal)', None, 100, 4),
        ('VLDL Cholesterol', 'mg/dL', '5 - 40', 5, 40, 5),
        ('TC/HDL Ratio', '', '< 4.5', None, 4.5, 6),
    ],

    'Thyroid Profile (T3, T4, TSH)': [
        ('T3 (Triiodothyronine)', 'ng/dL', '80 - 200', 80, 200, 1),
        ('T4 (Thyroxine)', 'µg/dL', '5.0 - 12.0', 5.0, 12.0, 2),
        ('TSH', 'µIU/mL', '0.4 - 4.0', 0.4, 4.0, 3),
        ('Free T4', 'ng/dL', '0.8 - 1.8', 0.8, 1.8, 4),
    ],

    'TSH Ultra Sensitive': [
        ('TSH (Ultra Sensitive)', 'µIU/mL', '0.35 - 4.94', 0.35, 4.94, 1),
    ],

    'Blood Sugar (Fasting)': [
        ('Fasting Blood Glucose', 'mg/dL', '70 - 100', 70, 100, 1),
    ],

    'Blood Sugar (PP)': [
        ('Post Prandial Blood Glucose', 'mg/dL', '< 140', None, 140, 1),
    ],

    'HbA1c': [
        ('HbA1c (Glycosylated Hb)', '%', '4.0 - 5.6 (Normal)', 4.0, 5.6, 1),
        ('Estimated Avg. Glucose', 'mg/dL', '68 - 114', 68, 114, 2),
    ],

    'Urine Routine & Microscopy': [
        ('Color', '', 'Pale Yellow - Amber', None, None, 1),
        ('Appearance', '', 'Clear', None, None, 2),
        ('pH', '', '4.5 - 8.0', 4.5, 8.0, 3),
        ('Specific Gravity', '', '1.005 - 1.030', 1.005, 1.030, 4),
        ('Glucose', '', 'Absent', None, None, 5),
        ('Protein / Albumin', '', 'Absent', None, None, 6),
        ('Ketone Bodies', '', 'Absent', None, None, 7),
        ('Blood / Hemoglobin', '', 'Absent', None, None, 8),
        ('Bilirubin', '', 'Absent', None, None, 9),
        ('Urobilinogen', 'mg/dL', '0.1 - 1.0', 0.1, 1.0, 10),
        ('Nitrite', '', 'Absent', None, None, 11),
        ('Pus Cells', '/HPF', '0 - 5', 0, 5, 12),
        ('Red Blood Cells', '/HPF', '0 - 2', 0, 2, 13),
        ('Epithelial Cells', '/HPF', '0 - 5', 0, 5, 14),
        ('Casts', '/LPF', 'Absent', None, None, 15),
        ('Crystals', '', 'Absent', None, None, 16),
        ('Bacteria', '', 'Absent', None, None, 17),
    ],

    'Urine Culture': [
        ('Organism Isolated', '', 'No Growth', None, None, 1),
        ('Colony Count', 'CFU/mL', '', None, None, 2),
        ('Sensitivity Pattern', '', '', None, None, 3),
    ],

    'ESR': [
        ('ESR (Westergren)', 'mm/1st hr', '0 - 20', 0, 20, 1),
    ],

    'Blood Group & Rh': [
        ('Blood Group (ABO)', '', 'A / B / AB / O', None, None, 1),
        ('Rh Factor', '', 'Positive / Negative', None, None, 2),
    ],

    'Dengue NS1 Antigen': [
        ('Dengue NS1 Antigen', '', 'Negative', None, None, 1),
        ('Dengue IgG Antibody', '', 'Negative', None, None, 2),
        ('Dengue IgM Antibody', '', 'Negative', None, None, 3),
    ],

    'Typhoid (Widal)': [
        ('S.Typhi O Antigen', 'Titer', '< 1:80', None, None, 1),
        ('S.Typhi H Antigen', 'Titer', '< 1:80', None, None, 2),
        ('S.Paratyphi AH', 'Titer', '< 1:80', None, None, 3),
        ('S.Paratyphi BH', 'Titer', '< 1:80', None, None, 4),
    ],

    'Hepatitis B (HBsAg)': [
        ('HBsAg (Hepatitis B Surface Antigen)', '', 'Non-Reactive', None, None, 1),
    ],
}


def seed_test_parameters():
    with app.app_context():
        added = 0
        skipped = 0

        for test_name, params in PARAMETERS.items():
            test = Test.query.filter_by(name=test_name).first()
            if not test:
                print(f"[SKIP] Test '{test_name}' not found in DB")
                skipped += 1
                continue

            # Check if parameters already exist
            existing = TestParameter.query.filter_by(test_id=test.id).count()
            if existing > 0:
                print(f"[OK] '{test_name}' already has {existing} parameters")
                continue

            for param_name, unit, range_text, range_min, range_max, order in params:
                tp = TestParameter(
                    test_id=test.id,
                    parameter_name=param_name,
                    unit=unit,
                    normal_range_text=range_text,
                    normal_range_min=range_min,
                    normal_range_max=range_max,
                    display_order=order
                )
                db.session.add(tp)
                added += 1

            print(f"[OK] Added {len(params)} parameters for '{test_name}'")

        db.session.commit()
        print(f"\nDone! Added {added} parameters. Skipped {skipped} tests.")


if __name__ == '__main__':
    seed_test_parameters()
