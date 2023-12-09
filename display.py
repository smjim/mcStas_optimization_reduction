import mcstasHelper as mc
import matplotlib.pyplot as plt
import numpy as np
import tifffile
import re
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("inFile", help="Input file")
parser.add_argument("plot_type", nargs="?", default="full", choices=["x", "y", "full"],
				help="Plot type: 'x', 'y', or 'full'")
parser.add_argument('--showN', action='store_true', help='if true then display plots for N')

args = parser.parse_args()
inFile = args.inFile
plot_type = args.plot_type.lower()

I, sigI, N, dataHeader, L = mc.extractMcStasData(inFile) 
component = dataHeader['component']
position = dataHeader['position']
title = f'{component}; ({position})m'
#print(json.dumps(dataHeader, indent=4))
print(inFile)

if dataHeader['type'][:8]=="array_2d":
	print(dataHeader)
	extent = np.array(dataHeader['xylimits'].split(),dtype=float)
	
	# Call the mcstas2TIFF function to generate .tif files
	imN, imI, sigI = mc.mcstas2TIFF(inFile, save=False)
	
	if plot_type == "x":
		unit = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
		dx = (extent[1] - extent[0]) / np.array(imI).shape[1] 

		# Generate X cross-section cross_section
		cross_section = np.sum(np.array(imI), axis=0)  # Sum along the horizontal axis
		err_cross_section = np.sqrt(np.sum(np.square(np.array(sigI)), axis=0))

		x = np.linspace(extent[0], extent[1], np.size(cross_section))
		plt.errorbar(x, cross_section, err_cross_section, capsize=2)
		plt.xlabel(dataHeader['xlabel'])
		plt.ylabel('Intensity [n/s]/ '+"{:.2e}".format(dx)+' ['+unit[0]+']')
		plt.title("X Cross-Section: "+title)
		plt.tight_layout()
		plt.show()
	elif plot_type == "y":
		unit = re.findall(r"\[(.*?)\]", dataHeader['ylabel'])
		dx = (extent[3] - extent[2]) / np.array(imI).shape[0] 

		# Generate Y cross-section
		cross_section = np.flip(np.sum(np.array(imI), axis=1))  # Sum along the horizontal axis
		err_cross_section = np.flip(np.sqrt(np.sum(np.square(np.array(sigI)), axis=1)))

		x = np.linspace(extent[3], extent[2], np.size(cross_section))
		plt.errorbar(x, cross_section, err_cross_section, capsize=2)
		plt.xlim(extent[2], extent[3])
		plt.xlabel(dataHeader['ylabel'])
		plt.ylabel('Intensity [n/s]/ '+"{:.2e}".format(dx)+' ['+unit[0]+']')
		plt.title("Y Cross-Section: "+title)
		plt.tight_layout()
		plt.show()
	elif plot_type == "full":
		unit1 = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
		unit2 = re.findall(r"\[(.*?)\]", dataHeader['ylabel'])
		# Calculate bin size
		dx = (extent[1] - extent[0]) / (np.array(imI).shape[1] - 1)
		dy = (extent[3] - extent[2]) / (np.array(imI).shape[0] - 1)

		#plt.imshow(np.array(imI), extent=extent, cmap='plasma', norm='log') 
		#plt.imshow(np.flipud(np.array(imI)), extent=extent, cmap='plasma', norm='log', vmin=1, vmax=1e6) 
		plt.imshow(np.flipud(np.array(imI)), extent=extent, cmap='plasma', norm='log') 
		plt.colorbar().set_label('Intensity [n/s]/ '+"{:.2e}".format(dx*dy)+' ['+unit1[0]+'*'+unit2[0]+']')
		plt.xlabel(dataHeader['xlabel'])
		plt.ylabel(dataHeader['ylabel'])
		plt.title(title, pad=10)
		plt.tight_layout()
		plt.show()

		if (args.showN==1):
			plt.imshow(np.array(imN), extent=extent, cmap='plasma') 
			plt.colorbar().set_label('N/ '+"{:.2e}".format(dx*dy)+' ['+unit1[0]+'*'+unit2[0]+']')
			plt.xlabel(dataHeader['xlabel'])
			plt.ylabel(dataHeader['ylabel'])
			plt.title(title, pad=10)
			plt.tight_layout()
			plt.show()

		## Show the TIFF file with tags
		#mc.show_tiff(inFile+"_N.tif", extent, dataHeader['xlabel'], dataHeader['ylabel'])
		#mc.show_tiff(inFile+"_I.tif", extent, dataHeader['xlabel'], dataHeader['ylabel'])
	else:
		print("Invalid plot type. Please specify 'x', 'y', or 'full'.")

elif dataHeader['type'][:8]=="array_1d":
	I, sigI, N, L = mc.mcstas2np(inFile)

	unit = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
	dx = (L[-1] - L[0]) / np.size(L) 

	plt.errorbar(L, I, yerr=sigI, fmt='o', capsize=2)
	plt.xlabel(dataHeader['xlabel'])
	plt.ylabel('Intensity [n/s]/ '+"{:.2e}".format(dx)+' ['+unit[0]+']')
	plt.title(title, pad=10)
	plt.tight_layout()
	plt.show()

	if (args.showN==1):
		plt.plot(L, N)
		plt.xlabel(dataHeader['xlabel'])
		plt.ylabel('N/ '+"{:.2e}".format(dx)+' ['+unit[0]+']')
		plt.title(title, pad=10)
		plt.tight_layout()
		plt.show()

else:
	print("Unknown Data Type.")


