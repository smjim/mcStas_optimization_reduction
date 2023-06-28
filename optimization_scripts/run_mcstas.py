import hashlib
import csv
import os
import numpy as np

# for unique naming of output files
def generate_hash(*parameters):
	combined_parameters = ''.join(str(param) for param in parameters)
	hash_object = hashlib.sha256(combined_parameters.encode())
	hash_value = hash_object.hexdigest()
	return hash_value

# run simulation with params
def run(n, coll, apt_rad, R, output_dir):
	# const params: coll, apt_rad
	# var params: R 

	# generate parameter string for R
	params_string = ""
	print(R)
	for i in range(R.shape[0]):
		for j in range(R.shape[1]):
			param_name = f"{['R0_', 'alpha_', 'm_'][j]}{i+1}"
			param_value = R[i, j]
			params_string += f"{param_name}={param_value} "
			#params_string += #f"{param_name}=R[{i},{j}] "

	params_string = params_string.rstrip()
	hash_value = generate_hash(n, coll, apt_rad, R)

	filename = "{}run_{}".format(output_dir, hash_value)
	print("running command:\nmcrun --mpi=32 SANS1.instr -d {} -s 100100100 -n {} Wavelength_Min=0 Wavelength_Max=20 VS_Central_Wavelength=0 Channel=2 N={} Exit_slit_radius={:0.4f} {}".format(filename, n, coll, apt_rad, params_string))
	os.system("mcrun --mpi=32 SANS1.instr -d {} -s 100100100 -n {} Wavelength_Min=0 Wavelength_Max=20 VS_Central_Wavelength=0 Channel=2 N={} Exit_slit_radius={:0.4f} {}".format(filename, n, coll, apt_rad, params_string))
	return filename

# analyze simulation output
# return estimated countrate corrected for detector efficiency
def analyze(dirName):
	# Load data from dirName/Sample_Position_spectrum.dat
	sim_dat = np.loadtxt("{}/Sample_Position_spectrum.dat".format(dirName))
	L_sim = sim_dat[:,0] # [AA]
	I_sim = sim_dat[:,1] # range 0..20AA, binsize=0.05AA, *20 to normalize to [n/s/0.05AA]
	I_sim_err = sim_dat[:,2] # [n/s/0.05AA]

	# Scale data based on wavelength detector efficiency to find est. cps
	I_mes = I_sim*L_sim/(1.8e5)
	I_mes_err = I_sim_err*L_sim/(1.8e5)

	# Find total counts
	sim_sum = np.sum(I_mes)
	sim_err = np.sqrt(np.sum(np.square(I_mes_err)))

	return sim_sum, sim_err

# find mes_sum, mes_err for experiment with given const params
def experiment_data(coll, apt_rad):
	# Collimators, ap_radius, mes_sum, mes_err
	data = [ 
		[8, 0.01, 5130, 0.000777],
		[7, 0.01, 4090, 0.000757],
		[4, 0.01, 844, 1.68],
		[0, 0.01, 264, 0.727]
	]   

	for row in data:
		if row[0] == coll and row[1] == apt_rad:
			return row[2], row[3]

	# No match found, raise an error
	raise ValueError(f"No data available for coll={coll} and apt_rad={apt_rad}")


def objective_function(n, coll_values, apt_rad_values, R, output_dir, summary_file):
	err = 0 

	for coll in coll_values:
		for apt_rad in apt_rad_values:
			# find measured intensity for given const params
			mes_sum, mes_err = experiment_data(coll, apt_rad) 

			# run simulation with given const and var params
			outDir = run(n, coll, apt_rad, R, output_dir)
				
			# extract simulation estimated count rate
			sim_sum, sim_err = analyze(outDir)
				
			# write output to file
			line = [coll, apt_rad]
			for i in range(R.shape[0]):
				for j in range(R.shape[1]):
					line.append(R[i, j]) 
			line.extend([sim_sum, sim_err])
			with open(summary_file, 'a', newline='') as file:
				writer = csv.writer(file)
				writer.writerow(line)
					
			err += (mes_sum - sim_sum)**2 
			#err += (mes_sum/sim_sum - 1 )**2
				
	return err 
