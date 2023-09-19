import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def plot_off_mesh(filename):
	with open(filename, "r") as f:
		lines = f.readlines()

	num_vertices, num_faces, _ = map(int, lines[1].split())

	vertices = []
	for line in lines[2:2+num_vertices]:
		vertex = list(map(float, line.split()[0:3]))
		# Plot vertices as (x, z, y)
		vertex = [vertex[0], vertex[2], vertex[1]]
		vertices.append(vertex)

	faces = []
	for line in lines[2+num_vertices:]:
		face = list(map(int, line.split()[1:]))
		faces.append(face)

	vertices = np.array(vertices)
	faces = np.array(faces)

	fig = plt.figure()
	ax = fig.add_subplot(111, projection="3d")

	mesh = Poly3DCollection(vertices[faces - 1], facecolors="cyan", linewidths=1, edgecolors="r", alpha=0.1)
	ax.add_collection3d(mesh)

	return ax

def plot_3d_data(filename, ax):
	data = np.loadtxt(filename, usecols=(0, 1, 2))
	ax.scatter(data[:, 0], data[:, 2], data[:, 1], c="b", marker="o")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Plot .off geometry and 3D data on top")
	parser.add_argument("off_file", type=str, help="Path to the .off file")
	parser.add_argument("data_file", type=str, help="Path to the 3D data file")
	args = parser.parse_args()

	ax = plot_off_mesh(args.off_file)
	plot_3d_data(args.data_file, ax)

	ax.set_xlabel('X [m]')
	ax.set_ylabel('Z [m]')
	ax.set_zlabel('Y [m]')

	ax.set_xlim(-0.2,0.2)
	ax.set_ylim(1.5,5.5)
	ax.set_zlim(-0.2,0.2)

	ax.set_title('Monolith Guide Interaction Events')
	plt.show()
