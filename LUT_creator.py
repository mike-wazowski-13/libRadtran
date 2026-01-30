import numpy as np
import pandas as pd
import subprocess
import csv
import os

###### Functions ########

def input_writer(filename, variables):
    wavelength, aod, ssa, sza = variables

    content = f"""# Atmosphere & source
data_files_path /home/miguel/libRadtran/data/
atmosphere_file /home/miguel/libRadtran/data/atmmod/afglus.dat
source solar /home/miguel/libRadtran/data/solar_flux/atlas_plus_modtran

# Atmospheric components
mol_modify O3 300 DU
mol_modify H2O 8 mm
albedo 0.04

aerosol_default
aerosol_set_tau_at_wvl {wavelength} {aod}
aerosol_modify ssa scale {ssa}
aerosol_modify gg set 0.7

# Wavelength
wavelength {wavelength} {wavelength}

# Disable band parameterization for accurate spectral calculation
mol_abs_param crs

# Solver & geometry
rte_solver disort
number_of_streams 10
day_of_year 100
sza {sza}
altitude 0.01

# Output
output_user eglo edir edn
quiet
"""
    with open(f"{filename}.inp", "w") as f:
        f.write(content)


def librad_run(input_filename, output_filename):
    subprocess.run(f"../../bin/uvspec < {input_filename} > {output_filename}",shell=True)
    return pd.read_csv(output_filename, sep=r"\s+", header=None)

# Parameter ranges
wavelengths=np.arange(320, 361, 10) 
aod_range=np.arange(0.1, 1.51, 0.01)
ssa_range=np.arange(0.55, 1.01, 0.01)
sza_range=np.arange(10, 71, 2.5)

input_base="tmp_lut"
output_base="tmp_lut.out"
csv_file="libradtran_LUT.csv"

# Write CSV header once
with open(csv_file,"w",newline="") as f:
    writer=csv.writer(f)
    writer.writerow(["Wavelength","O3","AOD","SSA","SZA","Glob","Dir","Difu","DGR"])

counter=0
for wavelength in wavelengths:
    O3=300
    for aod in aod_range:
        for ssa in ssa_range:
            for sza in sza_range:
                variables=(wavelength,aod,ssa,sza)
                input_writer(input_base,variables)
                results=librad_run(f"{input_base}.inp",output_base)
                eglo=results.iloc[0,0]
                edir=results.iloc[0,1]
                edn=results.iloc[0,2]
                dgr=edir/eglo if eglo!=0 else np.nan
                # Append row directly to CSV
                with open(csv_file,"a",newline="") as f:
                    writer=csv.writer(f)
                    writer.writerow([wavelength,O3,aod,ssa,sza,eglo,edir,edn,dgr])
                counter+=1
                if counter%1000==0:
                    print(f"Completed {counter} simulations")

print("LUT generation completed.")

