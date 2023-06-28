from scipy.optimize import fmin
from run_mcstas import objective_function, analyze, run, experiment_data, generate_hash
import csv
import numpy as np

# 'roll' a simplex down through parameter space to do nonlinear optimization 
def simplex_search(p0, R_bounds, coll_values, apt_rad_values, output_dir, summary_file, opt_file, max_iter):
	n = 1e8
	p = 1e10

	# Define the objective function for the simplex search
	def simplex_objective_function(R):
		# Compute the error based on the modified R
		R = R.reshape(-1,3)
		err = objective_function(n, coll_values, apt_rad_values, R, output_dir, summary_file)
		pen = p*penalty_function(R)
		print('\n============\nR:\n', R, '\nerr:\n', err, '\npenalty:\n', pen, '\n============\n')

		# write optimization parameters to file
		line = []
		for i in range(R.shape[0]):
			for j in range(R.shape[1]):
				line.append(R[i, j])
		line.extend([err, pen, err+pen])
		with open(opt_file, 'a', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(line)

		return err + pen

	# Define penalty function to discourage out of bounds parameters
	def penalty_function(R):
		lb = R_bounds[:,:,0]
		ub = R_bounds[:,:,1]
		penalty = 0

		for i in range(R.shape[0]):		# ROI
			for j in range(R.shape[1]):	# param
				if R[i,j] < lb[i,j]:
					penalty += (lb[i,j] - R[i,j])**2
				elif R[i,j] > ub[i,j]:
					penalty += (R[i,j] - ub[i,j])**2

		return penalty

	# Define the initial simplex based on the bounds for R_ROI
	dp = 0.1
	
	m = 7 # number of ROIs
	simplex_initial = [ 
    	p0 - dp * np.eye(m*3).reshape(-1,m,3)[3*i+j] * (R_bounds[i, j, 1] - R_bounds[i, j, 0]) 
    	for i in range(m)
    	for j in range(3)
	]

	simplex_initial.insert(0, p0) 

	simplex_initial = np.array(simplex_initial)

	print('initial simplex:',simplex_initial)
	print('initial simplex shape', simplex_initial.shape)
	print('simplex reshapen:',simplex_initial.reshape(-1,m*3))
	simplex_initial = simplex_initial.reshape(-1,m*3)

	# Run simplex optimization varying R_ROI
	result = fmin(simplex_objective_function, p0, args=(), xtol=1e-2, ftol=1e-2, maxiter=max_iter, maxfun=None, full_output=0, disp=1, retall=0, callback=None, initial_simplex=simplex_initial)

	# Get the optimal R and construct the optimal_parameters
	optimal_R = result
	optimal_parameters = np.vstack((p0[0], optimal_R, p0[2:]))

	return optimal_parameters

# 'roll' a simplex down through parameter space to do nonlinear optimization 
def simplex_search_single_ROI(p0, R_bounds, coll_values, apt_rad_values, output_dir, summary_file, opt_file, max_iter):
	n = 1e8
	ROI = 2
	p = 1e10

	# Extract the initial guess for R_ROI
	R_ROI = p0[ROI-1]

	# Extract bounds on R_ROI
	R_ROI_bounds = R_bounds[ROI-1]

	print(R_ROI)
	print(R_ROI_bounds)

	# Define the objective function for the simplex search
	def simplex_objective_function(R_ROI):
		# Create a temporary copy of R
		R = np.copy(p0)
		R[1] = R_ROI

		# Compute the error based on the modified R
		err = objective_function(n, coll_values, apt_rad_values, R, output_dir, summary_file)
		pen = p*penalty_function(R_ROI)
		print('\n============\nR:\n', R, '\nerr:\n', err, '\npenalty:\n', pen, '\n============\n')

		# write optimization parameters to file
		line = []
		for i in range(R.shape[0]):
			for j in range(R.shape[1]):
				line.append(R[i, j])
		line.extend([err, pen, err+pen])
		with open(opt_file, 'a', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(line)

		return err + pen

	# Define penalty function to discourage out of bounds parameters
	def penalty_function(R_ROI):
		lb = R_ROI_bounds[:,0]
		ub = R_ROI_bounds[:,1]
		penalty = 0

		for i in range(len(R_ROI)):
			if R_ROI[i] < lb[i]:
				penalty += (lb[i] - R_ROI[i])**2
			elif R_ROI[i] > ub[i]:
				penalty += (R_ROI[i] - ub[i])**2

		return penalty

	# Define the initial simplex based on the bounds for R_ROI
	dp = 0.1
	simplex_initial = [
		p0,
		p0+[1,0,0,0,0,0,0,0]*dp*()
	]
	#simplex_initial = [
	#	R_ROI,
	#	R_ROI - [0.025*dp, 0, 0],
	#	R_ROI - [0, 2.4*dp, 0],
	#	R_ROI - [0, 0, 0.07*dp]
	#]
	print('initial simplex:',simplex_initial)

	# Run simplex optimization varying R_ROI
	#result = minimize(simplex_objective_function, R_ROI, method='Nelder-Mead', options={'maxiter': max_iter}, bounds=R_ROI_bounds, initial_simplex=simplex_initial)
	result = fmin(simplex_objective_function, R_ROI, args=(), xtol=1e-4, ftol=1e-4, maxiter=max_iter, maxfun=None, full_output=0, disp=1, retall=0, callback=None, initial_simplex=simplex_initial)

	# Get the optimal R_ROI and construct the optimal_parameters
	optimal_R_ROI = result.x
	#TODO make this work for any ROI specification
	optimal_parameters = np.vstack((p0[0], optimal_R_ROI, p0[2:]))

	return optimal_parameters
