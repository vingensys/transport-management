# check_env.py

print("🔍 Checking Python Environment...")

try:
    import numpy as np
    import matplotlib.pyplot as plt
    import sklearn
    import tensorflow as tf
    print("✅ numpy version:", np.__version__)
    print("✅ matplotlib version:", plt.__version__)
    print("✅ scikit-learn version:", sklearn.__version__)
    print("✅ tensorflow version:", tf.__version__)
except ImportError as e:
    print("❌ Import failed:", e)
except Exception as e:
    print("⚠️ Unexpected error:", e)

print("\n🧠 TensorFlow GPU availability:", tf.config.list_physical_devices('GPU'))
print("✅ Environment check complete.")
