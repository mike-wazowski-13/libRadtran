import numpy as np
import pandas as pd
import subprocess

#select the variable to modify and the range (first, last, step)

chosen_variable = 4
#VARIABLE NUMBERS: O3:0 | H2O:1 | albedo:2 | AOD:3 | angstom:4 | SSA:5 | DOY:6
variable_range = np.arange(0.00, 1.10, 0.20) #last not included

default = [300, 10, 0.2, 0.1, 0.5, 0.95, 150]

def input_writer(filename, fit_values, variable, value, sza):

    fit_values[variable] = value
    O3, H2O, albedo, aod, alpha, ssa, doy= fit_values

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

df = []

for i in variable_range:
    input_writer("input_30",default, chosen_variable, i, 30)
    out_df = librad_run("input_30.inp", "out30.txt")

    control_df = pd.read_csv("control_out_30.txt", sep=r"\s+", header=None)
    #I have control and the new df both with 4 columns: WL, Gob, Dir, Difu
    
    row = [chosen_variable, i]
    for j in range(1,4):
        new_col = out_df[j]
        control_col = control_df[j]
        diff = difference_percent(new_col, control_col)
        row.append(diff)
    df.append(row)

df_results = pd.DataFrame(df, columns=["variable", "value", "Glob_dif", "Dir_dif", "Difu_dif"])

print(df_results)