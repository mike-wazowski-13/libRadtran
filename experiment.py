import numpy as np
import pandas as pd
import subprocess

def input_writer(filename, values, sza, aod):

    O3, H2O, albedo = values

    content = f"""# Atmosphere & source
data_files_path /home/miguel/libRadtran/data/
atmosphere_file /home/miguel/libRadtran/data/atmmod/afglus.dat # Location of the extraterrestrial spectrum
source solar /home/miguel/libRadtran/data/solar_flux/atlas_plus_modtran
#source solar /home/miguel/libRadtran/data/solar_flux/kurudz_0.1nm.dat

# Atmospheric components
mol_modify O3 {O3} DU
mol_modify H2O {H2O} mm
albedo {albedo}

aerosol_default
aerosol_modify tau set {aod}
#aerosol_angstrom    0.01 0.0001
aerosol_modify ssa set 0.9500000000000003
aerosol_modify gg set 0.7

# Wavelength 
wavelength 289.0 366.0
spline 290.000 365.000 0.5

# Disable band parameterization for accurate spectral calculation
mol_abs_param crs

# Solver & geometry
rte_solver disort
number_of_streams 10
sza {sza}
altitude 0.1

# Output
output_user lambda eglo edir edn
quiet
"""

    with open(f"{filename}.inp", "w") as file:
        file.write(content)

def residual_calc(observed, predicted):
    observed = np.array(observed)
    predicted = np.array(predicted)

    rmse = np.sqrt(np.mean((observed - predicted) ** 2))
    return rmse

def librad_run(input_filename, output_filename):
#Runs libradtran and returns you a df with 4 columns: WL, Glob, Dir, Dif
#you can acces them by: results[i], being i the number of the column, and "results" how you decide to name the df
    subprocess.run(f"../bin/uvspec < {input_filename} > {output_filename}", shell=True)
    #Waits until the previous process is done (by default subprocess.run does it)
    results = pd.read_csv(output_filename, sep=r'\s+', header=None)
    return results

##################################

conditions = [300, 7.5, 0.6]
input_writer("prueba_writer",conditions,0.15, 48)

prob = librad_run("prueba_writer.inp", "prueba_out.txt")

print(prob[0])