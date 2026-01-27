import numpy as np
import pandas as pd
import subprocess

#Define the range (first, last, step) of each magnitude of the following list
#VARIABLE NUMBERS: O3:0 | albedo:2 | AOD:3 | SSA:5 | DOY:6
magnitudes = ["O3", "albedo", "AOD", "SSA", "DOY"]

mg0 = np.arange(200, 501, 100)
mg2 = np.arange(0.0, 1.0, 0.1)
mg3 = np.arange(0.01, 1.6, 0.1)
mg5 = np.arange(0.6, 1.01, 0.05)
mg6 = np.arange(0, 301, 100)
mg_list = [mg0, mg2, mg3, mg5, mg6]

#And now lets define 
default = [300, 0.05, 0.4, 0.95, 150]

def input_writer(filename, fit_values, variable, value, WL_nm, sza):
    constants = fit_values.copy()
    constants[variable] = value
    O3, albedo, aod, ssa, doy = constants

    content = f"""# Atmosphere & source
data_files_path /home/miguel/libRadtran/data/
atmosphere_file /home/miguel/libRadtran/data/atmmod/afglus.dat # Location of the extraterrestrial spectrum
source solar /home/miguel/libRadtran/data/solar_flux/atlas_plus_modtran
#source solar /home/miguel/libRadtran/data/solar_flux/kurudz_0.1nm.dat

# Atmospheric components
mol_modify O3 {O3} DU
mol_modify H2O 10 mm
albedo {albedo}

aerosol_default
aerosol_set_tau_at_wvl {WL_nm} {aod}
aerosol_modify ssa scale {ssa}
aerosol_modify gg set 0.7

# Wavelength 
wavelength {WL_nm} {WL_nm}
#No spline is needed

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
    subprocess.run(f"../../bin/uvspec < {input_filename} > {output_filename}", shell=True)
    #Waits until the previous process is done (by default subprocess.run does it)
    results = pd.read_csv(output_filename, sep=r'\s+', header=None)
    return results


##################################

SZA = 30
df = []

wl_range = range(320, 361, 10)  

for iter in range(len(mg_list)):
    variable_range = mg_list[iter]

    for i in variable_range:

        for WL in wl_range:
            # Write input
            input_writer(f"input_{SZA}_{WL}", default, iter, i, WL, SZA)

            # Run model
            out_df = librad_run(f"input_{SZA}_{WL}.inp", f"out_{SZA}_{WL}.txt")

            # Read matching control
            control_df = pd.read_csv(f"ctrl_out_{WL}_{SZA}.txt",sep=r"\s+",header=None)

            # Row order: variable, value, WL, diffs
            row = [magnitudes[iter], i, WL]

            for j in range(1, 4):
                new_col = out_df[j]
                control_col = control_df[j]

                diff = (100 * (new_col - control_col) / control_col).values[0]
                row.append(diff)

            df.append(row)

df_results = pd.DataFrame(df, columns=["variable","value","WL","Glob_dif","Dir_dif","Difu_dif"])

df_results.to_csv(f"libRad{SZA}_monochr.csv", index=False)

   