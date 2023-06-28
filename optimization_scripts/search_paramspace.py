# perform organized search of parameter space 
# James Rogers, jroger87@vols.utk.edu
# 6-20-2023

import numpy as np
import time
import csv
import os
import hashlib
import argparse

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

def main(output_dir, num_samples):
	# Step 0: Open summary file for writing results
	summary_file = "{}/output.dat".format(output_dir)
	num_ROIs = 7
	n = 1e8
	with open(summary_file, 'w', newline='') as file:
		writer = csv.writer(file)

		# write header
		header = ['coll', 'ap_radius']
		for i in range(num_ROIs):
			for j, prefix in enumerate(['R0_', 'alpha_', 'm_']):
				param_name = f"{prefix}{i+1}"
				header.append(param_name)
		header.extend(['mes_sum', 'mes_err'])
		writer.writerow(header)

	# Step 1: Initialize constant parameters for simulation (the numbers below correspond to available experimental data)
	# const params: coll, apt_rad
	coll_values = [8] # number of collimators [1]
	apt_rad_values = [0.010] # exit slit radius [m]
	#coll_values = (0, 4, 7, 8) # number of collimators [1]
	#apt_rad_values = (0.003, 0.005, 0.010) # exit slit radius [m]
	
	# Step 2: Initialize variable parameters for simulation and define boundaries
	# var params: R0, alpha, m
	# default: (0.99, 6.1, 1)
	# (R0, alpha, m) x (ROI 1, ROI 2, ROI 3, ROI 4, ROI 5, ...) 
	#R_bounds = np.array([[	[0, 0, 0],		# min values for params
	#						[0, 0, 0],
	#						[0, 0, 0],
	#						[0, 0, 0],
	#						[0, 0, 0],
	#						[0, 0, 0],
	#						[0, 0, 0]	],
	#					 [	[0.99, 10, 1],		# max values for params
	#						[0.99, 10, 3],
	#						[0.99, 10, 1],
	#						[0.99, 10, 1],
	#						[0.99, 10, 1],
	#						[0.99, 10, 1],
	#						[0.99, 10, 1]	],
	#					 ])
	# (k1 [R0], k2 [alpha], k3 [m]) x (min, max)
	#k_bounds = np.array([	[0, 1, 0],
	#						[1, 6, 1]	])

	# Step 3: Run initial set of parameters for breadth (all combinations of const params, with all bounds combinations of var params) 
	# (R0, alpha, m) x (ROI 1, ROI 2, ROI 3, ROI 4, ROI 5, ...) 
	R = np.array([	[0.99, 6.1, 1],
					[0.99, 6.1, 3],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1]	])

	for coll in coll_values:
		for ap_radius in apt_rad_values:
			for ROI in range(num_ROIs):
				print('ROI', ROI)
				for k1 in np.linspace(0.75, 1, num_samples): 
					# scale ROI 'ROI' by k from optimal found 6-23 
					k2 = 1
#					k3 = -2.02*k1 + 2.44
					for k3 in np.linspace(0.3, 1, num_samples):
						k = np.array([k1, k2, k3])
						R_scaled = R*1
						R_scaled[ROI] *= k
	
						print('scaling: ')
						print(k)
						print(R_scaled)
	
						# run simulation with given const and var params
						outDir = run(n, coll, ap_radius, R_scaled, output_dir)
					
						# extract simulation estimated count rate
						sim_sum, sim_err = analyze(outDir)
				
						# write output to file
						line = [coll, ap_radius]
						for i in range(R_scaled.shape[0]):
							for j in range(R_scaled.shape[1]):
								line.append(R_scaled[i, j])
						line.extend([sim_sum, sim_err])
						with open(summary_file, 'a', newline='') as file:
							writer = csv.writer(file)
							writer.writerow(line)
	
if __name__ == '__main__':
	num_samples = 10
	parser = argparse.ArgumentParser(description='perform organized search of parameter space')
	parser.add_argument('output_dir', help='Output directory for the files')

	args = parser.parse_args()
	main(args.output_dir, num_samples)
