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
        vertices.append(vertex)

    faces = []
    for line in lines[2+num_vertices:]:
        face = list(map(int, line.split()[1:]))
        faces.append(face)

    vertices = np.array(vertices)
    faces = np.array(faces)

    # Find the minimum and maximum values in each dimension
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)
    
    # Translate and scale to fit within the unit cube (0, 1) in all dimensions
    translated_scaled_vertices = (vertices - min_coords) / (max_coords - min_coords)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    mesh = Poly3DCollection(translated_scaled_vertices[faces - 1], facecolors="cyan", linewidths=1, edgecolors="r", alpha=0.1)
    ax.add_collection3d(mesh)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot a 3D mesh from a .off file")
    parser.add_argument("filename", type=str, help="Path to the .off file")
    args = parser.parse_args()

    plot_off_mesh(args.filename)

