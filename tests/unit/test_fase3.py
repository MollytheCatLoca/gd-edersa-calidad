#!/usr/bin/env python3
"""Test Fase 3 functions"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the functions
from dashboard.pages.fase3_datos import (
    create_tab1_overview,
    create_tab2_quality,
    create_tab3_temporal,
    create_tab4_correlations,
    create_tab5_hourly,
    create_tab6_sensitivity,
    create_tab7_critical,
    create_tab8_ramps,
    create_tab9_duration,
    create_tab10_typical,
    create_tab11_findings,
    create_tab12_recommendations
)

# Test each function
functions = [
    ("Tab 1 - Overview", create_tab1_overview),
    ("Tab 2 - Quality", create_tab2_quality),
    ("Tab 3 - Temporal", create_tab3_temporal),
    ("Tab 4 - Correlations", create_tab4_correlations),
    ("Tab 5 - Hourly", create_tab5_hourly),
    ("Tab 6 - Sensitivity", create_tab6_sensitivity),
    ("Tab 7 - Critical", create_tab7_critical),
    ("Tab 8 - Ramps", create_tab8_ramps),
    ("Tab 9 - Duration", create_tab9_duration),
    ("Tab 10 - Typical", create_tab10_typical),
    ("Tab 11 - Findings", create_tab11_findings),
    ("Tab 12 - Recommendations", create_tab12_recommendations)
]

print("Testing Fase 3 tab functions...")
print("="*60)

for name, func in functions:
    try:
        result = func()
        print(f"✅ {name}: OK")
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        import traceback
        traceback.print_exc()
        print()

print("="*60)