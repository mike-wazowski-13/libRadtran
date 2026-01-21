import pandas as pd

df = pd.read_csv(r"C:\Users\miguel.huerta\Desktop\PhD\Kyriaki_libradtran\control_out_30.txt", sep=r"\s+", header=None)
print(df)