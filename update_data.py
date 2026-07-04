from data_dictionary import DataManager
from PriceEngine import PriceEngine

print("Starting automatic data update...")
dm = DataManager()
# Instantiating PriceEngine automatically triggers the download of the latest supermarkets.json 
# and the 7-day old version, and runs the preprocessing step to format package sizes.
engine = PriceEngine(dm)
print("Data update complete! Files are ready in the 'data' folder.")
