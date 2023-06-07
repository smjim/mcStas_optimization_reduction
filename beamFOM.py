import numpy as np
from scipy.special import gammaln
import h5py
import string
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("inFile", help="Input file")
parser.add_argument('--rebin', nargs=1, type=float, metavar=('newSize'),
					help='Resized array length: newSize')
parser.add_argument('--noshow', action='store_true', help='if true then only show value, dont display plot')

args = parser.parse_args()
inFile = args.inFile

# get data from h5 file
file = h5py.File(inFile, "r")
group = file["entry"]

print(group["experiment_title"][0])

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
	rebinned_counts = rebin_histogram(counts_per_bin, newSize)
	rebinned_time = rebin_histogram(event_time_zero[:-1], newSize)/ (event_time_zero[:-1].size // newSize)
	rebinned_counts_err = np.sqrt(rebin_histogram(np.square(counts_per_bin_err), newSize))

	# find count rate
	rebinned_time_per_bin = np.diff(rebinned_time)
	counts_per_second = rebinned_counts[:-1]/ rebinned_time_per_bin
	counts_per_second_err = rebinned_counts_err[:-1]/ rebinned_time_per_bin
else:
	# find count rate
	counts_per_second = counts_per_bin/ time_per_bin
	counts_per_second_err = counts_per_bin_err/ event_time_zero[:-1]

# Calculate deviance and reduced deviance for Poisson data fit
def calculate_poisson_deviance(counts_per_second, mean):
	observed_log_likelihood = counts_per_second * np.log(counts_per_second) - counts_per_second - gammaln(counts_per_second + 1)
	expected_log_likelihood = counts_per_second * np.log(mean) - mean - gammaln(counts_per_second + 1)
	deviance = 2 * np.sum(observed_log_likelihood - expected_log_likelihood)
	return deviance

k = np.mean(counts_per_second)
deviance = calculate_poisson_deviance(counts_per_second, k)
deviance_ndof = deviance/ (counts_per_second.size - 1)

print(k, " counts/ second")
print("deviance/ ndof = ", deviance_ndof)

if (args.noshow==0):
	import matplotlib.pyplot as plt
	if args.rebin:  
		plt.errorbar(rebinned_time[:-1], counts_per_second, yerr=counts_per_second_err, fmt=' ', capsize=2)
		plt.plot(rebinned_time[:-1], np.zeros(rebinned_time[:-1].size) + k, linestyle='--')
	else:
		plt.errorbar(event_time_zero[:-1], counts_per_second, yerr=counts_per_second_err, fmt=' ', capsize=2)
		plt.plot(event_time_zero[:-1], np.zeros(event_time_zero[:-1].size) + k, linestyle='--')

	plt.xlabel('time [s]')
	plt.ylabel('count rate [1/s]')
	plt.title(group["title"][0].decode("UTF-8"))
	plt.show()

