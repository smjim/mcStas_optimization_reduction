import numpy as np
from scipy.special import gammaln
import h5py
import string
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("inFile", help="Input file")
parser.add_argument('--rebin', nargs=1, type=float, metavar=('newSize'),
					help='Resized array length: newSize')
parser.add_argument('--outlier', nargs=1, type=float, metavar=('n'),
					help='if true, then eliminate datapoints greater than n sigma away from the mean')
parser.add_argument('--noshow', action='store_true', help='if true then only show value, dont display plot')

args = parser.parse_args()
inFile = args.inFile

# get data from h5 file
file = h5py.File(inFile, "r")
group = file["entry"]

# extract relevant data from input file
event_time_zero = np.array(group["monitor2/event_time_zero"]) # seconds
event_time_offset = np.array(group["monitor2/event_time_offset"]) # microseconds
event_index = np.array(group["monitor2/event_index"])

counts_per_bin = np.diff(event_index) 
counts_per_bin_err = np.sqrt(counts_per_bin)
time_per_bin = np.diff(event_time_zero)

# rebin histogram if necessary to increase statistics
if args.rebin:
	def rebin_histogram(hist, new_size):
		old_size = hist.size
	
		if new_size >= old_size:
			raise ValueError("The new size should be smaller than the old size.")
	
		if old_size % new_size != 0:
			rem = old_size % new_size
			print("! New size is not a factor of old size, cutting out last ", rem, " entries")
			hist = hist[:-rem]
	
		factor = old_size // new_size
	
		# Reshape the histogram array to a 2D array
		hist_2d = hist.reshape((new_size, factor))
	
		# Sum the values in each bin of the new histogram
		rebinned_hist = np.sum(hist_2d, axis=1)
	
		return rebinned_hist

	# rebin counts_per_bin, time_per_bin
	newSize = int(args.rebin[0])
	rebinned_counts = rebin_histogram(counts_per_bin, newSize) # sum col-wise
	rebinned_time = rebin_histogram(event_time_zero[:-1], newSize)/ (event_time_zero[:-1].size // newSize) # average col-wise
	rebinned_counts_err = np.sqrt(rebin_histogram(np.square(counts_per_bin_err), newSize)) # sqrt of sum col-wise of squared values

	# find count rate
	event_time = rebinned_time[:-1]
	time_per_bin = np.diff(rebinned_time)
	counts_per_second = rebinned_counts[:-1]/ time_per_bin
	counts_per_second_err = rebinned_counts_err[:-1]/ time_per_bin
else:
	# find count rate
	event_time = event_time_zero[:-1]
	time_per_bin = time_per_bin
	counts_per_second = counts_per_bin/ time_per_bin
	counts_per_second_err = counts_per_bin_err/ event_time_zero[:-1]

# weighted mean and standard error
def mean_with_error(points, errors):
	weighted_sum = np.sum(points / (errors ** 2))
	sum_of_weights = np.sum(1 / (errors ** 2))
	mean = weighted_sum / sum_of_weights
	error = np.sqrt(1 / sum_of_weights)
	return mean, error

# Calculate deviance and reduced deviance for Poisson data fit
def calculate_poisson_deviance(counts_per_second, mean):
	observed_log_likelihood = counts_per_second * np.log(counts_per_second) - counts_per_second - gammaln(counts_per_second + 1)
	expected_log_likelihood = counts_per_second * np.log(mean) - mean - gammaln(counts_per_second + 1)
	deviance = 2 * np.sum(observed_log_likelihood - expected_log_likelihood)
	return deviance

#k = np.mean(counts_per_second)
#k_err = np.sqrt(np.sum(np.square(counts_per_second_err)))
k, k_err = mean_with_error(counts_per_second, counts_per_second_err)
deviance = calculate_poisson_deviance(counts_per_second, k)
deviance_ndof = deviance/ (counts_per_second.size - 1)

if (args.outlier==1):
	print('without removing outliers:')
print("{:.2e}".format(k), "±", "{:.2e}".format(k_err)," counts/ second")
print("deviance/ ndof = ", deviance_ndof)
print('average bin width:',np.average(time_per_bin),'s')

# if --outlier == true, then eliminate datapoints that lie > n sigma away from the mean
if (args.outlier):
	n = int(args.outlier[0])
	def eliminate_outliers(array, errors, time, n):
		mean = np.mean(array)
		std = np.std(array)
		threshold = n * std
	
		filtered_array = array[abs(array - mean) <= threshold]
		filtered_errors = errors[abs(array - mean) <= threshold]
		filtered_time = time[abs(array - mean) <= threshold]
	
		return filtered_array, filtered_errors, filtered_time

	counts_per_second, counts_per_second_err, event_time = eliminate_outliers(counts_per_second, counts_per_second_err, event_time, n)

	#k = np.mean(counts_per_second)
	#k_err = np.sqrt(np.sum(np.square(counts_per_second_err)))
	k, k_err = mean_with_error(counts_per_second, counts_per_second_err)
	deviance = calculate_poisson_deviance(counts_per_second, k)
	deviance_ndof = deviance/ (counts_per_second.size - 1)
	
	print('with outliers removed :')
	print("{:.2e}".format(k), "±", "{:.2e}".format(k_err)," counts/ second")
	print("deviance/ ndof = ", deviance_ndof)

if (args.noshow==0):
	import matplotlib.pyplot as plt
	plt.errorbar(event_time, counts_per_second, yerr=counts_per_second_err, 
			fmt=' ', capsize=2, label='counts per second')
	plt.plot(event_time, np.zeros(event_time.size) + k, 
			linestyle='--', label='mean = '+"{:.2e}".format(k))

	plt.fill_between(event_time, np.zeros(event_time.size)+k-(k_err/2), np.zeros(event_time.size)+k+(k_err/2),
			color='gray', alpha=0.9, label='mean error = '+"{:.2e}".format(k_err))

	plt.xlabel('time [s]')
	plt.ylabel('count rate [1/s]')
	plt.legend()
	plt.grid()
	plt.title(group["title"][0].decode("UTF-8"))

	plt.show()

