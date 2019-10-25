# -*- coding: utf-8 -*-
'''
The center of the floating collar is (0,0,0)
Fish cage is along the Z- irection
Z=0 is the free surface
Z<0 is the water zone
Z>0 is the air zone
The fish cage is a cylindrical shape
!! the sinker points are added manually 
Because it is dependent on individual cage.
Any question please email: hui.cheng@uis.no
'''
# define the fish cage shape
import numpy as np
from numpy import pi
D = 15  # [m]  fish cage diameter
H = 30  # [m]  fish cage height
L = 1.5  # [m]  bar length
NT = 72  # it can use int(pi*D/L)   # Number of the nodes in circumference
NT=int(pi*D/L)
NN = 20  # it can use int(H/L)      # Number-1 of the nodes in the height
NN=int(H/L)
p = np.zeros([(NN + 1) * NT, 3])

# generate the point coordinates matrix
for i in range(0, NT):
    for j in range(0, NN + 1):
        p[i + j * NT, :] = [
            D / 2 * np.cos(i * 2 * pi / NT), D / 2 * np.sin(i * 2 * pi / NT),
            -j * L
        ]

# the below is the commond in the Mesh, Salome.
# the mesh creater script
import sys
import salome
salome.salome_init()
theStudy = salome.myStudy
import SMESH, SALOMEDS
from salome.smesh import smeshBuilder
smesh = smeshBuilder.New(theStudy)
Mesh_1 = smesh.Mesh()

# add the pints into geometry
for i in range(len(p)):
    nodeID = Mesh_1.AddNode(float(p[i, 0]), float(p[i, 1]), float(p[i, 2]))
    
# add the horizontial line into geometry
con=[]
for i in range(1, NT + 1):
    for j in range(0, NN + 1):
        if i == NT:
            edge = Mesh_1.AddEdge([i + j * NT, 1 + i + (j - 1) * NT])
            con.append([i + j * NT-1, 1 + i + (j - 1) * NT-1])
        else:
            edge = Mesh_1.AddEdge([i + j * NT, 1 + i + j * NT])
            con.append([i + j * NT-1, 1 + i + j * NT-1])
# add the vertical line into geometry
for i in range(1, NT + 1):
    for j in range(0, NN):
        edge = Mesh_1.AddEdge([i + j * NT, i + (j + 1) * NT])
        con.append([i + j * NT-1, i + (j + 1) * NT-1])
import os
cwd = os.getcwd()
np.savetxt('lineconnections.txt', con)


def Cal_screen(POSI, elem, are):  # todo: auto generate the screen element
    sur = []
    for i in range(len(elem)):
        for j in range(len(elem)):
            twoli = set([elem[i][0], elem[i][1], elem[j][0], elem[j][1]])
            if len(set(twoli)) == 3:
                ele = [k for k in twoli]
                ele.sort()
                a1 = Cal_distence(POSI[ele[0]], POSI[ele[1]])
                a2 = Cal_distence(POSI[ele[0]], POSI[ele[2]])
                a3 = Cal_distence(POSI[ele[1]], POSI[ele[2]])
                s = (a1 + a2 + a3) / 2
                K = np.sqrt(s * (s - a1) * (s - a2) * (s - a3))
                if K > are * 0.9:
                    if ele not in sur:
                        sur.append(ele)
    return sur

isDone = Mesh_1.Compute()
# nameing  the group

# defaults nname for all the twines and nodes.
twines = Mesh_1.CreateEmptyGroup(SMESH.EDGE, 'twines')
nbAdd = twines.AddFrom(Mesh_1.GetMesh())
smesh.SetName(twines, 'twines')

allnodes = Mesh_1.CreateEmptyGroup(SMESH.NODE, 'allnodes')
nbAdd = allnodes.AddFrom(Mesh_1.GetMesh())
smesh.SetName(allnodes, 'allnodes')

# define the fixed points, the reaction forces are calculated based on fixed points.
fixed = Mesh_1.CreateEmptyGroup(SMESH.NODE, 'fixed')
nbAdd = fixed.Add([i for i in range(NT + 1)])
smesh.SetName(fixed, 'fixed')

# bottom ring will keep the cage and add the sink forces
bottomring = Mesh_1.CreateEmptyGroup(SMESH.EDGE, 'bottomring')
nbAdd = bottomring.Add([i for i in range(1 + NN, 1 + (NT) * (NN + 1), NN + 1)])
smesh.SetName(bottomring, 'bottomring')

# the top ring to keep ths shape of the fish cage.
topring = Mesh_1.CreateEmptyGroup(SMESH.EDGE, 'topring')
nbAdd = topring.Add([i for i in range(1, 1 + (NT) * (NN + 1), NN + 1)])
smesh.SetName(topring, 'topring')

# generate the name for each node to assign the hycxrodynamic forces.
for i in range(1, (NN + 1) * NT + 1):
    node1 = Mesh_1.CreateEmptyGroup(SMESH.NODE, 'node%s' % i)
    nbAdd = node1.Add([i])
    smesh.SetName(node1, 'node%s' % i)
