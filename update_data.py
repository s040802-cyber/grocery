from data_dictionary import DataManager
from PriceEngine import PriceEngine

print("Starting automatic data update...")
dm = DataManager()
engine = PriceEngine(dm)
engine._download_datasets()
try:
    from unit_price import DataPreprocessor
    preprocessor = DataPreprocessor(engine.data_dir)
    preprocessor.preprocess()
except Exception as e:
    print(f"Failed to preprocess: {e}")
print("Data update complete! Files are ready in the 'data' folder.")
