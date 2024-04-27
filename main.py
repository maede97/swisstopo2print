import requests
import json
import numpy as np
from stl import mesh

corner1 = "2'635'780.2, 1'156'621.5"
corner3 = "2'643'012.2, 1'150'553.3"
FILENAME = "jungfrau.stl"
 
SWISSTOPO_URL = "https://api3.geo.admin.ch/rest/services/profile.json"

def generate_points_on_parallel_lines(corner1, corner2, num_points):
    x1, y1 = corner1[1], corner1[0]
    x2, y2 = corner2[1], corner2[0]

    # Calculate the distance between the corners
    distance = abs(x2 - x1)

    # Generate evenly spaced x-coordinates
    x_coordinates = np.linspace(x1, x2, num_points)

    # Generate points on opposite edges of the rectangle
    points_line1 = [(y1, x) for x in x_coordinates]
    points_line2 = [(y2, x) for x in x_coordinates]

    return points_line1, points_line2

def process_point(point):
    p = point.replace("'","")
    p = p.replace(" ","")
    p = p.split(",")
    p = [int(float(x)) for x in p]
    return p

p1 = process_point(corner1)
p3 = process_point(corner3)

pts1,pts2 = generate_points_on_parallel_lines(p1, p3, 100)

lines_x = []
lines_y = []
lines_z = []

for i in range(len(pts1)):
    geom = {
        "type": "LineString",
        "coordinates": [pts1[i], pts2[i]]
    }
    params = {
        "geom": json.dumps(geom),
        "sr": 2056
    }
    x_pts = []
    y_pts = []
    z_pts = []
    r = requests.get(SWISSTOPO_URL, params=params)
    for pt in r.json():
        h = pt["alts"]["COMB"]
        easting = pt["easting"]
        northing = pt["northing"]

        x_pts.append(easting)
        y_pts.append(northing)
        z_pts.append(h)

    lines_x.append(x_pts)
    lines_y.append(y_pts)
    lines_z.append(z_pts)

num_pts = len(lines_x[0])
num_lines = len(lines_x)
num_faces = (num_pts - 1) * 4 * (len(lines_x) - 1)
mesh = mesh.Mesh(np.zeros(num_faces, dtype=mesh.Mesh.dtype))

# compute offset
z_offset = 1
min_x = min([min(x) for x in lines_x])
min_y = min([min(y) for y in lines_y])
min_z = min([min(z) for z in lines_z]) - z_offset
max_x = max([max(x) for x in lines_x])
max_y = max([max(y) for y in lines_y])
max_z = max([max(z) for z in lines_z])

# now add all faces

face_count = 0
for i in range(1, num_pts):
    # use i, i-1 as 4 points
    for j in range(1, num_lines):

        # connect j, j -1
        p1 = lines_x[j - 1][i-1] - min_x, lines_y[j - 1][i-1] - min_y, lines_z[j - 1][i-1] - min_z
        p2 = lines_x[j - 1][i] - min_x, lines_y[j - 1][i] - min_y, lines_z[j - 1][i] - min_z
        p3 = lines_x[j][i] - min_x, lines_y[j][i] - min_y, lines_z[j][i] - min_z
        p4 = lines_x[j][i-1] - min_x, lines_y[j][i-1] - min_y, lines_z[j][i-1] - min_z

        # connect p1-p2-p3 and p1-p3-p4
        mesh.vectors[face_count][0] = p1
        mesh.vectors[face_count][1] = p2
        mesh.vectors[face_count][2] = p3
        face_count += 1

        mesh.vectors[face_count][0] = p1
        mesh.vectors[face_count][1] = p3
        mesh.vectors[face_count][2] = p4
        face_count += 1

# and add bottom block
bottom_z = 0

# add outside faces along lines
last = len(lines_y) - 1 # first line: 0
for i in range(1, num_pts):
    corner1 = lines_x[0][0] - min_x, lines_y[0][0] - min_y, bottom_z
    corner2 = lines_x[last][0] - min_x, lines_y[last][0] - min_y, bottom_z
    p1 = lines_x[0][i-1] - min_x, lines_y[0][i-1] - min_y, lines_z[0][i-1] - min_z
    p2 = lines_x[0][i] - min_x, lines_y[0][i] - min_y, lines_z[0][i] - min_z
    p3 = lines_x[last][i-1] - min_x, lines_y[last][i-1] - min_y, lines_z[last][i-1] - min_z
    p4 = lines_x[last][i] - min_x, lines_y[last][i] - min_y, lines_z[last][i] - min_z

    mesh.vectors[face_count][0] = corner1
    mesh.vectors[face_count][1] = p1
    mesh.vectors[face_count][2] = p2
    face_count += 1

    mesh.vectors[face_count][0] = corner2
    mesh.vectors[face_count][1] = p3
    mesh.vectors[face_count][2] = p4
    face_count += 1

mesh.vectors[face_count][0] = corner1
mesh.vectors[face_count][1] = p2
mesh.vectors[face_count][2] = p2[0], p2[1], 0
face_count += 1

mesh.vectors[face_count][0] = corner2
mesh.vectors[face_count][1] = p4
mesh.vectors[face_count][2] = p4[0], p4[1], 0
face_count += 1


# add outside faces along pts (each line once)
last = len(lines_y[0]) - 1 # first: 0
for i in range(1, num_lines):
    corner1 = lines_x[0][0] - min_x, lines_y[0][0] - min_y, bottom_z
    corner2 = lines_x[0][last] - min_x, lines_y[0][last] - min_y, bottom_z
    p1 = lines_x[i-1][0] - min_x, lines_y[i-1][0] - min_y, lines_z[i-1][0] - min_z
    p2 = lines_x[i][0] - min_x, lines_y[i][0] - min_y, lines_z[i][0] - min_z
    p3 = lines_x[i-1][last] - min_x, lines_y[i-1][last] - min_y, lines_z[i-1][last] - min_z
    p4 = lines_x[i][last] - min_x, lines_y[i][last] - min_y, lines_z[i][last] - min_z

    mesh.vectors[face_count][0] = corner1
    mesh.vectors[face_count][1] = p1
    mesh.vectors[face_count][2] = p2
    face_count += 1

    mesh.vectors[face_count][0] = corner2
    mesh.vectors[face_count][1] = p3
    mesh.vectors[face_count][2] = p4
    face_count += 1

mesh.vectors[face_count][0] = corner1
mesh.vectors[face_count][1] = p2
mesh.vectors[face_count][2] = p2[0], p2[1], 0
face_count += 1

mesh.vectors[face_count][0] = corner2
mesh.vectors[face_count][1] = p4
mesh.vectors[face_count][2] = p4[0], p4[1], 0
face_count += 1

# add bottom faces (2)
mesh.vectors[face_count][0] = min_x - min_x, min_y - min_y, 0
mesh.vectors[face_count][1] = max_x - min_x, min_y - min_y, 0
mesh.vectors[face_count][2] = max_x - min_x, max_y - min_y, 0
face_count += 1

mesh.vectors[face_count][0] = min_x - min_x, min_y - min_y, 0
mesh.vectors[face_count][1] = min_x - min_x, max_y - min_y, 0
mesh.vectors[face_count][2] = max_x - min_x, max_y - min_y, 0
face_count += 1

mesh.save(FILENAME)