# optimize simulation parameters 
# James Rogers, jroger87@vols.utk.edu
# 6-20-2023

from optimization_algorithms import simplex_search_single_ROI, simplex_search
import numpy as np
import csv
import os
import argparse

def main(output_dir, max_iter):
	# Step 0: Open summary files for writing results
	num_ROIs = 7

	# write output for every run
	summary_file = "{}/output.dat".format(output_dir)
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

	# write optimization parameters and opt_err
	opt_file = "{}/optimization_output.dat".format(output_dir)
	with open(opt_file, 'w', newline='') as file:
		writer = csv.writer(file)

		# write header
		header = []
		for i in range(num_ROIs):
			for j, prefix in enumerate(['R0_', 'alpha_', 'm_']):
				param_name = f"{prefix}{i+1}"
				header.append(param_name)
		header.extend(['param_err', 'param_penalty', 'opt_err'])
		writer.writerow(header)

	# Step 1: Initialize constant parameters for simulation (the numbers below correspond to available experimental data)
	# const params: coll, apt_rad
	coll_values = [0, 4, 7, 8] # number of collimators [1]
	apt_rad_values = [0.010] # exit slit radius [m]
	
	# Step 2: Initialize variable parameters for simulation and define boundaries
	# var params: R0, alpha, m
	# default: (0.99, 6.1, 1)
	# (min, max) x (R0, alpha, m) x (ROI 1, ROI 2, ROI 3, ROI 4, ROI 5, ...) 
	R_bounds = np.array([   [[0, 0.99], [0, 10], [0, 1]],
	                        [[0, 0.99], [0, 10], [0, 3]],
    	                    [[0, 0.99], [0, 10], [0, 1]],
        	                [[0, 0.99], [0, 10], [0, 1]],
            	            [[0, 0.99], [0, 10], [0, 1]],
                	        [[0, 0.99], [0, 10], [0, 1]],
                    	    [[0, 0.99], [0, 10], [0, 1]]    ]) 

	# Step 3: Run optimization scheme 
	# (R0, alpha, m) x (ROI 1, ROI 2, ROI 3, ROI 4, ROI 5, ...) 
	R = np.array([	[0.99, 6.1, 1],
					[0.99, 6.1, 3],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1],
					[0.99, 6.1, 1]	])

	# Initial guess for optimal parameters
	p0 = R

	# Run simplex search optimization with initial guess, R_bounds, constant parameters, and max_iter
	#optimal_params = simplex_search_single_ROI(p0, R_bounds, coll_values, apt_rad_values, output_dir, summary_file, opt_file, max_iter)
	optimal_params = simplex_search(p0, R_bounds, coll_values, apt_rad_values, output_dir, summary_file, opt_file, max_iter)

	print('optimal params:',optimal_params)
	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='perform organized search of parameter space')
	parser.add_argument('output_dir', help='Output directory for the files')
	parser.add_argument('max_iter', help='max number of iterations of optimization scheme')

	args = parser.parse_args()
	main(args.output_dir, int(args.max_iter))
