import mcstasHelper as mc
import matplotlib.pyplot as plt
import numpy as np
import re
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("inFile", help="Input file")

args = parser.parse_args()
inFile = args.inFile

I, sigI, N, dataHeader, L = mc.extractMcStasData(inFile) 
component = dataHeader['component']
#print(json.dumps(dataHeader, indent=4))
print(inFile)

if dataHeader['type'][:8]=="array_1d":
	I, sigI, N, L = mc.mcstas2np(inFile)

	# find fwhm
	hm_I = np.max(I) / 2 
	left_idx = np.argmin(np.abs(I[:np.argmax(I)] - hm_I))
	right_idx = np.argmin(np.abs(I[np.argmax(I):] - hm_I)) + np.argmax(I)
	print("fwhm: "+str(L[right_idx] - L[left_idx]))

	# find max and corresponding x value
	max_index = np.argmax(I)
	print("wavelength: "+str(L[max_index])+", intensity: "+str(I[max_index]))

	unit = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
	dx = (L[-1] - L[0]) / np.size(L) 

	plt.errorbar(L, I, yerr=sigI, fmt='o', capsize=2)
	plt.xlabel(dataHeader['xlabel'])
	plt.ylabel('Intensity/ '+"{:.2e}".format(dx)+' [s*'+unit[0]+']')
	plt.title(component, pad=10)
	plt.show()

	plt.plot(L, N)
	plt.xlabel(dataHeader['xlabel'])
	plt.ylabel('N/ '+"{:.2e}".format(dx)+' ['+unit[0]+']')
	plt.title(component, pad=10)
	plt.show()

else:
	print("Unknown Data Type.")
