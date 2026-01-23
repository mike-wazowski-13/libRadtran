import numpy as np
import pandas as pd
import subprocess

#Define the range (first, last, step) of each magnitude of the following list
#VARIABLE NUMBERS: O3:0 | H2O:1 | albedo:2 | AOD:3 | angstom:4 | SSA:5 | DOY:6
magnitudes = ["O3", "H2O", "albedo", "AOD", "angstrom", "SSA", "DOY"]

mg0 = np.arange(200, 501, 100)
mg1 = np.arange(5, 36, 10)
mg2 = np.arange(0.0, 1.1, 0.2)
mg3 = np.arange(0.01, 1.6, 0.1)
mg4 = np.arange(0.00, 1.10, 0.20) 
mg5 = np.arange(0.6, 1.01, 0.05)
mg6 = np.arange(0, 301, 100)
mg_list = [mg0, mg1, mg2, mg3, mg4, mg5, mg6]

#And now lets define 
default = [300, 10, 0.2, 0.1, 0.5, 0.95, 150]

def input_writer(filename, fit_values, variable, value, sza):
    constants = fit_values.copy()
    constants[variable] = value
    O3, H2O, albedo, aod, alpha, ssa, doy = constants

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
aerosol_angstrom    {alpha} 0.001
aerosol_modify ssa set {ssa}
aerosol_modify gg set 0.7

# Wavelength 
wavelength 289.0 366.0
spline 290.000 365.000 0.5

# Disable band parameterization for accurate spectral calculation
mol_abs_param crs

# Solver & geometry
rte_solver disort
number_of_streams 10
day_of_year {doy}
sza {sza}
altitude 0.1

# Output
output_user lambda eglo edir edn
quiet
"""

    with open(f"{filename}.inp", "w") as file:
        file.write(content)

def librad_run(input_filename, output_filename):
#Runs libradtran and returns you a df with 4 columns: WL, Glob, Dir, Dif
#you can acces them by: results[i], being i the number of the column, and "results" how you decide to name the df
    subprocess.run(f"../bin/uvspec < {input_filename} > {output_filename}", shell=True)
    #Waits until the previous process is done (by default subprocess.run does it)
    results = pd.read_csv(output_filename, sep=r'\s+', header=None)
    return results

def difference_percent(control_col, new_col):
    # Ensure same length
    if len(control_col) != len(new_col):
        raise ValueError("Input columns must have the same length.")
    
    diff = new_col - control_col
    rms_diff = np.sqrt(np.mean(diff**2))
    rms_control = np.sqrt(np.mean(control_col**2))
    
    percent_rms = 100 * rms_diff / rms_control
    return percent_rms

##################################
SZA = 30
df = []

for iter in range(len(mg_list)):
    variable_range = mg_list[iter]

    for i in variable_range:
        input_writer(f"input_{SZA}",default, iter, i, SZA)
        out_df = librad_run(f"input_{SZA}.inp", f"out{SZA}.txt")

        control_df = pd.read_csv(f"control_out_{SZA}.txt", sep=r"\s+", header=None)
        #I have control and the new df both with 4 columns: WL, Gob, Dir, Difu
        
        row = [magnitudes[iter], i]
        for j in range(1,4):
            new_col = out_df[j]
            control_col = control_df[j]
            diff = difference_percent(new_col, control_col)
            row.append(diff)
        df.append(row)

df_results = pd.DataFrame(df, columns=["variable", "value", "Glob_dif", "Dir_dif", "Difu_dif"])
df_results.to_csv(f"libRad{SZA}_variability.csv", index=False)

print(df_results)